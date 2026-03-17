#!/usr/bin/env python3
"""
Free Web Search Ultimate - 超级搜索核心 (v9.0 Super Workflow Upgraded)
新增 images 搜索，支持丰富过滤参数，移除冗余的双任务并发，优化 JSON 输出
"""
import argparse
import json
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

# 全局禁用 SSL 验证，应对部分网络环境
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

@dataclass
class Source:
    url: str
    title: str
    snippet: str = ""
    rank: int = 0
    engine: str = ""
    cross_validated: bool = False
    date: str = ""
    extra: Dict = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

@dataclass
class Answer:
    query: str
    search_type: str
    answer: str
    confidence: str
    sources: List[Source]
    validation: Dict
    metadata: Dict
    elapsed_ms: int

class UltimateSearcher:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        
    def _search_ddgs(self, query: str, search_type: str, timelimit: str = None, region: str = "wt-wt", max_results: int = 15, **kwargs) -> List[Source]:
        """使用官方 ddgs 库进行搜索（每次调用创建新实例保证线程安全）"""
        results = []
        try:
            from ddgs import DDGS
            # 创建局部实例
            with DDGS(timeout=self.timeout) as ddgs:
                if search_type == "text":
                    api_results = ddgs.text(query, region=region, max_results=max_results, timelimit=timelimit)
                elif search_type == "news":
                    api_results = ddgs.news(query, region=region, max_results=max_results, timelimit=timelimit)
                elif search_type == "videos":
                    api_results = ddgs.videos(query, region=region, max_results=max_results, timelimit=timelimit)
                elif search_type == "books":
                    api_results = ddgs.books(query, max_results=max_results)
                elif search_type == "images":
                    # images 接口支持丰富的 kwargs
                    # 注意：ddgs images 的 size 参数可用性与网络环境相关，自动降级尝试
                    img_size = kwargs.get('size') or 'Wallpaper'
                    size_fallbacks = [img_size, 'Wallpaper', 'Small', 'Large', 'Medium']
                    api_results = None
                    for try_size in size_fallbacks:
                        try:
                            api_results = ddgs.images(query, region=region, max_results=max_results, timelimit=timelimit, 
                                                    size=try_size, color=kwargs.get('color'), 
                                                    type_image=kwargs.get('type_image'), layout=kwargs.get('layout'),
                                                    license_image=kwargs.get('license_image'))
                            break  # 成功则退出循环
                        except Exception:
                            continue  # 尝试下一个 size
                    if api_results is None:
                        api_results = []
                else:
                    return []
                    
                for r in api_results:
                    url = r.get('href', r.get('url', r.get('content', '')))
                    if not url:
                        continue
                        
                    source = Source(
                        url=url,
                        title=r.get('title', ''),
                        snippet=r.get('body', r.get('description', '')),
                        rank=0, # 初始 rank，后续处理
                        engine=f'DDG-{search_type.capitalize()}',
                        date=r.get('date', r.get('published', '')),
                        extra={}
                    )
                    
                    # 提取不同类型的额外信息
                    if search_type == "videos":
                        source.extra['duration'] = r.get('duration')
                        source.extra['publisher'] = r.get('publisher')
                    elif search_type == "books":
                        source.extra['author'] = r.get('author')
                        source.extra['year'] = r.get('year')
                    elif search_type == "images":
                        source.url = r.get('image', url) # image 搜索中，url 字段通常是来源页，image 字段是原图
                        source.extra['source_url'] = url
                        source.extra['thumbnail'] = r.get('thumbnail')
                        source.extra['width'] = r.get('width')
                        source.extra['height'] = r.get('height')
                        source.extra['source'] = r.get('source')
                        
                    results.append(source)
        except Exception as e:
            results.append(Source(url="error", title=f"Error: {str(e)}", engine="error"))
        return results

    def _cross_validate(self, all_results: List[Source]) -> List[Source]:
        """交叉验证和去重，并分配 rank"""
        url_groups = {}
        for r in all_results:
            if r.url == "error":
                continue
                
            simplified = re.sub(r'^https?://(www\.)?', '', r.url).rstrip('/')
            simplified = simplified.split('#')[0].split('?')[0]
            
            if not simplified:
                continue
                
            if simplified not in url_groups:
                url_groups[simplified] = []
            url_groups[simplified].append(r)
        
        validated = []
        for url, group in url_groups.items():
            best_source = group[0]
            
            if len(group) >= 2:
                best_source.cross_validated = True
                best_source.engine = f"{best_source.engine} (x{len(group)})"
            
            valid_snippets = [s.snippet for s in group if len(s.snippet) > 20]
            if valid_snippets:
                best_source.snippet = max(valid_snippets, key=len)
                
            validated.append(best_source)
        
        # 按原始出现顺序和交叉验证情况排序
        validated.sort(key=lambda x: x.cross_validated, reverse=True)
        
        # 分配 rank
        for i, s in enumerate(validated, 1):
            s.rank = i
            
        return validated

    def search(self, query: str, search_type: str = "text", timelimit: str = None, region: str = "wt-wt", **kwargs) -> Answer:
        start_time = time.time()
        
        # v9.0 优化：不再使用双任务并发获取同一类型结果，而是直接请求足够的数量，避免浪费网络
        max_results = 30 if search_type == "text" else 20
        
        # 仍然使用 ThreadPoolExecutor 以便未来扩展多引擎，目前只有一个任务
        engines = [(self._search_ddgs, query, search_type, timelimit, region, max_results)]
        
        all_results = []
        errors = []
        with ThreadPoolExecutor(max_workers=1) as executor:
            # 传递 kwargs 给任务
            futures = [executor.submit(e[0], e[1], e[2], e[3], e[4], e[5], **kwargs) for e in engines]
            for future in as_completed(futures):
                res = future.result()
                for r in res:
                    if r.url == "error":
                        errors.append(r.title)
                    else:
                        all_results.append(r)
                
        validated_results = self._cross_validate(all_results)
        
        # v9.0 优化：answer 字段改为极简摘要，不重复完整 snippet，节省 token
        answer_text = ""
        if validated_results:
            answer_parts = []
            for i, s in enumerate(validated_results[:5], 1):
                badge = "✓" if s.cross_validated else "○"
                answer_parts.append(f"{i}. {badge} [{s.title}]({s.url})")
            answer_text = "Top Sources:\n" + "\n".join(answer_parts)
        else:
            error_msg = f" (Errors: {'; '.join(errors)})" if errors else ""
            answer_text = f"未找到相关结果，搜索引擎可能受到限制。{error_msg}"
            
        cross_count = sum(1 for s in validated_results if s.cross_validated)
        confidence = "HIGH" if cross_count >= 2 else ("MEDIUM" if validated_results else "LOW")
        
        return Answer(
            query=query,
            search_type=search_type,
            answer=answer_text,
            confidence=confidence,
            sources=validated_results[:max_results],
            validation={
                "total_results": len(all_results),
                "unique_results": len(validated_results),
                "cross_validated": cross_count
            },
            metadata={
                "engines_used": [e[2] for e in engines],
                "errors": errors
            },
            elapsed_ms=int((time.time() - start_time) * 1000)
        )

