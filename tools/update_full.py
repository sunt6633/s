"""
根据截图完整更新持仓数据，包括中兴通讯
"""
import json
from datetime import datetime

# 读取当前持仓
with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 根据截图更新最新价格和时间
prices = {
    '000063': {'price': 35.38, 'shares': 100, 'cost': 37.0},  # 中兴通讯
    '601318': {'price': 57.79, 'shares': 200, 'cost': 45.9},  # 中国平安
    '601166': {'price': 18.41, 'shares': 1100, 'cost': 16.8}, # 兴业银行
}

# 名称映射
name_map = {'000063': '中兴通讯', '601318': '中国平安', '601166': '兴业银行'}

# 重建持仓列表
positions = []
total_profit = 0
total_market = 0

for code, info in prices.items():
    market_value = info['price'] * info['shares']
    cost_value = info['cost'] * info['shares']
    profit = market_value - cost_value
    profit_rate = (profit / cost_value) * 100
    
    positions.append({
        'code': code,
        'name': name_map[code],
        'shares': info['shares'],
        'avg_cost': info['cost'],
        'current_price': info['price'],
        'market_value': market_value,
        'profit': profit,
        'profit_rate': profit_rate,
        'current_price_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sold_ratio': 0
    })
    
    total_profit += profit
    total_market += market_value

# 更新数据
initial = data['portfolio']['initial_capital']

data['positions'] = positions
data['portfolio']['current_capital'] = initial + total_profit
data['portfolio']['total_profit'] = total_profit
data['portfolio']['total_profit_rate'] = (total_profit / initial) * 100
data['portfolio']['total_value'] = data['portfolio']['current_capital']

print('=' * 50)
print('持仓数据已根据截图完整更新')
print('=' * 50)
print('更新时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('')
print('标的        成本      现价        盈亏         收益率')
print('-' * 50)

for p in positions:
    name = p['name'].ljust(8)
    cost = p['avg_cost']
    price = p['current_price']
    profit = p['profit']
    rate = p['profit_rate']
    print(f'{name} {cost:8.2f} {price:8.2f} {profit:+12.2f} {rate:+10.2f}%')

print('-' * 50)
print(f'总盈亏: {total_profit:+.2f}元 ({total_profit/initial*100:+.2f}%)')
print(f'总资产: {data["portfolio"]["current_capital"]:,.2f}元')

# 保存
with open('portfolio.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('')
print('数据已保存到portfolio.json')
