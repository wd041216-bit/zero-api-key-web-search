#!/usr/bin/env python3
"""
Free Web Search v1.0 - Page Browser
Simple page fetching with urllib
"""

import urllib.request
import sys

def browse_page(url):
    """Fetch and display page content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Simple text extraction
            import re
            # Remove scripts and styles
            text = re.sub(r'\u003cscript[^\u003e]*\u003e.*?\u003c/script\u003e', '', html, flags=re.DOTALL|re.I)
            text = re.sub(r'\u003cstyle[^\u003e]*\u003e.*?\u003c/style\u003e', '', text, flags=re.DOTALL|re.I)
            # Remove HTML tags
            text = re.sub(r'\u003c[^\u003e]+\u003e', ' ', text)
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
    except Exception as e:
        return f"Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python browse.py 'https://example.com'")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"🌐 Browsing: {url}\n")
    
    content = browse_page(url)
    
    # Print first 2000 chars
    print(content[:2000])
    
    if len(content) > 2000:
        print(f"\n... ({len(content) - 2000} more chars)")

if __name__ == "__main__":
    main()
