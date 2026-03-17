#!/usr/bin/env python3
"""
Free Web Search Ultimate - 超级搜索核心 (v6.0 Super Workflow Upgraded)
支持普通网页与新闻搜索 + 时间过滤 + 智能解析 + 交叉验证
"""
import argparse
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

# 全局禁用 SSL 验证，应对部分网络环境
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

@dataclass
class Source:
    url: str
    title: str
    snippet: str = ""
    credibility: float = 0.0
    engine: str = ""
    cross_validated: bool = False
    date: str = ""

@dataclass
class Answer:
    query: str
    search_type: str
    answer: str
    confidence: str
    sources: List[Source]
    validation: Dict
    elapsed_ms: int

class UltimateSearcher:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        import random
        self.headers = {
            'User-Agent': random.choice(UA_LIST),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

    def _fetch_with_retry(self, url: str, retries: int = 2) -> Optional[str]:
        """带指数退避的重试机制"""
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as r:
                    return r.read().decode('utf-8', errors='ignore')
            except Exception:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _search_ddgs_text(self, query: str, timelimit: str = None) -> List[Source]:
        """使用官方 ddgs 库进行网页搜索"""
        results = []
        try:
            from ddgs import DDGS
            # page=1 和 page=2 混合获取更多结果
            for page in [1, 2]:
                api_results = DDGS().text(query, max_results=10, timelimit=timelimit, page=page)
                for r in api_results:
                    results.append(Source(
                        url=r.get('href', ''),
                        title=r.get('title', ''),
                        snippet=r.get('body', ''),
                        credibility=0.95,
                        engine='DDG-Web'
                    ))
        except Exception:
            pass
        return results

    def _search_ddgs_news(self, query: str, timelimit: str = None) -> List[Source]:
        """使用官方 ddgs 库进行新闻搜索"""
        results = []
        try:
            from ddgs import DDGS
            api_results = DDGS().news(query, max_results=15, timelimit=timelimit)
            for r in api_results:
                results.append(Source(
                    url=r.get('url', ''),
                    title=r.get('title', ''),
                    snippet=r.get('body', ''),
                    date=r.get('date', ''),
                    credibility=0.98,  # 新闻源可信度更高
                    engine='DDG-News'
                ))
        except Exception:
            pass
        return results

    def _search_yahoo(self, query: str) -> List[Source]:
        """Yahoo 搜索解析器 (作为备用)"""
        q = urllib.parse.quote_plus(query)
        html = self._fetch_with_retry(f'https://search.yahoo.com/search?p={q}')
        if not html:
            return []
        
        results = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            divs = soup.find_all('div', class_=re.compile('algo'))
            for div in divs[:8]:
                a = div.find('a', attrs={'data-matarget': 'algo'}) or div.find('a')
                if not a:
                    continue
                    
                href = a.get('href', '')
                m = re.search(r'RU=([^/]+)', href)
                real_url = urllib.parse.unquote(m.group(1)) if m else href
                
                # 过滤图片搜索链接
                if 'images.search.yahoo.com' in real_url or 'video.search.yahoo.com' in real_url:
                    continue
                
                snippet_div = div.find('div', class_=re.compile('compText'))
                snippet_text = snippet_div.get_text(separator=' ', strip=True) if snippet_div else ''
                snippet_text = re.sub(r'\s+', ' ', snippet_text)
                
                title = a.get_text(separator=' ', strip=True)
                title = re.sub(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*›.*$', '', title).strip()
                
                if real_url.startswith('http'):
                    results.append(Source(
                        url=real_url,
                        title=title,
                        snippet=snippet_text,
                        credibility=0.85,
                        engine='Yahoo'
                    ))
        except Exception:
            pass
        return results

    def _cross_validate(self, all_results: List[Source]) -> List[Source]:
        """交叉验证和去重"""
        url_groups = {}
        for r in all_results:
            # 简化URL进行匹配
            simplified = re.sub(r'^https?://(www\.)?', '', r.url).rstrip('/')
            simplified = simplified.split('#')[0].split('?')[0]
            
            if not simplified:
                continue
                
            if simplified not in url_groups:
                url_groups[simplified] = []
            url_groups[simplified].append(r)
        
        validated = []
        for url, group in url_groups.items():
            # 优先选择 DDG 的结果
            group.sort(key=lambda x: 1 if x.engine.startswith('DDG') else 0, reverse=True)
            best_source = group[0]
            
            if len(group) >= 2:
                best_source.credibility = min(0.99, best_source.credibility + 0.1 * len(group))
                best_source.cross_validated = True
                engines = set(s.engine for s in group)
                best_source.engine = f"{best_source.engine} (+{len(engines)-1})"
            
            valid_snippets = [s.snippet for s in group if len(s.snippet) > 20]
            if valid_snippets:
                best_source.snippet = max(valid_snippets, key=len)
                
            validated.append(best_source)
        
        validated.sort(key=lambda x: (x.cross_validated, x.credibility), reverse=True)
        return validated

    def search(self, query: str, search_type: str = "auto", timelimit: str = None) -> Answer:
        start_time = time.time()
        
        # 自动推断搜索类型
        is_news = False
        if search_type == "news":
            is_news = True
        elif search_type == "auto":
            news_keywords = ['news', 'latest', 'today', 'update', '新闻', '最新', '今日']
            is_news = any(k in query.lower() for k in news_keywords)
            
        engines = []
        if is_news:
            engines = [(self._search_ddgs_news, query, timelimit)]
        else:
            engines = [
                (self._search_ddgs_text, query, timelimit),
                (self._search_yahoo, query)
            ]
        
        all_results = []
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = [executor.submit(*e) for e in engines]
            for future in as_completed(futures):
                all_results.extend(future.result())
                
        validated_results = self._cross_validate(all_results)
        
        # 提取摘要作为答案
        answer_text = ""
        if validated_results:
            answer_parts = []
            for i, s in enumerate(validated_results[:5], 1):
                badge = "✓" if s.cross_validated else "○"
                date_str = f" [{s.date}]" if s.date else ""
                answer_parts.append(f"{i}. {badge} {s.title}{date_str}\n   {s.snippet}")
            answer_text = "\n\n".join(answer_parts)
        else:
            answer_text = "未找到相关结果，搜索引擎可能受到限制。"
            
        cross_count = sum(1 for s in validated_results if s.cross_validated)
        confidence = "HIGH" if cross_count >= 2 else ("MEDIUM" if validated_results else "LOW")
        
        return Answer(
            query=query,
            search_type="news" if is_news else "text",
            answer=answer_text,
            confidence=confidence,
            sources=validated_results[:15],
            validation={
                "total_results": len(all_results),
                "unique_results": len(validated_results),
                "cross_validated": cross_count
            },
            elapsed_ms=int((time.time() - start_time) * 1000)
        )

def main():
    parser = argparse.ArgumentParser(description="Free Web Search Ultimate (v6.0)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--type", choices=["auto", "text", "news"], default="auto", help="搜索类型: auto, text, news")
    parser.add_argument("--timelimit", choices=["d", "w", "m", "y"], help="时间限制: d(天), w(周), m(月), y(年)")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    searcher = UltimateSearcher()
    answer = searcher.search(args.query, search_type=args.type, timelimit=args.timelimit)
    
    if args.json:
        print(json.dumps(asdict(answer), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"🔍 搜索: {answer.query} (类型: {answer.search_type})")
        print(f"⏱️  耗时: {answer.elapsed_ms}ms | 置信度: {answer.confidence}")
        print(f"📊 结果: 找到 {answer.validation['unique_results']} 个独立结果，{answer.validation['cross_validated']} 个交叉验证")
        print(f"{'='*60}\n")
        
        if answer.sources:
            print("📋 摘要结果:\n")
            print(answer.answer)
            print(f"\n{'-'*60}")
            print("🔗 详细来源:")
            for i, s in enumerate(answer.sources, 1):
                badge = "✓" if s.cross_validated else "○"
                date_str = f" [{s.date}]" if s.date else ""
                print(f"  {i}. {badge} [{s.engine}] {s.title[:60]}{date_str}")
                print(f"     URL: {s.url[:80]}...")
        else:
            print("❌ 未找到结果")

if __name__ == "__main__":
    main()
