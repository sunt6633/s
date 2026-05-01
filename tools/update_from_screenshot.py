"""
根据截图更新持仓实时价格
"""
import json
from datetime import datetime

# 读取当前持仓
with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 根据截图更新最新价格
prices = {
    '000063': 35.38,  # 中兴通讯
    '601318': 57.79,  # 中国平安
    '601166': 18.41,  # 兴业银行
}

print('=== 更新持仓数据 ===')
total_profit = 0

for pos in data['positions']:
    code = pos['code']
    if code in prices:
        old_price = pos.get('current_price', 0)
        pos['current_price'] = prices[code]
        pos['current_price_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 重新计算盈亏
        market_value = prices[code] * pos['shares']
        cost = pos['avg_cost'] * pos['shares']
        pos['profit'] = market_value - cost
        pos['profit_rate'] = (pos['profit'] / cost) * 100
        total_profit += pos['profit']
        
        print(f"{pos['name']} {code}: {old_price} -> {prices[code]}")
        print(f"  盈亏: {pos['profit']:+.2f} ({pos['profit_rate']:+.2f}%)")

# 重新计算总资产
initial = data['portfolio']['initial_capital']
current = initial + total_profit
data['portfolio']['current_capital'] = current

print(f"\n总资产: {current:,.2f}元")
print(f"总盈亏: {total_profit:+.2f}元 ({total_profit/initial*100:+.2f}%)")

# 保存
with open('portfolio.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('\n数据已更新！')
