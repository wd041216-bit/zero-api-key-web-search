"""CLI smoke tests against the installed console scripts."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "fake_ddgs"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


class TestCliIntegration(unittest.TestCase):
    def _env_with_fake_ddgs(self) -> dict[str, str]:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{FIXTURE_ROOT}{os.pathsep}{existing}" if existing else str(FIXTURE_ROOT)
        )
        return env

    def _serve_tempdir(self, tmpdir: str):
        handler = partial(QuietHandler, directory=tmpdir)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            _, port = sock.getsockname()

        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, port

    def test_search_web_json_cli(self):
        result = subprocess.run(
            [sys.executable, "-m", "zero_api_key_web_search.search_web", "python release", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["query"], "python release")
        self.assertEqual(payload["search_type"], "text")
        self.assertGreaterEqual(len(payload["sources"]), 2)
        self.assertEqual(payload["metadata"]["providers_used"], ["ddgs"])

    def test_search_web_providers_cli(self):
        result = subprocess.run(
            [sys.executable, "-m", "zero_api_key_web_search.search_web", "providers", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        names = [item["name"] for item in payload["providers"]]
        self.assertIn("ddgs", names)
        self.assertIn("searxng", names)
        self.assertIn("brightdata", names)
        self.assertIn("free-verified", payload["profiles"])
        self.assertIn("docs-first", payload["goggles"])

    def test_context_json_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "zero_api_key_web_search.context",
                "python release",
                "--goggles",
                "docs-first",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["query"], "python release")
        self.assertEqual(payload["metadata"]["context_model"], "llm-context-v1")
        self.assertIn("# Search context: python release", payload["context_markdown"])

    def test_verify_claim_json_cli(self):
        result = subprocess.run(
            [sys.executable, "-m", "zero_api_key_web_search.verify_claim", "python release status", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim"], "python release status")
        self.assertIn(
            payload["verdict"],
            {"supported", "likely_supported", "contested", "likely_false", "insufficient_evidence"},
        )
        self.assertIn("supporting_count", payload["analysis"])
        self.assertIn("verification_model", payload["analysis"])
        self.assertEqual(payload["analysis"]["verification_model"]["name"], "evidence-aware-heuristic-v3")

    def test_legacy_verify_claim_module_alias(self):
        result = subprocess.run(
            [sys.executable, "-m", "zero_api_key_web_search_compat.verify_claim", "python release status", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim"], "python release status")
        self.assertEqual(payload["analysis"]["verification_model"]["name"], "evidence-aware-heuristic-v3")

    def test_evidence_report_json_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "zero_api_key_web_search.evidence_report",
                "python release status",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=self._env_with_fake_ddgs(),
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["query"], "python release status")
        self.assertEqual(payload["claim"], "python release status")
        self.assertEqual(payload["analysis"]["report_model"], "evidence-report-v2")
        self.assertIn("verdict_rationale", payload)
        self.assertIn("coverage_warnings", payload)
        self.assertIn("stance_summary", payload)
        self.assertIn("citations", payload)
        self.assertIn("source_digest", payload)

    def test_browse_page_json_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "index.html").write_text(
                "<html><head><title>Fixture</title></head><body>Hello fixture world.</body></html>",
                encoding="utf-8",
            )
            server, thread, port = self._serve_tempdir(tmpdir)
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "zero_api_key_web_search.browse_page",
                        f"http://127.0.0.1:{port}/index.html",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["title"], "Fixture")
        self.assertIn("Hello fixture world.", payload["content"])

    def test_search_web_json_cli_with_searxng_provider(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "search").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "url": "http://127.0.0.1:9999/provider-page.html",
                                "title": "SearXNG fixture result",
                                "content": "A fixture result returned by searxng.",
                                "publishedDate": "2026-03-20",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            server, thread, port = self._serve_tempdir(tmpdir)
            env = os.environ.copy()
            env["ZERO_SEARCH_SEARXNG_URL"] = f"http://127.0.0.1:{port}"
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "zero_api_key_web_search.search_web",
                        "release signal",
                        "--provider",
                        "searxng",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                )
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

        payload = json.loads(result.stdout)
        self.assertEqual(payload["metadata"]["providers_used"], ["searxng"])
        self.assertEqual(payload["validation"]["providers_requested"], ["searxng"])
        self.assertEqual(payload["sources"][0]["engine"], "SEARXNG-Text")

    def test_verify_claim_json_cli_with_deep_and_searxng(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "search").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "url": "http://127.0.0.1:0/page-a.html",
                                "title": "Ambiguous release update",
                                "content": "A short ambiguous snippet without a full conclusion.",
                                "publishedDate": "2026-03-20",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            Path(tmpdir, "page-a.html").write_text(
                (
                    "<html><head><title>Official release</title></head><body>"
                    "Python 3.13 is the latest stable release according to the official release notes."
                    "</body></html>"
                ),
                encoding="utf-8",
            )
            server, thread, port = self._serve_tempdir(tmpdir)
            search_payload = json.loads(Path(tmpdir, "search").read_text(encoding="utf-8"))
            search_payload["results"][0]["url"] = f"http://127.0.0.1:{port}/page-a.html"
            Path(tmpdir, "search").write_text(json.dumps(search_payload), encoding="utf-8")

            env = os.environ.copy()
            env["ZERO_SEARCH_SEARXNG_URL"] = f"http://127.0.0.1:{port}"
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "zero_api_key_web_search.verify_claim",
                        "Python 3.13 is the latest stable release",
                        "--provider",
                        "searxng",
                        "--deep",
                        "--max-pages",
                        "1",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                )
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

        payload = json.loads(result.stdout)
        self.assertTrue(payload["analysis"]["page_aware"])
        self.assertEqual(payload["analysis"]["page_fetches_succeeded"], 1)
        self.assertEqual(payload["metadata"]["providers_requested"], ["searxng"])
        self.assertEqual(
            payload["supporting_sources"][0]["extra"]["verification"]["page_evidence"]["status"],
            "success",
        )

    def test_evidence_report_json_cli_with_claim_and_deep(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "search").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "url": "http://127.0.0.1:0/page-a.html",
                                "title": "Ambiguous release update",
                                "content": "A short ambiguous snippet without a full conclusion.",
                                "publishedDate": "2026-03-20",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            Path(tmpdir, "page-a.html").write_text(
                (
                    "<html><head><title>Official release</title></head><body>"
                    "Python 3.13 is the latest stable release according to the official release notes."
                    "</body></html>"
                ),
                encoding="utf-8",
            )
            server, thread, port = self._serve_tempdir(tmpdir)
            search_payload = json.loads(Path(tmpdir, "search").read_text(encoding="utf-8"))
            search_payload["results"][0]["url"] = f"http://127.0.0.1:{port}/page-a.html"
            Path(tmpdir, "search").write_text(json.dumps(search_payload), encoding="utf-8")

            env = os.environ.copy()
            env["ZERO_SEARCH_SEARXNG_URL"] = f"http://127.0.0.1:{port}"
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "zero_api_key_web_search.evidence_report",
                        "Python 3.13 stable release",
                        "--claim",
                        "Python 3.13 is the latest stable release",
                        "--provider",
                        "searxng",
                        "--deep",
                        "--max-pages",
                        "1",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                )
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim"], "Python 3.13 is the latest stable release")
        self.assertTrue(payload["analysis"]["page_aware"])
        self.assertEqual(payload["analysis"]["page_fetches_succeeded"], 1)
        self.assertEqual(payload["metadata"]["providers_requested"], ["searxng"])
        self.assertEqual(payload["analysis"]["report_model"], "evidence-report-v2")
