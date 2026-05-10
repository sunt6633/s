#!/usr/bin/env python3
"""包装脚本用于运行stock-analyst脚本，解决Windows编码问题"""
import subprocess
import sys
import os

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 解析参数
if len(sys.argv) < 2:
    print("用法: python run_stock_analysis.py <股票代码>")
    print("示例: python run_stock_analysis.py 601318.SH")
    sys.exit(1)

stock_code = sys.argv[1]
script_path = os.path.join(os.path.dirname(__file__), 'fetch_all.py')

print(f"正在分析股票: {stock_code}")
print("-" * 50)

# 运行脚本
try:
    result = subprocess.run(
        [sys.executable, script_path, stock_code],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
except Exception as e:
    print(f"执行失败: {e}")
