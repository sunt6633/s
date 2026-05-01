#!/usr/bin/env python3
"""安装stock-analyst依赖"""
import subprocess
import sys

packages = [
    'akshare', 'yfinance', 'pandas', 'numpy', 
    'matplotlib', 'pillow', 'markdown', 'requests',
    'fpdf2', 'python-docx', 'pymupdf'
]

print('Installing packages...')
for pkg in packages:
    try:
        print(f'  Installing {pkg}...', end=' ')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
        print('OK')
    except Exception as e:
        print(f'FAILED: {e}')

print()
print('All packages installed!')
