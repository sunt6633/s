import json

# 读取当前持仓
with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== 持仓数据 ===')
for pos in data['positions']:
    print(f"{pos['name']} {pos['code']}: 成本={pos['avg_cost']}, 现价={pos['current_price']}, 盈亏={pos['profit_rate']:.2f}%")