def main():
    parser = argparse.ArgumentParser(description="Free Web Search Ultimate (v9.0)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--type", choices=["text", "news", "videos", "books", "images"], default="text", help="搜索类型")
    parser.add_argument("--region", default="wt-wt", help="地区代码，如 zh-cn, en-us, wt-wt(全球)")
    parser.add_argument("--timelimit", choices=["d", "w", "m", "y"], help="时间限制: d(天), w(周), m(月), y(年)")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    # images 专属参数
    parser.add_argument("--size", choices=["Small", "Medium", "Large", "Wallpaper"], help="[images] 图片尺寸")
    parser.add_argument("--color", help="[images] 图片颜色，如 Red, Blue, Monochrome 等")
    parser.add_argument("--type_image", choices=["photo", "clipart", "gif", "transparent", "line"], help="[images] 图片类型")
    parser.add_argument("--license", choices=["any", "Public", "Share", "ShareCommercially", "Modify", "ModifyCommercially"], help="[images] 图片许可")
    
    args = parser.parse_args()
    
    kwargs = {}
    if args.size: kwargs['size'] = args.size
    if args.color: kwargs['color'] = args.color
    if args.type_image: kwargs['type_image'] = args.type_image
    if args.license: kwargs['license_image'] = args.license
    
    searcher = UltimateSearcher()
    answer = searcher.search(args.query, search_type=args.type, timelimit=args.timelimit, region=args.region, **kwargs)
    
    if args.json:
        print(json.dumps(asdict(answer), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"🔍 搜索: {answer.query} (类型: {answer.search_type} | 地区: {args.region})")
        print(f"⏱️  耗时: {answer.elapsed_ms}ms | 置信度: {answer.confidence}")
        print(f"📊 结果: 找到 {answer.validation['unique_results']} 个独立结果")
        if answer.metadata['errors']:
            print(f"⚠️ 警告: 发生 {len(answer.metadata['errors'])} 个引擎错误")
        print(f"{'='*60}\n")
        
        if answer.sources:
            print("📋 简明摘要:\n")
            print(answer.answer)
            print(f"\n{'-'*60}")
            print("🔗 详细来源:")
            for s in answer.sources:
                badge = "✓" if s.cross_validated else "○"
                date_str = f" [{s.date}]" if s.date else ""
                extra_str = f" {s.extra}" if s.extra else ""
                print(f"  {s.rank}. {badge} [{s.engine}] {s.title[:60]}{date_str}{extra_str}")
                # v9.0 优化：不再截断 URL，完整输出
                print(f"     URL: {s.url}")
        else:
            print("❌ 未找到结果")

if __name__ == "__main__":
    main()
