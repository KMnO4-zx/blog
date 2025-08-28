#!/usr/bin/env python3
"""
快速开始脚本
一键运行所有示例
运行方法：python quick_start.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

async def install_requirements():
    """安装依赖"""
    print("📦 检查并安装依赖...")
    try:
        import aiohttp
        import requests
        print("✅ 依赖已安装")
    except ImportError:
        print("🔄 安装依赖...")
        os.system("pip install -r requirements.txt")
        print("✅ 依赖安装完成")

async def run_demo(demo_name: str, demo_func):
    """运行演示"""
    print(f"\n🎯 运行 {demo_name}...")
    try:
        await demo_func()
        print(f"✅ {demo_name} 完成")
    except Exception as e:
        print(f"❌ {demo_name} 失败: {e}")

async def basic_demo():
    """基础演示"""
    from examples._01_basic_async import main as basic_main
    await basic_main()

async def concurrency_demo():
    """并发演示"""
    from examples._02_concurrency_examples import main as concurrency_main
    await concurrency_main()

async def downloader_demo():
    """下载器演示"""
    from examples.async_downloader import demo_basic_download
    await demo_basic_download()

async def task_manager_demo():
    """任务管理器演示"""
    from examples.task_manager import main as task_main
    await task_main()

async def main():
    """主函数"""
    print("🚀 Python异步编程快速开始")
    print("=" * 50)
    
    # 安装依赖
    await install_requirements()
    
    # 运行演示
    demos = [
        ("基础概念", basic_demo),
        ("并发控制", concurrency_demo),
        ("异步下载器", downloader_demo),
        ("任务管理器", task_manager_demo),
    ]
    
    for demo_name, demo_func in demos:
        await run_demo(demo_name, demo_func)
    
    print("\n" + "=" * 50)
    print("🎉 快速体验完成！")
    print("📚 查看 python-async-tutorial.md 获取完整教程")

if __name__ == "__main__":
    asyncio.run(main())