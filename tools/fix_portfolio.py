"""
金小融资金修复脚本
中兴通讯(000063)属于孙先生自有持仓，不计入金小融账户
"""
import json
from datetime import datetime

PORTFOLIO_FILE = 'D:/for workbuddy/finance_bot/portfolio.json'

def fix_portfolio():
    """修复持仓数据，移除中兴通讯，只保留金小融操作的标的"""
    print("=" * 60)
    print("金小融资金修复")
    print("=" * 60)
    
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 记录修复前的数据
    print("\n【修复前持仓】")
    for p in data['positions']:
        print(f"  {p['name']} {p['code']}: {p['shares']}股")
    
    # 过滤掉中兴通讯（孙先生自有持仓）
    sun_positions = [p for p in data['positions'] if p['code'] == '000063']
    jin_positions = [p for p in data['positions'] if p['code'] != '000063']
    
    print(f"\n【孙先生自有持仓 - 已移除】")
    for p in sun_positions:
        print(f"  {p['name']} {p['code']}: {p['shares']}股")
        print(f"    (金小融不负责，不计入盈亏计算)")
    
    # 计算金小融的买入成本
    jin_cost = 0
    for p in jin_positions:
        cost = p['avg_cost'] * p['shares']
        jin_cost += cost
        print(f"\n【金小融买入】{p['name']} {p['shares']}股 × {p['avg_cost']} = {cost:,.2f}元")
    
    print(f"\n金小融买入总成本: {jin_cost:,.2f}元")
    
    # 计算卖出收入（止盈卖出200股平安@59.72）
    sell_income = 59.72 * 200
    print(f"卖出平安收入: +{sell_income:,.2f}元 (200股@59.72)")
    
    # 计算当前持仓市值（金小融部分）
    jin_market_value = 0
    for p in jin_positions:
        mv = p['current_price'] * p['shares']
        p['market_value'] = mv
        jin_market_value += mv
        profit = (p['current_price'] - p['avg_cost']) * p['shares']
        profit_rate = (p['current_price'] - p['avg_cost']) / p['avg_cost'] * 100
        print(f"\n{p['name']} {p['code']}")
        print(f"  持仓: {p['shares']}股 | 成本: {p['avg_cost']} | 现价: {p['current_price']}")
        print(f"  市值: {mv:,.2f}元 | 盈亏: {profit:+,.2f}元 ({profit_rate:+.2f}%)")
    
    # 计算金小融总资产
    # 初始资金100000 - 买入支出 + 卖出收入 + 当前持仓市值
    initial_capital = 100000
    jin_total = initial_capital - jin_cost + sell_income + jin_market_value
    jin_profit = jin_total - initial_capital
    jin_profit_rate = jin_profit / initial_capital * 100
    
    print(f"\n" + "=" * 60)
    print("金小融资金计算（不含中兴通讯）")
    print("=" * 60)
    print(f"  初始资金:     {initial_capital:,.2f}元")
    print(f"  - 买入支出:   {jin_cost:,.2f}元")
    print(f"  + 卖出收入:   {sell_income:,.2f}元")
    print(f"  + 持仓市值:   {jin_market_value:,.2f}元")
    print(f"  ─────────────────────────")
    print(f"  当前总资产:   {jin_total:,.2f}元")
    print(f"  总盈亏:       {jin_profit:+,.2f}元 ({jin_profit_rate:+.2f}%)")
    print(f"  ─────────────────────────")
    print(f"  收益率:       {jin_profit_rate:+.2f}%")
    
    # 更新数据
    data['positions'] = jin_positions  # 只保留金小融持仓
    data['portfolio']['initial_capital'] = initial_capital
    data['portfolio']['current_capital'] = jin_total
    data['portfolio']['total_profit'] = jin_profit
    data['portfolio']['total_profit_rate'] = jin_profit_rate
    data['portfolio']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['portfolio']['note'] = '不含孙先生自有持仓(中兴通讯000063)'
    
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 数据已修复并保存！")
    
    return jin_total, jin_profit, jin_profit_rate

if __name__ == '__main__':
    fix_portfolio()
