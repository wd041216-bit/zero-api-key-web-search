#!/usr/bin/env python3
"""
Browse Page v4.0 - 智能页面浏览
- 三级策略：Fast/Stealth/Dynamic
"""

import argparse
import json
import time
import urllib.request

class PageBrowser:
    def __init__(self, timeout=30):
        self.timeout = timeout
    
    def fetch_fast(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return None
    
    def fetch_stealth(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            }
            req = urllib.request.Request(url, headers=headers)
            time.sleep(0.5)
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return None
    
    def browse(self, url, mode="auto", max_words=600):
        print(f"🌐 浏览: {url}")
        print(f"🎯 模式: {mode}\n")
        
        html = None
        used_mode = mode
        
        if mode == "auto":
            html = self.fetch_fast(url)
            used_mode = "fast" if html else "stealth"
            if not html:
                html = self.fetch_stealth(url)
        elif mode == "fast":
            html = self.fetch_fast(url)
        elif mode == "stealth":
            html = self.fetch_stealth(url)
        
        if not html:
            return {"url": url, "error": "获取失败", "confidence": "LOW"}
        
        # 简单提取
        import re
        title = re.search(r'<title>([^<]+)</title>', html, re.I)
        title = title.group(1).strip() if title else "N/A"
        
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL|re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        words = text.split()
        confidence = "HIGH" if len(words) > 100 else "MEDIUM" if len(words) > 50 else "LOW"
        
        return {
            "url": url,
            "title": title,
            "content": text[:max_words*6],
            "word_count": len(words),
            "mode": used_mode,
            "confidence": confidence
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True)
    parser.add_argument("-m", "--mode", default="auto", choices=["auto", "fast", "stealth"])
    parser.add_argument("-w", "--max-words", type=int, default=600)
    parser.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    browser = PageBrowser()
    result = browser.browse(args.url, args.mode, args.max_words)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"📄 {result.get('title', 'N/A')}")
        print(f"✅ 置信度: {result.get('confidence', 'N/A')}")
        print(f"📊 字数: {result.get('word_count', 0)}")
        print(f"\n{result.get('content', '')[:500]}...")

if __name__ == "__main__":
    main()
