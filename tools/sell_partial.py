import json
from datetime import datetime

# 读取当前持仓
with open('portfolio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 中国平安止盈50%
for pos in data['positions']:
    if pos['code'] == '601318':
        sell_shares = pos['shares'] // 2  # 卖出200股
        sell_price = 59.72
        profit = (sell_price - pos['avg_cost']) * sell_shares

        # 更新持仓
        pos['shares'] -= sell_shares
        pos['sold_ratio'] = 0.5

        # 增加现金
        data['portfolio']['current_capital'] += sell_price * sell_shares

        # 记录交易
        trade = {
            'date': '2026-04-17',
            'time': '11:49:00',
            'code': '601318',
            'name': '中国平安',
            'action': 'sell_partial',
            'price': sell_price,
            'shares': sell_shares,
            'amount': sell_price * sell_shares,
            'profit': profit,
            'reason': '止盈(盈利+30.11%)，卖出50%锁利'
        }
        data['trade_history'].append(trade)

        print('已执行止盈：卖出{} {}股 @ {}'.format(pos['name'], sell_shares, sell_price))
        print('锁定利润：{:.2f}元'.format(profit))
        break

# 保存
with open('portfolio.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('\n持仓已更新')
