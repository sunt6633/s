"""查询卖出平安资金去向"""
import json

with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=' * 50)
print('资金追踪')
print('=' * 50)
print()

# 初始资金
initial = 100000
print(f'初始资金: {initial:,.0f}元')
print()

# 买入成本
cost_000063 = 37 * 100    # 中兴通讯
cost_601318 = 45.9 * 400 # 平安（原始400股）
cost_601166 = 16.8 * 1100 # 兴业银行
total_cost = cost_000063 + cost_601318 + cost_601166

print(f'买入总支出: {total_cost:,.0f}元')
print(f'  - 中兴通讯100股 x 37.00 = {cost_000063:,}')
print(f'  - 中国平安400股 x 45.90 = {cost_601318:,}')
print(f'  - 兴业银行1100股 x 16.80 = {cost_601166:,}')
print()

# 卖出收入
sell_601318 = 59.72 * 200  # 止盈卖出200股
print(f'卖出收入: +{sell_601318:,.2f}元')
print(f'  - 中国平安200股 x 59.72 (11:49止盈)')
print()

# 应该剩余现金
expected_cash = initial - total_cost + sell_601318
print(f'预期现金: {expected_cash:,.2f}元')
print()

# 当前持仓市值
market_value = sum(p['current_price'] * p['shares'] for p in data['positions'])
print(f'当前持仓市值: {market_value:,.2f}元')
for p in data['positions']:
    print(f"  - {p['name']}: {p['shares']}股 x {p['current_price']:.2f} = {p['current_price']*p['shares']:,.2f}")
print()

# 总计
total = expected_cash + market_value
print(f'预期总资产: {total:,.2f}元')
print(f'实际总资产: {data["portfolio"]["current_capital"]:,.2f}元')
print()

# 盈亏计算
profit = data['portfolio']['current_capital'] - initial
print(f'总盈亏: {profit:+,.2f}元 ({profit/initial*100:+.2f}%)')
