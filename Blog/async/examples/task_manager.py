#!/usr/bin/env python3
"""
并发任务管理器 - 实战项目2
支持任务队列、进度跟踪、错误处理
运行方法：python task_manager.py
"""

import asyncio
import random
import time
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: str = None
    start_time: float = None
    end_time: float = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'duration': self.duration,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

class ConcurrentTaskManager:
    """并发任务管理器"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.tasks: Dict[str, Dict] = {}
        self.results: List[TaskResult] = []
        self.semaphore = asyncio.Semaphore(max_workers)
        self.running_tasks = set()
    
    def add_task(self, task_id: str, coro_func: Callable, *args, **kwargs):
        """添加任务到队列"""
        self.tasks[task_id] = {
            'coro_func': coro_func,
            'args': args,
            'kwargs': kwargs,
            'priority': kwargs.pop('priority', 0),
            'retry_count': kwargs.pop('retry_count', 0)
        }
    
    async def execute_single_task(self, task_id: str) -> TaskResult:
        """执行单个任务"""
        async with self.semaphore:
            task_info = self.tasks[task_id]
            coro_func = task_info['coro_func']
            args = task_info['args']
            kwargs = task_info['kwargs']
            max_retries = task_info['retry_count']
            
            result = TaskResult(task_id=task_id, status=TaskStatus.RUNNING)
            result.start_time = time.time()
            
            # 重试机制
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        print(f"🔄 任务{task_id}重试第{attempt}次")
                    
                    task_result = await coro_func(*args, **kwargs)
                    
                    result.status = TaskStatus.COMPLETED
                    result.result = task_result
                    result.end_time = time.time()
                    
                    print(f"✅ 任务{task_id}完成（耗时：{result.duration:.2f}s）")
                    break
                    
                except asyncio.CancelledError:
                    result.status = TaskStatus.CANCELLED
                    result.error = "任务被取消"
                    result.end_time = time.time()
                    print(f"🛑 任务{task_id}被取消")
                    break
                    
                except Exception as e:
                    if attempt == max_retries:
                        result.status = TaskStatus.FAILED
                        result.error = str(e)
                        result.end_time = time.time()
                        print(f"❌ 任务{task_id}失败：{e}")
                    else:
                        await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避
            
            return result
    
    async def run_all(self) -> List[TaskResult]:
        """运行所有任务"""
        if not self.tasks:
            print("没有任务需要执行")
            return []
        
        print(f"🚀 开始执行 {len(self.tasks)} 个任务")
        print(f"最大并发数: {self.max_workers}")
        print("-" * 60)
        
        start_time = time.time()
        
        # 按优先级排序
        sorted_tasks = sorted(self.tasks.items(), 
                            key=lambda x: x[1]['priority'], reverse=True)
        
        # 创建所有任务
        task_coroutines = [
            self.execute_single_task(task_id)
            for task_id, _ in sorted_tasks
        ]
        
        # 并发执行所有任务
        self.results = await asyncio.gather(*task_coroutines)
        
        total_time = time.time() - start_time
        
        # 打印统计信息
        self.print_statistics(total_time)
        
        return self.results
    
    async def run_with_progress(self) -> List[TaskResult]:
        """运行所有任务并显示进度"""
        if not self.tasks:
            print("没有任务需要执行")
            return []
        
        total_tasks = len(self.tasks)
        completed = 0
        failed = 0
        
        print(f"🎯 任务进度跟踪")
        print(f"总任务数: {total_tasks}")
        print("-" * 60)
        
        start_time = time.time()
        results = []
        
        # 按优先级排序
        sorted_tasks = sorted(self.tasks.items(), 
                            key=lambda x: x[1]['priority'], reverse=True)
        
        # 逐个执行任务（使用信号量控制并发）
        for task_id, _ in sorted_tasks:
            result = await self.execute_single_task(task_id)
            results.append(result)
            
            if result.status == TaskStatus.COMPLETED:
                completed += 1
            else:
                failed += 1
            
            # 显示进度
            progress = (completed + failed) / total_tasks * 100
            print(f"📊 进度: {progress:.1f}% ({completed + failed}/{total_tasks})")
        
        total_time = time.time() - start_time
        
        self.results = results
        self.print_statistics(total_time)
        
        return results
    
    def print_statistics(self, total_time: float):
        """打印执行统计"""
        successful = [r for r in self.results if r.status == TaskStatus.COMPLETED]
        failed = [r for r in self.results if r.status == TaskStatus.FAILED]
        cancelled = [r for r in self.results if r.status == TaskStatus.CANCELLED]
        
        print("\n" + "=" * 60)
        print("📊 任务执行统计")
        print("-" * 40)
        print(f"总任务数: {len(self.results)}")
        print(f"成功: {len(successful)}")
        print(f"失败: {len(failed)}")
        print(f"取消: {len(cancelled)}")
        print(f"总耗时: {total_time:.2f}秒")
        
        if successful:
            avg_duration = sum(r.duration for r in successful) / len(successful)
            max_duration = max(r.duration for r in successful)
            min_duration = min(r.duration for r in successful)
            
            print(f"平均任务耗时: {avg_duration:.2f}秒")
            print(f"最长任务耗时: {max_duration:.2f}秒")
            print(f"最短任务耗时: {min_duration:.2f}秒")
        
        if failed:
            print(f"失败率: {len(failed)/len(self.results)*100:.1f}%")
    
    def save_results(self, filename: str = 'task_results.json'):
        """保存结果到文件"""
        results_dict = [result.to_dict() for result in self.results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存到: {filename}")

# 示例任务函数
class DemoTasks:
    """演示任务集合"""
    
    @staticmethod
    async def simulate_work(task_id: str, base_time: float = 1.0, fail_rate: float = 0.1):
        """模拟工作任务"""
        work_time = base_time + random.uniform(-0.5, 0.5)
        work_time = max(0.5, work_time)
        
        await asyncio.sleep(work_time)
        
        # 随机失败
        if random.random() < fail_rate:
            raise ValueError(f"任务{task_id}随机失败")
        
        return f"任务{task_id}完成，处理了{work_time:.2f}秒的工作"
    
    @staticmethod
    async def fetch_data(task_id: str, url: str):
        """模拟网络请求"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return f"从{url}获取数据成功（任务{task_id}）"
    
    @staticmethod
    async def cpu_intensive_task(task_id: str, iterations: int = 1000000):
        """CPU密集型任务（适合演示，不适合真正的异步）"""
        # 注意：真正的CPU密集型任务应该用进程池
        await asyncio.sleep(0.1)  # 模拟一些I/O
        
        # 少量CPU工作
        result = sum(i * i for i in range(iterations))
        return f"任务{task_id}计算完成，结果：{result}