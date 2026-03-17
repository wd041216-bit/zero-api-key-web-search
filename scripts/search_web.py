#!/usr/bin/env python3
"""
Free Web Search Ultimate - 超级搜索核心 (v5.0 Super Workflow Upgraded)
多引擎并行 + 智能解析 + 反爬虫 + 交叉验证 + 官方API集成
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

@dataclass
class Answer:
    query: str
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

    def _search_ddgs_api(self, query: str) -> List[Source]:
        """使用官方 ddgs 库 (DuckDuckGo API)"""
        results = []
        try:
            from ddgs import DDGS
            # 使用 DDGS 官方库获取结果，无需解析 HTML
            api_results = DDGS().text(query, max_results=10)
            for r in api_results:
                results.append(Source(
                    url=r.get('href', ''),
                    title=r.get('title', ''),
                    snippet=r.get('body', ''),
                    credibility=0.95,  # 官方 API 结果可信度高
                    engine='DDG-API'
                ))
        except ImportError:
            # 如果未安装 ddgs，静默失败，依赖 HTML 备用引擎
            pass
        except Exception:
            pass
        return results

    def _search_ddg_html(self, query: str) -> List[Source]:
        """备用：DuckDuckGo HTML 爬取"""
        q = urllib.parse.quote_plus(query)
        html = self._fetch_with_retry(f'https://html.duckduckgo.com/html/?q={q}')
        if not html:
            return []
        
        results = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            divs = soup.find_all('div', class_='result')
            for div in divs[:8]:
                a = div.find('a', class_='result__a')
                snip = div.find('a', class_='result__snippet')
                if a:
                    href = a.get('href', '')
                    # Decode DDG redirect URL
                    m = re.search(r'uddg=([^&]+)', href)
                    real_url = urllib.parse.unquote(m.group(1)) if m else href
                    if real_url.startswith('http') and 'duckduckgo.com/y.js' not in real_url:
                        # 修复 snippet 词语粘连问题：使用 separator=' '
                        snippet_text = snip.get_text(separator=' ', strip=True) if snip else ''
                        snippet_text = re.sub(r'\s+', ' ', snippet_text)
                        
                        results.append(Source(
                            url=real_url,
                            title=a.get_text(separator=' ', strip=True),
                            snippet=snippet_text,
                            credibility=0.85,
                            engine='DDG-HTML'
                        ))
        except Exception:
            pass
        return results

    def _search_yahoo(self, query: str) -> List[Source]:
        """修复后的 Yahoo 搜索解析器"""
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
                # Yahoo 结构已变，真实链接在 data-matarget="algo" 的 a 标签里
                a = div.find('a', attrs={'data-matarget': 'algo'}) or div.find('a')
                if not a:
                    continue
                    
                href = a.get('href', '')
                # 从重定向 URL 中提取真实 URL
                m = re.search(r'RU=([^/]+)', href)
                real_url = urllib.parse.unquote(m.group(1)) if m else href
                
                # 修复 snippet 提取
                snippet_div = div.find('div', class_=re.compile('compText'))
                snippet_text = snippet_div.get_text(separator=' ', strip=True) if snippet_div else ''
                snippet_text = re.sub(r'\s+', ' ', snippet_text)
                
                title = a.get_text(separator=' ', strip=True)
                # 移除 Yahoo 标题中自带的域名后缀（如 "OpenAIopenai.com › index › gpt-4"）
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
            # 简化URL进行匹配 (忽略 www, http/https, 路径尾斜杠)
            simplified = re.sub(r'^https?://(www\.)?', '', r.url).rstrip('/')
            simplified = simplified.split('#')[0].split('?')[0]
            
            if simplified not in url_groups:
                url_groups[simplified] = []
            url_groups[simplified].append(r)
        
        validated = []
        for url, group in url_groups.items():
            # 优先选择 DDG-API 的结果，因为它的 snippet 最干净
            group.sort(key=lambda x: 1 if x.engine == 'DDG-API' else 0, reverse=True)
            best_source = group[0]
            
            if len(group) >= 2:
                best_source.credibility = min(0.99, best_source.credibility + 0.1 * len(group))
                best_source.cross_validated = True
                engines = set(s.engine for s in group)
                best_source.engine = f"{best_source.engine} (+{len(engines)-1})"
            
            # 选择最长的且质量最好的 snippet
            valid_snippets = [s.snippet for s in group if len(s.snippet) > 20]
            if valid_snippets:
                best_source.snippet = max(valid_snippets, key=len)
                
            validated.append(best_source)
        
        validated.sort(key=lambda x: (x.cross_validated, x.credibility), reverse=True)
        return validated

    def search(self, query: str) -> Answer:
        start_time = time.time()
        
        # 并行执行所有引擎
        engines = [
            self._search_ddgs_api,
            self._search_ddg_html,
            self._search_yahoo
        ]
        
        all_results = []
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = [executor.submit(engine, query) for engine in engines]
            for future in as_completed(futures):
                all_results.extend(future.result())
                
        validated_results = self._cross_validate(all_results)
        
        # 提取摘要作为答案
        answer_text = ""
        if validated_results:
            answer_parts = []
            for i, s in enumerate(validated_results[:5], 1):
                badge = "✓" if s.cross_validated else "○"
                answer_parts.append(f"{i}. {badge} {s.title}\n   {s.snippet}")
            answer_text = "\n\n".join(answer_parts)
        else:
            answer_text = "未找到相关结果，搜索引擎可能受到限制。"
            
        cross_count = sum(1 for s in validated_results if s.cross_validated)
        confidence = "HIGH" if cross_count >= 2 else ("MEDIUM" if validated_results else "LOW")
        
        return Answer(
            query=query,
            answer=answer_text,
            confidence=confidence,
            sources=validated_results[:10],
            validation={
                "total_results": len(all_results),
                "unique_results": len(validated_results),
                "cross_validated": cross_count
            },
            elapsed_ms=int((time.time() - start_time) * 1000)
        )

def main():
    parser = argparse.ArgumentParser(description="Free Web Search Ultimate (v5.0)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    searcher = UltimateSearcher()
    answer = searcher.search(args.query)
    
    if args.json:
        print(json.dumps(asdict(answer), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"🔍 搜索: {answer.query}")
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
                print(f"  {i}. {badge} [{s.engine}] {s.title[:60]}")
                print(f"     URL: {s.url[:80]}...")
        else:
            print("❌ 未找到结果")

if __name__ == "__main__":
    main()
