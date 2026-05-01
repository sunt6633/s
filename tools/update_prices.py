# -*- coding: utf-8 -*-
"""更新持仓价格到最新"""
import sys, json
sys.path.insert(0, 'D:/for workbuddy/finance_bot')

# 获取最新价格
import qveris_api_manager
qveris_api_manager._current_index = 1
import trading_engine_v9
trading_engine_v9._cached_search_id = None

from trading_engine_v9 import get_realtime_price

# 读取当前持仓
with open('D:/for workbuddy/finance_bot/portfolio.json', 'r', encoding='utf-8') as f:
    portfolio = json.load(f)

print('=== 当前持仓 ===')
for pos in portfolio['positions']:
    code = pos['code']
    current_price = get_realtime_price(code)
    profit = (current_price - pos['avg_cost']) * pos['shares']
    profit_rate = (current_price / pos['avg_cost'] - 1) * 100

    print(f"{pos['name']}({code})")
    print(f"  成本价: {pos['avg_cost']}元 -> 现价: {current_price}元")
    print(f"  持股: {pos['shares']}股")
    print(f"  盈亏: {profit:.0f}元 ({profit_rate:.2f}%)")
    print()

    # 更新价格
    pos['current_price'] = current_price

# 计算总资产
total_value = portfolio['portfolio']['current_capital']
for pos in portfolio['positions']:
    total_value += pos['current_price'] * pos['shares']

portfolio['portfolio']['total_value'] = total_value
portfolio['portfolio']['total_profit'] = total_value - portfolio['portfolio']['initial_capital']
portfolio['portfolio']['total_profit_rate'] = portfolio['portfolio']['total_profit'] / portfolio['portfolio']['initial_capital'] * 100

print("=== 账户总览 ===")
print(f"总资产: {total_value:.2f}元")
print(f"总收益: {portfolio['portfolio']['total_profit']:.2f}元 ({portfolio['portfolio']['total_profit_rate']:.2f}%)")
print(f"现金: {portfolio['portfolio']['current_capital']:.2f}元")

# 保存更新
with open('D:/for workbuddy/finance_bot/portfolio.json', 'w', encoding='utf-8') as f:
    json.dump(portfolio, f, indent=2, ensure_ascii=False)
print("\n已更新持仓价格！")
