#!/usr/bin/env python3
"""Optional Laya-backed neural sieve for search results and claim evidence.

Laya (https://huggingface.co/convaiinnovations/laya, Apache-2.0) is a
non-autoregressive "System 1" decision model: give it a state (text or JSON)
plus a batch of typed questions and it answers all of them in a single
forward pass (~35 ms on GPU, 100-330 questions/sec batched on a T4) with
calibrated probabilities. It never generates text, so there is nothing to
parse and nothing to hallucinate.

This module wires Laya into the sieve pipeline as two optional stages:

- **Result sieving** (:func:`filter_sources`): score every search result for
  relevance to the query with one forward pass per result, dropping noise
  before it ever reaches the agent's context window.
- **Stance classification** (:func:`classify_stance`): replace the lexical
  keyword-overlap classifier in ``verify_claim`` with probabilistic
  support/conflict answers, one forward pass per source.

Everything here degrades gracefully: if the ``laya`` package (or torch) is
not installed, the pipeline falls back to the lexical heuristic model and
records that in the result metadata. Laya is therefore an *accelerant*, not
a dependency.

Install with::

    pip install "zerosieve[laya]"

Environment variables
----------------------

===========================  ==============================================
``ZEROSIEVE_LAYA_MODEL``     HF repo id (default ``convaiinnovations/laya``)
``ZEROSIEVE_LAYA_SUBFOLDER`` ``multilingual`` / ``typed-decisions`` / unset
``ZEROSIEVE_LAYA_DEVICE``    ``cuda`` / ``mps`` / ``cpu`` (default: auto)
``HF_ENDPOINT``              set to ``https://hf-mirror.com`` on networks
                             that cannot reach huggingface.co directly
===========================  ==============================================

Calibration caveat (carried over from the upstream model card): Laya ships
over-confident — refitting one temperature per (question type, option count)
moved mean ECE 0.466 -> 0.081 upstream. The thresholds here are exposed as
constructor arguments so you can tighten them against a small labeled set
from your own domain before trusting the probabilities at scale.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Protocol

logger = logging.getLogger(__name__)

DEFAULT_LAYA_MODEL = "convaiinnovations/laya"

#: Relevance probability at or above which a source survives sieving.
DEFAULT_RELEVANCE_THRESHOLD = 0.5

#: Stance probability at or above which a source is supporting/conflicting.
DEFAULT_STANCE_THRESHOLD = 0.5


class StanceBackend(Protocol):
    """Minimal interface a Laya agent (or test double) must satisfy."""

    def predict(self, state: Any, questions: dict) -> dict: ...


class LayaUnavailableError(RuntimeError):
    """Raised when Laya was requested but the package/weights are unusable."""


def laya_importable() -> bool:
    try:
        import laya  # noqa: F401
    except Exception:
        return False
    return True


class LayaBackend:
    """Lazy, thread-safe handle over a Laya agent checkpoint.

    The checkpoint (hundreds of MB) is only downloaded on the first
    :meth:`predict`, never at import time, so ``import zerosieve`` stays
    instant and dependency-free.
    """

    def __init__(
        self,
        model_id: str | None = None,
        subfolder: str | None = None,
        device: str | None = None,
        token: str | None = None,
    ):
        self.model_id = model_id or os.environ.get("ZEROSIEVE_LAYA_MODEL", DEFAULT_LAYA_MODEL)
        self.subfolder = subfolder or os.environ.get("ZEROSIEVE_LAYA_SUBFOLDER") or None
        self.device = device or os.environ.get("ZEROSIEVE_LAYA_DEVICE") or None
        self.token = token
        self._agent: StanceBackend | None = None
        self._load_error: str | None = None
        self._lock = threading.Lock()

    @property
    def model_label(self) -> str:
        base = self.model_id
        return f"{base}:{self.subfolder}" if self.subfolder else base

    def _get_agent(self) -> StanceBackend:
        if self._agent is not None:
            return self._agent
        with self._lock:
            if self._agent is not None:
                return self._agent
            if self._load_error is not None:
                raise LayaUnavailableError(self._load_error)
            try:
                import laya
            except Exception as exc:  # pragma: no cover - depends on env
                self._load_error = (
                    f"laya package unavailable ({exc}). "
                    'Install it with: pip install "zerosieve[laya]"'
                )
                raise LayaUnavailableError(self._load_error) from exc
            try:
                kwargs: dict[str, Any] = {"device": self.device}
                if self.token:
                    kwargs["token"] = self.token
                if self.subfolder:
                    kwargs["subfolder"] = self.subfolder
                self._agent = laya.load(self.model_id, **kwargs)
            except Exception as exc:
                self._load_error = (
                    f"could not load Laya checkpoint {self.model_label!r} ({exc}). "
                    "If huggingface.co is unreachable from your network, set "
                    "HF_ENDPOINT=https://hf-mirror.com and retry."
                )
                raise LayaUnavailableError(self._load_error) from exc
            return self._agent

    def predict(self, state: Any, questions: dict) -> dict:
        """One forward pass: answer every question about one state."""
        return self._get_agent().predict(state, questions)

    def warmup(self) -> None:
        """Force checkpoint download/load now instead of on first use."""
        self._get_agent()


def _state_for(source) -> dict:
    state: dict[str, Any] = {"title": source.title, "url": source.url}
    if source.snippet:
        state["snippet"] = source.snippet
    if source.date:
        state["date"] = source.date
    return state


def filter_sources(
    query: str,
    sources,
    backend: LayaBackend,
    threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
) -> tuple[list, dict]:
    """Sieve search results through a Laya relevance gate.

    Each source costs one forward pass with a single ``noul`` (yes/no)
    question; sources at or above ``threshold`` survive, the rest are
    dropped and counted. Returns ``(kept, metadata)``. Failures degrade to
    keeping everything — a broken sieve must never empty the funnel.
    """
    kept: list = []
    dropped = 0
    errors = 0
    for source in sources:
        try:
            result = backend.predict(
                _state_for(source),
                {
                    "relevant": {
                        "type": "noul",
                        "instructions": (
                            "Is this search result relevant and informative for "
                            f"the query: '{query}'?"
                        ),
                    }
                },
            )
            prob = float(result["answers"]["relevant"]["noul"])
        except LayaUnavailableError:
            # Persistent (checkpoint/dependency) failure: abort the sieve so
            # the caller can fall back with everything intact.
            raise
        except Exception as exc:
            logger.debug("laya filter failed for %s: %s", source.url, exc)
            errors += 1
            kept.append(source)
            continue
        source.extra = {
            **source.extra,
            "laya": {"relevant": round(prob, 4), "model": backend.model_label},
        }
        if prob >= threshold:
            kept.append(source)
        else:
            dropped += 1
    metadata = {
        "enabled": True,
        "model": backend.model_label,
        "threshold": threshold,
        "kept": len(kept),
        "dropped": dropped,
        "errors": errors,
    }
    return kept, metadata


def classify_stance(
    claim: str,
    source,
    backend: LayaBackend,
    threshold: float = DEFAULT_STANCE_THRESHOLD,
) -> tuple[str, dict]:
    """Probabilistic stance classification for one source against a claim.

    Asks support and conflict as two ``noul`` questions in a single forward
    pass — replacing the lexical classifier's regex conflict markers and
    keyword-overlap cutoff with calibrated probabilities. Falls back to
    ``neutral`` on backend errors so one bad source cannot skew a verdict.
    """
    state = _state_for(source)
    try:
        result = backend.predict(
            state,
            {
                "support": {
                    "type": "noul",
                    "instructions": (
                        f"Does this text affirmatively support the claim: '{claim}'?"
                    ),
                },
                "conflict": {
                    "type": "noul",
                    "instructions": (
                        f"Does this text state or imply the claim is false: '{claim}'?"
                    ),
                },
            },
        )
        p_support = float(result["answers"]["support"]["noul"])
        p_conflict = float(result["answers"]["conflict"]["noul"])
    except LayaUnavailableError:
        raise
    except Exception as exc:
        logger.debug("laya stance failed for %s: %s", source.url, exc)
        return "neutral", {
            "laya_stance": {"status": "error", "error": str(exc)[:200], "model": backend.model_label},
        }

    if p_support >= threshold and p_support >= p_conflict:
        classification = "supporting"
    elif p_conflict >= threshold and p_conflict > p_support:
        classification = "conflicting"
    else:
        classification = "neutral"

    return classification, {
        "laya_stance": {
            "status": "ok",
            "model": backend.model_label,
            "p_support": round(p_support, 4),
            "p_conflict": round(p_conflict, 4),
            "threshold": threshold,
            "classification": classification,
        },
    }


def blend_strength(
    stance_probability: float,
    quality_score: float,
    freshness_score: float,
) -> float:
    """Combine Laya stance probability with the existing quality heuristics.

    Keeps the pipeline's proven domain/freshness priors but lets the neural
    stance decision dominate instead of lexical overlap:

        0.55 * stance + 0.35 * quality + 0.10 * freshness
    """
    score = (stance_probability * 0.55) + (quality_score * 0.35) + (freshness_score * 0.10)
    return round(min(max(score, 0.0), 1.0), 3)


def add_laya_args(parser) -> None:
    """Attach the shared ``--laya*`` flag group to a CLI parser."""
    group = parser.add_argument_group("laya sieve")
    group.add_argument(
        "--laya",
        action="store_true",
        help="Enable the Laya neural sieve (relevance filter / stance verifier). "
        "Falls back to the lexical heuristic when the laya package or checkpoint "
        "is unavailable.",
    )
    group.add_argument(
        "--laya-model",
        default=None,
        help=f"HuggingFace repo id (default: {DEFAULT_LAYA_MODEL}, or $ZEROSIEVE_LAYA_MODEL).",
    )
    group.add_argument(
        "--laya-subfolder",
        default=None,
        help="Checkpoint subfolder: 'multilingual' (100+ languages) or 'typed-decisions'.",
    )
    group.add_argument(
        "--laya-device",
        default=None,
        help="Inference device: cuda, mps, or cpu (default: auto-detect).",
    )
    group.add_argument(
        "--laya-threshold",
        type=float,
        default=None,
        help="Probability cutoff for keeping a result / calling a stance (default: 0.5).",
    )


def laya_backend_from_args(args) -> LayaBackend | None:
    """Build a backend from parsed CLI args, or None when --laya is absent."""
    if not getattr(args, "laya", False):
        return None
    return LayaBackend(
        model_id=getattr(args, "laya_model", None),
        subfolder=getattr(args, "laya_subfolder", None),
        device=getattr(args, "laya_device", None),
    )


def laya_search_kwargs(args) -> dict:
    """``search()`` keyword arguments implied by the CLI laya flags."""
    kwargs: dict[str, Any] = {}
    if getattr(args, "laya", False):
        kwargs["laya_filter"] = True
        if getattr(args, "laya_threshold", None) is not None:
            kwargs["laya_threshold"] = args.laya_threshold
    return kwargs


def laya_verify_kwargs(args) -> dict:
    """``verify_claim()`` / ``evidence_report()`` kwargs implied by --laya."""
    kwargs: dict[str, Any] = {}
    if getattr(args, "laya", False):
        kwargs["verifier"] = "laya"
        if getattr(args, "laya_threshold", None) is not None:
            kwargs["laya_threshold"] = args.laya_threshold
    return kwargs
