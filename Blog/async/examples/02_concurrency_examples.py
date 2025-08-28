#!/usr/bin/env python3
"""
Python并发执行示例
展示如何设置和控制多并发任务
运行方法：python 02_concurrency_examples.py
"""

import asyncio
import random
import time
from typing import List, Dict

# 1. 信号量控制并发数
class SemaphoreExample:
    """使用信号量限制并发数的示例"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
    
    async def worker(self, worker_id: int, semaphore: asyncio.Semaphore, work_time: float):
        """工作协程"""
        async with semaphore:
            print(f"🚀 工人{worker_id}开始工作（最大并发数：{self.max_concurrent}）")
            await asyncio.sleep(work_time)
            print(f"✅ 工人{worker_id}完成工作（耗时：{work_time}秒）")
            return f"工人{worker_id}完成任务"
    
    async def run_with_semaphore(self, num_workers: int = 10):
        """使用信号量运行多个任务"""
        print(f"\n=== 信号量控制并发示例 ===")
        print(f"总任务数：{num_workers}，最大并发数：{self.max_concurrent}")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 创建任务，每个任务耗时随机1-3秒
        tasks = [
            self.worker(i, semaphore, random.uniform(1, 3))
            for i in range(1, num_workers + 1)
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        print(f"总耗时：{total_time:.2f}秒")
        print(f"理论最少时间：{max(t.get_coro().__name__ == 'worker' for t in tasks)}秒")
        return results

# 2. 任务队列和生产者消费者模式
class TaskQueueExample:
    """任务队列示例"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.results = []
    
    async def producer(self, num_tasks: int):
        """生产者：产生任务"""
        print(f"\n=== 生产者消费者模式 ===")
        print(f"生产者开始生成{num_tasks}个任务")
        
        for i in range(num_tasks):
            task = {
                'id': i + 1,
                'work_time': random.uniform(0.5, 2.0),
                'difficulty': random.choice(['简单', '中等', '困难'])
            }
            await self.task_queue.put(task)
            print(f"📥 生产了任务{task['id']}（{task['difficulty']}，{task['work_time']:.1f}秒）")
        
        # 发送结束信号
        for _ in range(self.max_workers):
            await self.task_queue.put(None)
    
    async def consumer(self, worker_id: int):
        """消费者：处理任务"""
        while True:
            task = await self.task_queue.get()
            
            if task is None:  # 结束信号
                print(f"🏁 工人{worker_id}收到结束信号")
                break
            
            print(f"👷 工人{worker_id}开始处理任务{task['id']}（{task['difficulty']}）")
            await asyncio.sleep(task['work_time'])
            
            result = {
                'task_id': task['id'],
                'worker_id': worker_id,
                'processing_time': task['work_time'],
                'status': 'completed'
            }
            
            self.results.append(result)
            print(f"✅ 工人{worker_id}完成任务{task['id']}")
            
            self.task_queue.task_done()
    
    async def run_queue_example(self, num_tasks: int = 6):
        """运行队列示例"""
        start_time = time.time()
        
        # 创建生产者和消费者任务
        producer_task = asyncio.create_task(self.producer(num_tasks))
        consumer_tasks = [
            asyncio.create_task(self.consumer(i))
            for i in range(1, self.max_workers + 1)
        ]
        
        # 等待所有任务完成
        await producer_task
        await asyncio.gather(*consumer_tasks)
        
        total_time = time.time() - start_time
        
        print(f"\n=== 队列处理统计 ===")
        print(f"总任务数：{len(self.results)}")
        print(f"工人数量：{self.max_workers}")
        print(f"总耗时：{total_time:.2f}秒")
        
        return self.results

# 3. 批量任务处理
class BatchProcessor:
    """批量任务处理器"""
    
    def __init__(self, batch_size: int = 3, delay_between_batches: float = 0.5):
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
    
    async def process_item(self, item_id: int, processing_time: float):
        """处理单个项目"""
        print(f"🔄 处理项目{item_id}（预计{processing_time}秒）")
        await asyncio.sleep(processing_time)
        return f"项目{item_id}处理完成"
    
    async def process_in_batches(self, items: List[Dict]):
        """分批处理项目"""
        print(f"\n=== 批量处理示例 ===")
        print(f"总项目数：{len(items)}，批次大小：{self.batch_size}")
        
        start_time = time.time()
        all_results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            print(f"\n📦 处理第{(i // self.batch_size) + 1}批，共{len(batch)}个项目")
            
            # 处理当前批次
            batch_tasks = [
                self.process_item(item['id'], item['time'])
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)
            
            # 批次间延迟
            if i + self.batch_size < len(items):
                print(f"⏸️ 批次间休息{self.delay_between_batches}秒...")
                await asyncio.sleep(self.delay_between_batches)
        
        total_time = time.time() - start_time
        print(f"\n=== 批量处理完成 ===")
        print(f"总耗时：{total_time:.2f}秒")
        print(f"项目结果：{all_results}")
        
        return all_results

