"""ddgs-backed search provider."""

from __future__ import annotations

from typing import Optional

from free_web_search.providers.base import ProviderResult


class DdgsProvider:
    """Search provider backed by the ddgs package."""

    name = "ddgs"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        from ddgs import DDGS

        results: list[ProviderResult] = []
        with DDGS(timeout=self.timeout) as ddgs:
            if search_type == "text":
                api_results = ddgs.text(
                    query,
                    region=region,
                    max_results=max_results,
                    timelimit=timelimit,
                )
            elif search_type == "news":
                api_results = ddgs.news(
                    query,
                    region=region,
                    max_results=max_results,
                    timelimit=timelimit,
                )
            elif search_type == "videos":
                api_results = ddgs.videos(
                    query,
                    region=region,
                    max_results=max_results,
                    timelimit=timelimit,
                )
            elif search_type == "books":
                api_results = ddgs.books(query, max_results=max_results)
            elif search_type == "images":
                img_size = kwargs.get("size") or "Wallpaper"
                size_fallbacks = [img_size, "Wallpaper", "Small", "Large", "Medium"]
                api_results = None
                for try_size in size_fallbacks:
                    try:
                        api_results = ddgs.images(
                            query,
                            region=region,
                            max_results=max_results,
                            timelimit=timelimit,
                            size=try_size,
                            color=kwargs.get("color"),
                            type_image=kwargs.get("type_image"),
                            layout=kwargs.get("layout"),
                            license_image=kwargs.get("license_image"),
                        )
                        break
                    except Exception:
                        continue
                if api_results is None:
                    api_results = []
            else:
                return []

            for result in api_results:
                url = result.get("href", result.get("url", result.get("content", "")))
                if not url:
                    continue

                metadata = {}
                if search_type == "videos":
                    metadata["duration"] = result.get("duration")
                    metadata["publisher"] = result.get("publisher")
                elif search_type == "books":
                    metadata["author"] = result.get("author")
                    metadata["year"] = result.get("year")
                elif search_type == "images":
                    metadata["source_url"] = url
                    metadata["thumbnail"] = result.get("thumbnail")
                    metadata["width"] = result.get("width")
                    metadata["height"] = result.get("height")
                    metadata["source"] = result.get("source")
                    url = result.get("image", url)

                results.append(
                    ProviderResult(
                        url=url,
                        title=result.get("title", ""),
                        snippet=result.get("body", result.get("description", "")),
                        date=result.get("date", result.get("published", "")),
                        metadata=metadata,
                    )
                )

        return results
