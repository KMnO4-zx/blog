#!/usr/bin/env python3
"""
Python异步基础概念示例
这个文件展示了async/await的基本用法
运行方法：python 01_basic_async.py
"""

import asyncio
import time

# 1. 最基本的异步函数
async def say_hello(name: str, delay: float = 1.0):
    """异步打招呼函数"""
    print(f"开始打招呼给 {name}")
    await asyncio.sleep(delay)  # 非阻塞等待
    print(f"你好，{name}！")
    return f"已完成对{name}的问候"

# 2. 顺序执行 vs 并发执行
async def sequential_example():
    """顺序执行的例子"""
    print("\n=== 顺序执行示例 ===")
    start_time = time.time()
    
    result1 = await say_hello("小明", 1)
    result2 = await say_hello("小红", 1)
    result3 = await say_hello("小刚", 1)
    
    elapsed = time.time() - start_time
    print(f"顺序执行耗时: {elapsed:.2f}秒")
    print(f"结果: {result1}, {result2}, {result3}")
    return elapsed

async def concurrent_example():
    """并发执行的例子"""
    print("\n=== 并发执行示例 ===")
    start_time = time.time()
    
    # 同时启动所有任务
    task1 = asyncio.create_task(say_hello("小明", 1))
    task2 = asyncio.create_task(say_hello("小红", 1))
    task3 = asyncio.create_task(say_hello("小刚", 1))
    
    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)
    
    elapsed = time.time() - start_time
    print(f"并发执行耗时: {elapsed:.2f}秒")
    print(f"结果: {results}")
    return elapsed

# 3. 异常处理
async def risky_operation(task_id: int):
    """可能失败的操作"""
    await asyncio.sleep(0.5)
    if task_id % 3 == 0:  # 每3个任务失败一个
        raise ValueError(f"任务{task_id}故意失败")
    return f"任务{task_id}成功"

async def exception_handling_example():
    """异常处理示例"""
    print("\n=== 异常处理示例 ===")
    
    tasks = [risky_operation(i) for i in range(1, 6)]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"任务{i}: 失败 - {result}")
        else:
            print(f"任务{i}: 成功 - {result}")

# 4. 超时控制
async def slow_operation():
    """慢操作"""
    await asyncio.sleep(3)
    return "操作完成"

async def timeout_example():
    """超时处理示例"""
    print("\n=== 超时处理示例 ===")
    
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
        print(f"操作成功: {result}")
    except asyncio.TimeoutError:
        print("操作超时！")

# 5. 任务取消
async def cancellable_task():
    """可取消的任务"""
    try:
        for i in range(10):
            print(f"工作中... {i}")
            await asyncio.sleep(0.5)
        return "任务完成"
    except asyncio.CancelledError:
        print("任务被取消")
        raise

async def cancellation_example():
    """任务取消示例"""
    print("\n=== 任务取消示例 ===")
    
    task = asyncio.create_task(cancellable_task())
    
    # 等待1秒后取消任务
    await asyncio.sleep(1)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        print("任务已成功取消")

def sync_vs_async_comparison():
    """同步vs异步对比"""
    print("\n=== 同步vs异步时间对比 ===")
    
    # 同步方式
    def sync_delay(duration):
        time.sleep(duration)
        return f"等待了{duration}秒"
    
    start = time.time()
    results = [sync_delay(1) for _ in range(3)]
    sync_time = time.time() - start
    print(f"同步执行3个1秒任务: {sync_time:.2f}秒")
    
    # 异步方式
    async def async_main():
        start = time.time()
        results = await asyncio.gather(*[say_hello(f"任务{i}", 1) for i in range(1, 4)])
        async_time = time.time() - start
        print(f"异步执行3个1秒任务: {async_time:.2f}秒")
        print(f"异步效率提升: {sync_time/async_time:.1f}x")
    
    asyncio.run(async_main())

async def main():
    """主函数 - 运行所有示例"""
    print("🚀 Python异步基础概念示例开始")
    print("=" * 50)
    
    # 运行基础示例
    await sequential_example()
    await concurrent_example()
    
    # 运行高级示例
    await exception_handling_example()
    await timeout_example()
    await cancellation_example()
    
    # 同步vs异步对比
    sync_vs_async_comparison()
    
    print("\n" + "=" * 50)
    print("✅ 所有示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())