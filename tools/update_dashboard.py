# -*- coding: utf-8 -*-
import json

# 读取持仓
p = json.load(open('D:/for workbuddy/finance_bot/portfolio.json', 'r', encoding='utf-8'))
positions = p.get('positions', [])

# 读取选股结果
try:
    s = json.load(open('D:/for workbuddy/finance_bot/stock_pool.json', 'r', encoding='utf-8'))
    stock_pool = s.get('stocks', s.get('stock_pool', []))[:10]
except:
    stock_pool = []

print('=== 持仓 ===')
for pos in positions:
    print(f"{pos['code']} {pos['name']} 成本:{pos['avg_cost']} 现价:{pos['current_price']} 盈亏:{pos.get('profit_rate', 0)}%")

print('\n=== 观察股票 ===')
for stk in stock_pool[:10]:
    scores = stk.get('scores', {})
    tech = stk.get('tech', {})
    print(f"{stk['code']} {stk['name']} 现价:{stk['price']} 涨跌:{stk.get('change_rate', 0)*100:.2f}% 评分:{scores.get('composite', 0)} 信号:{tech.get('signal', '-')}")

# 输出JSON供展示板使用
output = {
    'positions': positions,
    'watchlist': stock_pool[:10],
    'portfolio': p.get('portfolio', {})
}
json.dump(output, open('D:/for workbuddy/finance_bot/dashboard_data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('\n数据已导出到 dashboard_data.json')
