"""Deterministic fake ddgs backend used by CLI smoke tests."""


class DDGS:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def text(self, query, region="wt-wt", max_results=15, timelimit=None):
        lowered = query.lower()
        if "release status" in lowered or "latest stable release" in lowered:
            return [
                {
                    "href": "https://example.com/support-1",
                    "title": f"{query} confirmed",
                    "body": f"Independent report says {query} and provides confirmation details.",
                },
                {
                    "href": "https://example.org/support-2",
                    "title": f"{query} analysis",
                    "body": f"Analysts note that {query} is accurate based on current release notes.",
                },
                {
                    "href": "https://example.net/conflict-1",
                    "title": f"Fact check: {query}",
                    "body": "Some observers say the claim is false or disputed despite similar keywords.",
                },
            ]
        return [
            {
                "href": "https://example.com/alpha",
                "title": f"{query} Alpha",
                "body": "Alpha body with enough detail to keep as a snippet.",
            },
            {
                "href": "https://example.com/beta",
                "title": f"{query} Beta",
                "body": "Beta body with enough detail to keep as a snippet.",
            },
        ]

    def news(self, query, region="wt-wt", max_results=15, timelimit=None):
        return self.text(query, region=region, max_results=max_results, timelimit=timelimit)

    def videos(self, query, region="wt-wt", max_results=15, timelimit=None):
        return self.text(query, region=region, max_results=max_results, timelimit=timelimit)

    def books(self, query, max_results=15):
        return self.text(query, max_results=max_results)

    def images(
        self,
        query,
        region="wt-wt",
        max_results=15,
        timelimit=None,
        size=None,
        color=None,
        type_image=None,
        layout=None,
        license_image=None,
    ):
        return [
            {
                "href": "https://example.com/image-source",
                "image": "https://example.com/image.png",
                "title": f"{query} Image",
                "body": "Image body",
                "thumbnail": "https://example.com/thumb.png",
                "width": 800,
                "height": 600,
                "source": "example",
            }
        ]
