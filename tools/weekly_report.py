# -*- coding: utf-8 -*-
"""量化分析周报生成脚本"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
import json

print('=' * 60)
print('  金融助手 - 量化分析周报')
print('  生成时间:', datetime.now().strftime('%Y-%m-%d %H:%M'))
print('=' * 60)

with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stocks = data['stock_pool']

print()
print('📊 股票池分析 ({0}只股票)'.format(len(stocks)))
print('-' * 60)

sorted_stocks = sorted(stocks, key=lambda x: x.get('total_score', 0), reverse=True)

print()
print('🏆 TOP 5 量化优选股:')
for i, s in enumerate(sorted_stocks[:5], 1):
    print('  {0}. {1}({2}) 评分:{3:.1f} 信号:{4}'.format(i, s['name'], s['code'], s['total_score'], s['tech']['signal']))
    print('     行业:{0} 现价:{1} 涨跌:{2}%'.format(s['sector'], s['price'], s['change_rate']))
    print('     技术面:' + s['tech']['detail'])
    print()

print('📈 板块分布:')
sectors = {}
for s in stocks:
    sec = s['sector']
    if sec not in sectors:
        sectors[sec] = {'count': 0, 'avg_score': 0}
    sectors[sec]['count'] += 1
    sectors[sec]['avg_score'] += s['total_score']

for sec, info in sorted(sectors.items(), key=lambda x: x[1]['avg_score'], reverse=True):
    print('  {0}: {1}只 平均评分:{2:.1f}'.format(sec, info['count'], info['avg_score']/info['count']))

print()
print('🎯 信号统计:')
signals = {}
for s in stocks:
    sig = s['tech']['signal']
    signals[sig] = signals.get(sig, 0) + 1

for sig, cnt in sorted(signals.items(), key=lambda x: x[1], reverse=True):
    print('  {0}: {1}只'.format(sig, cnt))

print()
print('=' * 60)
print('  建议关注板块: 白酒/电力/保险/半导体')
print('=' * 60)
