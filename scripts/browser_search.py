#!/usr/bin/env python3
"""
Free Web Search Ultimate v4.0 - 浏览器版
史上最强免费搜索 - Playwright浏览器模式
"""

import asyncio
import json
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class Source:
    url: str
    title: str
    credibility: float = 0.0
    engine: str = "Browser"

@dataclass
class Answer:
    query: str
    answer: str
    confidence: str
    sources: List[Source]
    elapsed_ms: int

async def search_with_browser(query: str) -> Answer:
    """使用Playwright浏览器搜索"""
    import time
    start = time.time()
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 使用DuckDuckGo
            await page.goto(f'https://duckduckgo.com/?q={query}')
            await page.wait_for_load_state('networkidle')
            
            # 等待结果加载
            await page.wait_for_selector('.result', timeout=10000)
            
            # 提取结果
            results = []
            links = await page.query_selector_all('.result__a')
            
            for link in links[:5]:
                try:
                    href = await link.get_attribute('href')
                    title = await link.inner_text()
                    if href and title and len(title) > 5:
                        results.append(Source(
                            url=href,
                            title=title.strip(),
                            credibility=0.95,
                            engine='Browser-DDG'
                        ))
                except:
                    continue
            
            await browser.close()
            
            elapsed = int((time.time() - start) * 1000)
            
            if results:
                answer_text = "\n".join([f"{i+1}. {s.title}" for i, s in enumerate(results[:3])])
                return Answer(
                    query=query,
                    answer=answer_text,
                    confidence="HIGH",
                    sources=results,
                    elapsed_ms=elapsed
                )
            else:
                return Answer(
                    query=query,
                    answer="未找到结果",
                    confidence="LOW",
                    sources=[],
                    elapsed_ms=elapsed
                )
                
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return Answer(
            query=query,
            answer=f"搜索失败: {str(e)[:50]}",
            confidence="LOW",
            sources=[],
            elapsed_ms=elapsed
        )

def main():
    if len(sys.argv) < 2:
        print("Usage: python browser_search.py 'your query'")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"🔍 浏览器搜索: {query}\n")
    
    answer = asyncio.run(search_with_browser(query))
    
    print(f"{'='*60}")
    print(f"⏱️  {answer.elapsed_ms}ms | 可信度: {answer.confidence}")
    print(f"{'='*60}")
    print(f"\n📋 答案:\n{answer.answer}")
    
    if answer.sources:
        print(f"\n🔗 来源:")
        for i, s in enumerate(answer.sources, 1):
            print(f"  {i}. {s.title[:50]}...")
            print(f"     {s.url[:60]}...")

if __name__ == "__main__":
    main()