# 4. 动态任务管理
class DynamicTaskManager:
    """动态任务管理器"""
    
    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self.running_tasks = set()
    
    async def dynamic_task(self, task_id: int, base_time: float):
        """动态任务，根据ID调整执行时间"""
        work_time = base_time + (task_id * 0.2)
        await asyncio.sleep(work_time)
        return f"任务{task_id}完成（{work_time:.1f}秒）"
    
    async def add_task_dynamically(self, task_id: int, semaphore: asyncio.Semaphore):
        """动态添加任务"""
        async with semaphore:
            task = asyncio.create_task(self.dynamic_task(task_id, 1.0))
            self.running_tasks.add(task)
            
            try:
                result = await task
                print(f"🎯 动态任务{task_id}: {result}")
                return result
            finally:
                self.running_tasks.discard(task)
    
    async def monitor_tasks(self):
        """监控任务状态"""
        while self.running_tasks or not hasattr(self, 'monitor_done'):
            active_count = len(self.running_tasks)
            if active_count > 0:
                print(f"📊 当前活动任务数：{active_count}")
            await asyncio.sleep(0.5)
    
    async def run_dynamic_example(self, total_tasks: int = 8):
        """运行动态任务示例"""
        print(f"\n=== 动态任务管理示例 ===")
        print(f"总任务数：{total_tasks}，最大并发：{self.max_concurrent}")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 启动监控任务
        monitor_task = asyncio.create_task(self.monitor_tasks())
        
        # 动态创建任务
        tasks = [
            self.add_task_dynamically(i, semaphore)
            for i in range(1, total_tasks + 1)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 停止监控
        self.monitor_done = True
        await monitor_task
        
        total_time = time.time() - start_time
        print(f"\n=== 动态任务完成 ===")
        print(f"总耗时：{total_time:.2f}秒")
        
        return results

# 5. 优先级任务处理
class PriorityTaskProcessor:
    """优先级任务处理器"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    async def priority_task(self, task_id: int, priority: int, work_time: float):
        """优先级任务"""
        await asyncio.sleep(work_time)
        return {
            'task_id': task_id,
            'priority': priority,
            'work_time': work_time,
            'completed': True
        }
    
    async def process_by_priority(self, tasks: List[Dict]):
        """按优先级处理任务"""
        print(f"\n=== 优先级任务处理 ===")
        
        # 按优先级排序（数字越小优先级越高）
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'])
        
        start_time = time.time()
        results = []
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_priority(task_info):
            async with semaphore:
                result = await self.priority_task(
                    task_info['id'],
                    task_info['priority'],
                    task_info['time']
                )
                print(f"🏆 优先级{task_info['priority']}的任务{task_info['id']}完成")
                return result
        
        # 执行所有任务
        process_tasks = [process_with_priority(task) for task in sorted_tasks]
        results = await asyncio.gather(*process_tasks)
        
        total_time = time.time() - start_time
        
        print(f"\n=== 优先级处理完成 ===")
        print(f"总耗时：{total_time:.2f}秒")
        print("按优先级排序的结果：")
        for result in sorted(results, key=lambda x: x['priority']):
            print(f"  优先级{result['priority']} - 任务{result['task_id']}")
        
        return results

async def main():
    """运行所有并发示例"""
    print("🚀 Python并发执行示例")
    print("=" * 60)
    
    # 1. 信号量示例
    semaphore_example = SemaphoreExample(max_concurrent=3)
    await semaphore_example.run_with_semaphore(num_workers=8)
    
    # 2. 队列示例
    queue_example = TaskQueueExample(max_workers=3)
    await queue_example.run_queue_example(num_tasks=6)
    
    # 3. 批量处理示例
    batch_processor = BatchProcessor(batch_size=3, delay_between_batches=1.0)
    items = [
        {'id': i, 'time': random.uniform(0.5, 1.5)}
        for i in range(1, 8)
    ]
    await batch_processor.process_in_batches(items)
    
    # 4. 动态任务管理
    dynamic_manager = DynamicTaskManager(max_concurrent=4)
    await dynamic_manager.run_dynamic_example(total_tasks=8)
    
    # 5. 优先级任务处理
    priority_processor = PriorityTaskProcessor(max_workers=2)
    priority_tasks = [
        {'id': 1, 'priority': 3, 'time': 1.0},
        {'id': 2, 'priority': 1, 'time': 2.0},  # 最高优先级
        {'id': 3, 'priority': 2, 'time': 1.5},
        {'id': 4, 'priority': 3, 'time': 0.8},
    ]
    await priority_processor.process_by_priority(priority_tasks)
    
    print("\n" + "=" * 60)
    print("✅ 所有并发示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())