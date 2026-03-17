#!/usr/bin/env python3
"""
Free Web Search v1.0 - Simple Search Script
Uses DuckDuckGo + Bing fallback
"""

import urllib.request
import urllib.parse
import sys

def search_ddg(query):
    """Search DuckDuckGo Lite"""
    try:
        url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote_plus(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def search_bing(query):
    """Search Bing (fallback)"""
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py 'your query'")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"🔍 Searching: {query}\n")
    
    # Try DuckDuckGo first
    print("Trying DuckDuckGo...")
    result = search_ddg(query)
    
    if result:
        print("✅ DuckDuckGo success")
        # Print first 500 chars as preview
        print(result[:500])
    else:
        # Fallback to Bing
        print("❌ DuckDuckGo failed, trying Bing...")
        result = search_bing(query)
        
        if result:
            print("✅ Bing success")
            print(result[:500])
        else:
            print("❌ Both engines failed")

if __name__ == "__main__":
    main()
