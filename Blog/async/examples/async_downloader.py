#!/usr/bin/env python3
"""
异步下载器 - 实战项目1
可以并发下载多个URL内容
运行方法：python async_downloader.py
需要安装：pip install aiohttp
"""

import asyncio
import aiohttp
import time
from typing import List, Dict
import os

class AsyncDownloader:
    """异步下载器类"""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 10):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'AsyncDownloader/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def download_single(self, url: str) -> Dict[str, any]:
        """下载单个URL"""
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                content_length = len(content)
                
                print(f"✅ {url} - 状态码: {response.status}, 大小: {content_length:,}字符")
                
                return {
                    'url': url,
                    'status_code': response.status,
                    'success': True,
                    'content_length': content_length,
                    'content_preview': content[:200] + '...' if len(content) > 200 else content,
                    'headers': dict(response.headers)
                }
                
        except asyncio.TimeoutError:
            print(f"⏰ {url} - 超时")
            return {
                'url': url,
                'success': False,
                'error': 'timeout',
                'error_message': '请求超时'
            }
        except aiohttp.ClientError as e:
            print(f"❌ {url} - 网络错误: {e}")
            return {
                'url': url,
                'success': False,
                'error': 'network_error',
                'error_message': str(e)
            }
        except Exception as e:
            print(f"💥 {url} - 意外错误: {e}")
            return {
                'url': url,
                'success': False,
                'error': 'unknown_error',
                'error_message': str(e)
            }
    
    async def download_multiple(self, urls: List[str]) -> List[Dict[str, any]]:
        """并发下载多个URL"""
        if not self.session:
            raise RuntimeError("请使用异步上下文管理器")
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def download_with_semaphore(url: str):
            async with semaphore:
                return await self.download_single(url)
        
        # 创建所有任务
        tasks = [download_with_semaphore(url) for url in urls]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': 'exception',
                    'error_message': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def download_with_progress(self, urls: List[str]) -> Dict[str, any]:
        """带进度显示的下载"""
        total_urls = len(urls)
        completed = 0
        failed = 0
        
        print(f"\n🌐 开始下载 {total_urls} 个URL")
        print(f"最大并发数: {self.max_concurrent}")
        print("-" * 50)
        
        results = await self.download_multiple(urls)
        
        # 统计结果
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        total_size = sum(r.get('content_length', 0) for r in successful_results)
        
        return {
            'total_urls': total_urls,
            'successful': len(successful_results),
            'failed': len(failed_results),
            'total_size': total_size,
            'results': results,
            'success_rate': len(successful_results) / total_urls * 100
        }

class FileDownloader(AsyncDownloader):
    """文件下载器，支持保存到本地"""
    
    async def download_file(self, url: str, save_path: str) -> Dict[str, any]:
        """下载文件并保存到本地"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        'url': url,
                        'success': False,
                        'error': f'HTTP {response.status}'
                    }
                
                content = await response.read()
                
                # 确保目录存在
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # 保存文件
                with open(save_path, 'wb') as f:
                    f.write(content)
                
                file_size = len(content)
                print(f"💾 已保存: {save_path} ({file_size:,}字节)")
                
                return {
                    'url': url,
                    'save_path': save_path,
                    'file_size': file_size,
                    'success': True
                }
                
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }

# 测试URL列表
TEST_URLS = [
    'https://httpbin.org/delay/1',
    'https://jsonplaceholder.typicode.com/posts/1',
    'https://httpbin.org/delay/2',
    'https://jsonplaceholder.typicode.com/posts/2',
    'https://httpbin.org/user-agent',
    'https://jsonplaceholder.typicode.com/posts/3',
    'https://httpbin.org/headers',
    'https://jsonplaceholder.typicode.com/posts/4',
]

async def demo_basic_download():
    """基础下载演示"""
    print("🎯 基础下载演示")
    
    async with AsyncDownloader(max_concurrent=4) as downloader:
        start_time = time.time()
        
        results = await downloader.download_with_progress(TEST_URLS[:5])
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print("📊 下载统计")
        print(f"总耗时: {elapsed:.2f}秒")
        print(f"成功: {results['successful']}/{results['total_urls']}")
        print(f"失败: {results['failed']}/{results['total_urls']}")
        print(f"成功率: {results['success_rate']:.1f}%")
        print(f"总下载大小: {results['total_size']:,}字符")
        
        if results['failed'] > 0:
            print("\n❌ 失败的任务:")
            for result in results['results']:
                if not result['success']:
                    print(f"  {result['url']}: {result['error_message']}")

async def demo_file_download():
    """文件下载演示"""
    print("\n" + "="*60)
    print("🗂️ 文件下载演示")
    
    file_urls = [
        ('https://httpbin.org/robots.txt', 'downloads/robots.txt'),
        ('https://jsonplaceholder.typicode.com/posts', 'downloads/posts.json'),
    ]
    
    async with FileDownloader(max_concurrent=2) as downloader:
        start_time = time.time()
        
        tasks = [
            downloader.download_file(url, path)
            for url, path in file_urls
        ]
        
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 文件下载统计")
        print(f"总耗时: {elapsed:.2f}秒")
        
        for result in results:
            if result['success']:
                print(f"✅ {result['url']} → {result['save_path']}")
            else:
                print(f"❌ {result['url']}: {result['error']}")

async def demo_error_handling():
    """错误处理演示"""
    print("\n" + "="*60)
    print("🛡️ 错误处理演示")
    
    # 包含一些会失败的URL
    test_urls = [
        'https://httpbin.org/status/200',  # 成功
        'https://httpbin.org/status/404',  # 404错误
        'https://invalid-url-that-does-not-exist.com',  # 域名错误
        'https://httpbin.org/delay/10',  # 超时测试
        'https://httpbin.org/status/500',  # 服务器错误
    ]
    
    async with AsyncDownloader(max_concurrent=3, timeout=5) as downloader:
        results = await downloader.download_multiple(test_urls)
        
        print("\n📊 错误处理结果:")
        for result in results:
            if result['success']:
                print(f"✅ {result['url']}: 成功 ({result['status_code']})")
            else:
                print(f"❌ {result['url']}: {result['error_message']}")

async def demo_custom_urls():
    """自定义URL下载演示"""
    print("\n" + "="*60)
    print("🌐 自定义URL下载")
    
    # 用户可以修改这些URL
    custom_urls = [
        'https://api.github.com/users/octocat',
        'https://api.github.com/repos/microsoft/vscode',
        'https://httpbin.org/json',
        'https://httpbin.org/xml',
    ]
    
    async with AsyncDownloader(max_concurrent=2) as downloader:
        results = await downloader.download_with_progress(custom_urls)
        
        # 显示成功的内容预览
        for result in results['results']:
            if result['success'] and 'content_preview' in result:
                print(f"\n📄 {result['url']} 内容预览:")
                print(result['content_preview'])
                print("-" * 40)

async def main():
    """主函数"""
    print("🚀 异步下载器演示开始")
    
    # 创建下载目录
    os.makedirs('downloads', exist_ok=True)
    
    # 运行各种演示
    await demo_basic_download()
    await demo_file_download()
    await demo_error_handling()
    await demo_custom_urls()
    
    print("\n" + "="*60)
    print("✅ 所有演示完成！")
    print("📁 检查 downloads/ 目录查看下载的文件")

if __name__ == "__main__":
    asyncio.run(main())