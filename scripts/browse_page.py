#!/usr/bin/env python3
"""
Free Web Search Ultimate - 网页浏览与提取 (v7.0)
修复标题提取问题，支持 gzip 自动解压，增强容错能力
"""
import argparse
import gzip
import json
import re
import ssl
import sys
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def extract_text(html: str) -> str:
    """简单的文本提取，移除脚本和样式"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除无用标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()
            
        # 提取标题 (修复 .string 可能为 None 的问题)
        title = "Unknown Title"
        if soup.title:
            title = soup.title.get_text(strip=True)
            if not title:
                title = "Unknown Title"
        
        # 提取正文
        text = soup.get_text(separator=' ', strip=True)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return title, text
    except ImportError:
        # Fallback to regex if bs4 not available
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.DOTALL)
        title = "Unknown Title"
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            title = re.sub(r'\s+', ' ', title)
        
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return title, text

def browse(url: str, max_chars: int = 10000) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            raw = r.read()
            encoding = r.headers.get('Content-Encoding', '')
            
            # 自动解压 gzip 内容
            if encoding == 'gzip':
                html = gzip.decompress(raw).decode('utf-8', errors='ignore')
            elif encoding == 'deflate':
                import zlib
                html = zlib.decompress(raw).decode('utf-8', errors='ignore')
            else:
                html = raw.decode('utf-8', errors='ignore')
            
            title, text = extract_text(html)
            
            content = text[:max_chars]
            is_truncated = len(text) > max_chars
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "content": content,
                "truncated": is_truncated,
                "total_length": len(text)
            }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Web Page Browser (v7.0)")
    parser.add_argument("url", help="URL to browse")
    parser.add_argument("--max-chars", type=int, default=10000, help="Maximum characters to return")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    result = browse(args.url, args.max_chars)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["status"] == "success":
            print(f"\n📄 {result['title']}")
            print(f"🔗 {result['url']}")
            print(f"{'='*60}\n")
            print(result['content'])
            if result['truncated']:
                print(f"\n... [Truncated. Total length: {result['total_length']} chars]")
        else:
            print(f"❌ Error browsing {result['url']}: {result['error']}")

if __name__ == "__main__":
    main()
