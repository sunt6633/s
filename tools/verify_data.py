#!/usr/bin/env python3
"""验证修复后的数据"""
import json

with open('D:/for workbuddy/finance_bot/portfolio.json', 'r', encoding='utf-8') as f:
    portfolio = json.load(f)

with open('D:/for workbuddy/finance_bot/trades.json', 'r', encoding='utf-8') as f:
    trades = json.load(f)

p = portfolio['portfolio']
print('=== 验证数据 ===')
print('总资产 (total_assets):', round(p.get('total_assets', 0), 2))
print('累计盈利 (total_profit):', round(p.get('total_profit', 0), 2))
print('盈利率:', round(p.get('total_profit_rate', 0), 2), '%')
print('更新时间:', p.get('last_updated', '缺失'))

print()
print('=== 持仓 ===')
for pos in portfolio.get('positions', []):
    print(f"  {pos['name']}({pos['code']}): {pos['shares']}股 x {pos['current_price']:.2f} = {pos['market_value']:,.2f}元")

print()
print('=== trades.json ===')
print('可用现金 (cash):', trades['cash'])
print('总卖出:', trades['total_sell'])

# 计算验证
cash = trades['cash']
market_value = sum(pos.get('market_value', 0) for pos in portfolio.get('positions', []))
total = cash + market_value
print()
print('=== 计算验证 ===')
print('现金:', round(cash, 2), '+ 市值:', round(market_value, 2), '= 总资产:', round(total, 2))
print('盈利:', round(total - 100000, 2), '(+' + str(round((total-100000)/100000*100, 2)) + '%)')
