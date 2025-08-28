#!/usr/bin/env python3
"""
性能对比测试
比较同步、多线程、异步的性能差异
运行方法：python performance_test.py
"""

import asyncio
import aiohttp
import requests
import time
import concurrent.futures
import multiprocessing
from typing import List, Dict, Callable
import statistics
import json

# 测试URL列表 - 使用稳定的测试URL
TEST_URLS = [
    'https://httpbin.org/delay/1',
    'https://jsonplaceholder.typicode.com/posts/1',
    'https://httpbin.org/delay/2',
    'https://jsonplaceholder.typicode.com/posts/2',
    'https://httpbin.org/user-agent',
    'https://jsonplaceholder.typicode.com/posts/3',
    'https://httpbin.org/headers',
    'https://jsonplaceholder.typicode.com/posts/4',
    'https://httpbin.org/delay/1',
    'https://jsonplaceholder.typicode.com/posts/5',
]

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results = {}
    
    def sync_download(self, urls: List[str]) -> List[str]:
        """同步下载"""
        results = []
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                results.append(f"{url}: {len(response.text)} chars")
            except Exception as e:
                results.append(f"{url}: ERROR - {e}")
        return results
    
    def thread_download(self, urls: List[str], max_workers: int = 5) -> List[str]:
        """多线程下载"""
        def download_one(url):
            try:
                response = requests.get(url, timeout=10)
                return f"{url}: {len(response.text)} chars"
            except Exception as e:
                return f"{url}: ERROR - {e}"
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(download_one, urls))
        return results
    
    def process_download(self, urls: List[str]) -> List[str]:
        """多进程下载"""
        def download_one(url):
            try:
                response = requests.get(url, timeout=10)
                return f"{url}: {len(response.text)} chars"
            except Exception as e:
                return f"{url}: ERROR - {e}"
        
        with multiprocessing.Pool(processes=min(len(urls), multiprocessing.cpu_count())) as pool:
            results = pool.map(download_one, urls)
        return results
    
    async def async_download(self, urls: List[str], max_concurrent: int = 5) -> List[str]:
        """异步下载"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        ) as session:
            
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_one(url):
                async with semaphore:
                    try:
                        async with session.get(url) as response:
                            content = await response.text()
                            return f"{url}: {len(content)} chars"
                    except Exception as e:
                        return f"{url}: ERROR - {e}"
            
            results = await asyncio.gather(*[download_one(url) for url in urls])
            return results
    
    def measure_performance(self, func: Callable, *args, **kwargs) -> Dict[str, float]:
        """测量函数性能"""
        times = []
        
        # 预热
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
        except:
            pass
        
        # 多次测试取平均值
        num_runs = 3
        for i in range(num_runs):
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = asyncio.run(func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                times.append(elapsed)
                print(f"  运行 {i+1}: {elapsed:.2f}秒")
                
            except Exception as e:
                print(f"  运行 {i+1} 失败: {e}")
                times.append(float('inf'))
        
        if times and all(t != float('inf') for t in times):
            return {
                'min_time': min(times),
                'max_time': max(times),
                'avg_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0
            }
        else:
            return {'error': '测试失败'}
    
    def run_comparison(self, urls: List[str]) -> Dict[str, Dict]:
        """运行完整性能对比"""
        print("🚀 性能对比测试开始")
        print("=" * 60)
        print(f"测试URL数量: {len(urls)}")
        print(f"测试URL: {urls[:3]}...")
        print("=" * 60)
        
        test_cases = {
            '同步下载': lambda: self.sync_download(urls),
            '多线程(3 workers)': lambda: self.thread_download(urls, 3),
            '多线程(5 workers)': lambda: self.thread_download(urls, 5),
            '多线程(10 workers)': lambda: self.thread_download(urls, 10),
            '多进程': lambda: self.process_download(urls),
            '异步(3并发)': lambda: self.async_download(urls, 3),
            '异步(5并发)': lambda: self.async_download(urls, 5),
            '异步(10并发)': lambda: self.async_download(urls, 10),
        }
        
        self.results = {}
        
        for test_name, test_func in test_cases.items():
            print(f"\n📊 测试: {test_name}")
            print("-" * 40)
            
            perf_result = self.measure_performance(test_func)
            self.results[test_name] = perf_result
            
            if 'error' not in perf_result:
                print(f"  平均: {perf_result['avg_time']:.2f}秒")
                print(f"  最快: {perf_result['min_time']:.2f}秒")
                print(f"  最慢: {perf_result['max_time']:.2f}秒")
                print(f"  标准差: {perf_result['std_dev']:.2f}秒")
            else:
                print(f"  错误: {perf_result['error']}")
        
        return self.results
    
    def generate_report(self) -> str:
        """生成性能报告"""
        if not self.results:
            return "没有测试结果"
        
        # 过滤掉失败的测试
        valid_results = {k: v for k, v in self.results.items() 
                        if 'error' not in v}
        
        if not valid_results:
            return "所有测试都失败了"
        
        # 按平均时间排序
        sorted_results = sorted(valid_results.items(), 
                              key=lambda x: x[1]['avg_time'])
        
        # 计算效率倍数
        sync_time = valid_results.get('同步下载', {}).get('avg_time', 1)
        
        report = []
        report.append("\n" + "=" * 60)
        report.append("📈 性能测试报告")
        report.append("=" * 60)
        
        for rank, (test_name, result) in enumerate(sorted_results, 1):
            speedup = sync_time / result['avg_time'] if sync_time > 0 else 1
            report.append(f"{rank}. {test_name}")
            report.append(f"   平均时间: {result['avg_time']:.2f}秒")
            report.append(f"   相对同步: {speedup:.1f}x 更快")
            report.append("-" * 40)
        
        # 找出最佳配置
        best_method = sorted_results[0]
        report.append(f"\n🏆 最佳方法: {best_method[0]}")
        report.append(f"   比同步快 {sync_time/best_method[1]["avg_time"]:.1f} 倍")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = 'performance_results.json'):
        """保存结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存到: {filename}")

