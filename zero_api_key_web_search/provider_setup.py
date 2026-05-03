#!/usr/bin/env python3
"""Interactive provider setup wizard for zero-api-key-web-search.

Guides users through configuring Bright Data (production) and SearXNG (free)
search providers, validates API keys, and writes .env files.

Entry point:
    zero-setup [options]
"""

import argparse
import os
from pathlib import Path

from zero_api_key_web_search.core import UltimateSearcher
from zero_api_key_web_search.providers import BrightDataProvider, SearxngProvider


BRIGHTDATA_SIGNUP_URL = "https://get.brightdata.com/h21j9xz4uxgd"


def _test_brightdata(api_key: str, zone: str = "serp_api1") -> dict:
    """Test a Bright Data API key by making a real search request."""
    provider = BrightDataProvider(api_key=api_key, zone=zone)
    if not provider.is_configured():
        return {"success": False, "error": "API key is empty"}
    try:
        results = provider.search("test", search_type="text", region="wt-wt", max_results=3)
        if results and any(r.url != "error" for r in results):
            return {
                "success": True,
                "result_count": len(results),
                "sample_title": results[0].title[:60] if results else "",
                "sample_url": results[0].url[:80] if results else "",
            }
        return {"success": False, "error": "Search returned no valid results"}
    except RuntimeError as e:
        error_msg = str(e)
        if "zone" in error_msg.lower() and "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Zone '{zone}' not found. Create it in Bright Data Dashboard: Proxies → Add new zone → SERP API → name it '{zone}'",
                "needs_zone": True,
            }
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _test_searxng(url: str) -> dict:
    """Test a SearXNG instance URL."""
    provider = SearxngProvider(base_url=url)
    if not provider.is_configured():
        return {"success": False, "error": "URL is empty"}
    try:
        results = provider.search("test", search_type="text", region="wt-wt", max_results=3)
        if results:
            return {
                "success": True,
                "result_count": len(results),
                "sample_title": results[0].title[:60] if results else "",
            }
        return {"success": False, "error": "SearXNG returned no results"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _write_env_file(env_vars: dict, path: str = ".env") -> None:
    """Write environment variables to a .env file."""
    env_path = Path(path)
    existing = {}
    if env_path.exists():
        for line in env_path.read_text().strip().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                existing[key.strip()] = value.strip()

    existing.update(env_vars)
    lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    env_path.write_text("\n".join(lines) + "\n")
    print(f"\n✅ Written to {env_path.resolve()}")


def _print_export_commands(env_vars: dict) -> None:
    """Print export commands for the shell."""
    print("\n📋 Run these commands to set environment variables:")
    for key, value in env_vars.items():
        print(f"  export {key}={value}")
    print("\nOr add them to your .bashrc / .zshrc for persistence.")


def _show_provider_status() -> None:
    """Show current provider status."""
    searcher = UltimateSearcher()
    statuses = searcher.provider_statuses()
    profiles = searcher.provider_profiles()
    guidance = searcher._provider_guidance()

    print("\n" + "=" * 60)
    print("🔍 Provider Status")
    print("=" * 60)

    for item in statuses:
        status_icon = "✅" if item["status"] == "ready" else "⚪" if item["status"] == "not_configured" else "🔧"
        print(f"\n{status_icon} {item['name']}: {item['status']} ({item['kind']})")
        print(f"   {item['description']}")
        if item["status"] != "ready":
            print(f"   Setup: {item.get('setup', '')}")

    current = ", ".join(provider.name for provider in searcher.providers)
    print(f"\n🔄 Active providers: {current}")

    print("\n📋 Provider Profiles:")
    for name, item in profiles.items():
        print(f"   {name}: {', '.join(item['providers'])} — {item['description']}")

    print(f"\n💡 Recommendation: {guidance.get('recommended_next_step', '')}")


def run_interactive_setup(write_env: bool = True) -> None:
    """Run the interactive provider setup wizard."""
    print("\n" + "=" * 60)
    print("🔧 Zero-API-Key Web Search — Provider Setup")
    print("=" * 60)

    _show_provider_status()

    env_vars = {}

    # Bright Data setup
    print("\n" + "-" * 60)
    print("📦 Bright Data (Production-grade SERP)")
    print("-" * 60)
    print(f"Sign up with 5000 free credits: {BRIGHTDATA_SIGNUP_URL}")

    bd_key = input("\n  Enter your Bright Data API key (or press Enter to skip): ").strip()
    if bd_key:
        zone = input("  Enter your SERP zone name [serp_api1]: ").strip() or "serp_api1"
        print(f"\n  Testing Bright Data (zone: {zone})...")
        result = _test_brightdata(bd_key, zone)
        if result["success"]:
            print(f"  ✅ Bright Data working! Got {result['result_count']} results.")
            print(f"     Sample: {result.get('sample_title', '')}")
            env_vars["ZERO_SEARCH_BRIGHTDATA_API_KEY"] = bd_key
            if zone != "web_search":
                env_vars["ZERO_SEARCH_BRIGHTDATA_ZONE"] = zone
        else:
            print(f"  ❌ {result['error']}")
            if result.get("needs_zone"):
                print(f"\n  📝 To fix: In Bright Data Dashboard → Proxies → Add new zone → SERP API → name it '{zone}'")
                print(f"     Then re-run this setup wizard.")
            retry = input("  Try again with a different key/zone? (y/n): ").strip().lower()
            if retry == "y":
                bd_key2 = input("  API key: ").strip()
                zone2 = input(f"  Zone name [{zone}]: ").strip() or zone
                result2 = _test_brightdata(bd_key2, zone2)
                if result2["success"]:
                    print(f"  ✅ Bright Data working! Got {result2['result_count']} results.")
                    env_vars["ZERO_SEARCH_BRIGHTDATA_API_KEY"] = bd_key2
                    if zone2 != "web_search":
                        env_vars["ZERO_SEARCH_BRIGHTDATA_ZONE"] = zone2
                else:
                    print(f"  ❌ Still failing: {result2['error']}")
                    print("  You can set the environment variable later and re-run this wizard.")

    # SearXNG setup
    print("\n" + "-" * 60)
    print("🏠 SearXNG (Free self-hosted)")
    print("-" * 60)
    print("  Self-host a SearXNG instance for free cross-validation.")
    print("  See: https://github.com/searxng/searxng")

    searxng_url = input("\n  Enter your SearXNG URL (or press Enter to skip): ").strip()
    if searxng_url:
        print(f"\n  Testing SearXNG at {searxng_url}...")
        result = _test_searxng(searxng_url)
        if result["success"]:
            print(f"  ✅ SearXNG working! Got {result['result_count']} results.")
            env_vars["ZERO_SEARCH_SEARXNG_URL"] = searxng_url
        else:
            print(f"  ❌ {result['error']}")

    # Save
    if env_vars:
        print("\n" + "=" * 60)
        print("💾 Configuration Summary")
        print("=" * 60)
        for key, value in env_vars.items():
            masked = value[:8] + "..." if len(value) > 12 else value
            print(f"  {key}={masked}")

        if write_env:
            choice = input("\n  Save to .env file? (Y/n): ").strip().lower()
            if choice != "n":
                _write_env_file(env_vars)
            else:
                _print_export_commands(env_vars)
        else:
            _print_export_commands(env_vars)

    # Show final status
    print("\n" + "=" * 60)
    print("🔄 Final Provider Status")
    print("=" * 60)

    # Re-init with new env vars
    for key, value in env_vars.items():
        os.environ[key] = value

    _show_provider_status()

    # Recommended profile
    bd_ready = bool(env_vars.get("ZERO_SEARCH_BRIGHTDATA_API_KEY"))
    sx_ready = bool(env_vars.get("ZERO_SEARCH_SEARXNG_URL"))
    if bd_ready and sx_ready:
        print("\n🎯 Recommended profile: max-evidence (all providers)")
    elif bd_ready:
        print("\n🎯 Recommended profile: production (Bright Data)")
    elif sx_ready:
        print("\n🎯 Recommended profile: free-verified (DDGS + SearXNG)")
    else:
        print("\n🎯 Using default profile: free (DDGS only)")


def main():
    """CLI entry point for provider setup."""
    parser = argparse.ArgumentParser(
        description="Zero-API-Key Web Search — Provider Setup Wizard",
        epilog=(
            "Examples:\n"
            "  zero-setup\n"
            "  zero-setup --status\n"
            "  zero-setup --test-brightdata YOUR_API_KEY\n"
            "  zero-setup --test-searxng http://localhost:8080\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Show provider status only")
    parser.add_argument("--test-brightdata", metavar="API_KEY", help="Test a Bright Data API key")
    parser.add_argument("--zone", default="serp_api1", help="Bright Data zone name (default: serp_api1)")
    parser.add_argument("--test-searxng", metavar="URL", help="Test a SearXNG instance URL")
    parser.add_argument("--no-env", action="store_true", help="Don't write .env file, print export commands instead")

    args = parser.parse_args()

    if args.status:
        _show_provider_status()
        return

    if args.test_brightdata:
        result = _test_brightdata(args.test_brightdata, args.zone)
        if result["success"]:
            print(f"✅ Bright Data API key is valid. Got {result['result_count']} results.")
            print(f"   Sample: {result.get('sample_title', '')}")
        else:
            print(f"❌ Bright Data test failed: {result['error']}")
            if result.get("needs_zone"):
                print(f"   Create zone '{args.zone}' in Bright Data Dashboard → Proxies → Add new zone → SERP API")
        return

    if args.test_searxng:
        result = _test_searxng(args.test_searxng)
        if result["success"]:
            print(f"✅ SearXNG is working. Got {result['result_count']} results.")
        else:
            print(f"❌ SearXNG test failed: {result['error']}")
        return

    # Interactive setup
    run_interactive_setup(write_env=not args.no_env)


if __name__ == "__main__":
    main()