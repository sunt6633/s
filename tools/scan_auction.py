# -*- coding: utf-8 -*-
"""竞价阶段强势股扫描"""
import json
from datetime import datetime

# 设置UTF-8输出
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 从portfolio.json读取昨日行情数据
with open(r'D:\for workbuddy\finance_bot\portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=' * 60)
print('  [竞价阶段强势股扫描]')
print(f'  时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print(f'  阶段: 集合竞价 (9:15-9:25)')
print('=' * 60)
print()

# 按涨幅排序
stocks_data = data.get('stock_pool', [])
stocks_data.sort(key=lambda x: x.get('change_rate', 0), reverse=True)

print('[强势股排名 - 按昨日涨幅]')
print('-' * 55)

for i, stock in enumerate(stocks_data[:10], 1):
    name = stock.get('name', '')
    code = stock.get('code', '')
    change = stock.get('change_rate', 0)
    price = stock.get('price', 0)
    volume_ratio = stock.get('turnover', 0)
    score = stock.get('scores', {}).get('composite', 0)
    
    # 判断竞价强弱
    if change > 3:
        status = '[超级强势]'
        emoji = '*'
    elif change > 1.5:
        status = '[强势]'
        emoji = '+'
    elif change > 0.5:
        status = '[平稳偏强]'
        emoji = '~'
    elif change > 0:
        status = '[平稳]'
        emoji = '-'
    elif change > -2:
        status = '[偏弱]'
        emoji = 'v'
    else:
        status = '[弱势]'
        emoji = 'x'
    
    arrow = '+' if change >= 0 else ''
    print(f'{emoji} {i:2d}. {name}({code})')
    print(f'    现价: {price:.2f} | 涨幅: {arrow}{change}% | 换手: {volume_ratio}%')
    print(f'    综合评分: {score:.1f}分 | {status}')
    print()

print('-' * 55)
print()

# 强势股推荐
print('[今日竞价重点关注]')
print()

# 涨幅>2%的强势股
strong_stocks = [s for s in stocks_data if s.get('change_rate', 0) > 2]
if strong_stocks:
    print('[A] 超级强势股（涨幅>2%）：')
    for s in strong_stocks:
        print(f'   - {s.get("name")}({s.get("code")}) +{s.get("change_rate"):.2f}%')
    print()

# 量能放大股
active_stocks = [s for s in stocks_data if s.get('turnover', 0) > 5]
if active_stocks:
    print('[B] 活跃股（换手率>5%）：')
    for s in active_stocks[:5]:
        print(f'   - {s.get("name")}({s.get("code")}) 换手{s.get("turnover")}%')
    print()

# 综合评分Top5
top5 = sorted(stocks_data, key=lambda x: x.get('scores', {}).get('composite', 0), reverse=True)[:5]
print('[C] 综合评分Top5：')
for s in top5:
    print(f'   - {s.get("name")}({s.get("code")}) {s.get("scores", {}).get("composite", 0):.1f}分')

print()
print('=' * 60)
print('[提示] 以上为昨日收盘数据，竞价阶段请以实时数据为准')
print('=' * 60)