class ScalabilityTester:
    """可扩展性测试器"""
    
    def __init__(self):
        self.scalability_results = {}
    
    async def test_concurrency_levels(self, base_urls: List[str]) -> Dict[int, float]:
        """测试不同并发级别的性能"""
        print("\n🔍 并发级别可扩展性测试")
        print("-" * 40)
        
        levels = [1, 2, 3, 5, 8, 10, 15, 20]
        results = {}
        
        for level in levels:
            print(f"测试并发级别: {level}")
            
            async def test_level():
                start_time = time.time()
                await AsyncDownloader().async_download(base_urls, level)
                return time.time() - start_time
            
            elapsed = await test_level()
            results[level] = elapsed
            print(f"  耗时: {elapsed:.2f}秒")
        
        return results
    
    def analyze_optimal_concurrency(self, results: Dict[int, float]) -> int:
        """分析最佳并发数"""
        if not results:
            return 5  # 默认值
        
        # 找出性能提升开始递减的点
        sorted_levels = sorted(results.items())
        
        best_level = 1
        best_efficiency = float('inf')
        
        for level, time_taken in sorted_levels:
            efficiency = time_taken / level  # 每个任务的平均时间
            if efficiency < best_efficiency:
                best_efficiency = efficiency
                best_level = level
        
        return best_level

class IOTaskSimulator:
    """I/O任务模拟器"""
    
    @staticmethod
    async def simulate_io_task(task_id: int, delay: float = 1.0):
        """模拟I/O密集型任务"""
        await asyncio.sleep(delay + random.uniform(-0.2, 0.2))
        return f"任务{task_id}完成"
    
    @staticmethod
    def simulate_cpu_task(task_id: int, iterations: int = 1000000):
        """模拟CPU密集型任务"""
        result = sum(i * i for i in range(iterations))
        return f"任务{task_id}完成，结果: {result}"

async def run_io_vs_cpu_comparison():
    """运行I/O vs CPU密集型任务对比"""
    print("\n⚡ I/O vs CPU密集型任务对比")
    print("-" * 40)
    
    # I/O密集型测试
    io_tasks = [IOTaskSimulator.simulate_io_task(i, 0.5) for i in range(10)]
    start_time = time.time()
    io_results = await asyncio.gather(*io_tasks)
    io_time = time.time() - start_time
    
    print(f"异步I/O任务: {io_time:.2f}秒 (10个任务)")
    
    # CPU密集型测试 - 多进程
    start_time = time.time()
    with multiprocessing.Pool(processes=4) as pool:
        cpu_results = pool.map(IOTaskSimulator.simulate_cpu_task, range(10))
    cpu_time = time.time() - start_time
    
    print(f"多进程CPU任务: {cpu_time:.2f}秒 (10个任务)")
    print(f"I/O任务效率提升: {cpu_time/io_time:.1f}x")

async def main():
    """主函数"""
    print("🚀 Python异步性能测试套件")
    print("=" * 60)
    
    # 基本性能对比
    tester = PerformanceTester()
    results = tester.run_comparison(TEST_URLS)
    
    # 显示报告
    report = tester.generate_report()
    print(report)
    
    # 保存结果
    tester.save_results()
    
    # 可扩展性测试
    scalability_tester = ScalabilityTester()
    scalability_results = await scalability_tester.test_concurrency_levels(TEST_URLS[:5])
    
    optimal = scalability_tester.analyze_optimal_concurrency(scalability_results)
    print(f"\n🎯 推荐并发数: {optimal}")
    
    # I/O vs CPU对比
    await run_io_vs_cpu_comparison()
    
    print("\n" + "=" * 60)
    print("✅ 性能测试完成！")
    print("📊 检查 performance_results.json 查看详细结果")

if __name__ == "__main__":
    asyncio.run(main())