# -*- coding: utf-8 -*-
"""
小龙量化 - 快速测试脚本
使用腾讯财经数据源（免费稳定）
"""
import requests
import re
from datetime import datetime

# ============ 腾讯数据源 ============
def get_stock_price(stock_codes):
    """
    获取股票实时行情
    stock_codes: ['sh600519', 'sz000858', ...]
    """
    url = f'https://qt.gtimg.cn/q={",".join(stock_codes)}'
    r = requests.get(url, timeout=10)
    r.encoding = 'gbk'
    
    stocks = []
    for line in r.text.strip().split(';'):
        if '=' not in line:
            continue
        key, val = line.split('=', 1)
        parts = val.strip('"').split('~')
        if len(parts) > 40:
            stocks.append({
                'name': parts[1],
                'code': parts[2],
                'price': float(parts[3]) if parts[3] else 0,
                'change_pct': float(parts[32]) if parts[32] else 0,
                'volume': float(parts[36]) if parts[36] else 0,  # 成交量(手)
                'amount': float(parts[37]) if parts[37] else 0,  # 成交额(万)
                'high': float(parts[33]) if parts[33] else 0,
                'low': float(parts[34]) if parts[34] else 0,
                'open': float(parts[5]) if parts[5] else 0,
                'pe': float(parts[39]) if parts[39] else 0,  # 市盈率
            })
    return stocks

# ============ 简易多因子选股 ============
def score_stock(stock):
    """简易评分系统"""
    score = 50  # 基础分
    
    # 涨跌幅因子（适度上涨加分，大涨减分）
    change = stock['change_pct']
    if 0 < change < 3:
        score += 10
    elif 3 <= change < 5:
        score += 15
    elif change >= 5:
        score += 5  # 大涨谨慎
    elif -3 < change < 0:
        score -= 5
    elif change <= -3:
        score -= 15
    
    # 市盈率因子（10-30为合理）
    pe = stock['pe']
    if 10 < pe < 20:
        score += 15
    elif 20 <= pe < 30:
        score += 10
    elif pe >= 50:
        score -= 10
    
    # 成交量因子（放量上涨加分）
    if stock['volume'] > 10000 and change > 0:  # 成交量>1万手且上涨
        score += 10
    
    return min(100, max(0, score))

# ============ 模拟盘 ============
class PaperTrading:
    """模拟盘"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {code: {shares, avg_cost}}
        self.trades = []
    
    def buy(self, stock, shares=100):
        """买入"""
        cost = stock['price'] * shares
        if cost > self.cash:
            print(f"  ❌ 资金不足，需要{cost:.0f}元，只有{self.cash:.0f}元")
            return False
        
        self.cash -= cost
        code = stock['code']
        if code in self.positions:
            old = self.positions[code]
            total_shares = old['shares'] + shares
            avg_cost = (old['avg_cost'] * old['shares'] + stock['price'] * shares) / total_shares
            self.positions[code] = {'shares': total_shares, 'avg_cost': avg_cost}
        else:
            self.positions[code] = {'shares': shares, 'avg_cost': stock['price']}
        
        self.trades.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'action': '买入',
            'stock': f"{stock['name']}({code})",
            'price': stock['price'],
            'shares': shares,
            'amount': cost
        })
        print(f"  ✅ 买入 {stock['name']} {shares}股 @ {stock['price']}元 = {cost:.0f}元")
        return True
    
    def sell(self, stock, shares=100):
        """卖出"""
        code = stock['code']
        if code not in self.positions or self.positions[code]['shares'] < shares:
            print(f"  ❌ 持仓不足")
            return False
        
        revenue = stock['price'] * shares
        self.cash += revenue
        self.positions[code]['shares'] -= shares
        if self.positions[code]['shares'] == 0:
            del self.positions[code]
        
        self.trades.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'action': '卖出',
            'stock': f"{stock['name']}({code})",
            'price': stock['price'],
            'shares': shares,
            'amount': revenue
        })
        print(f"  ✅ 卖出 {stock['name']} {shares}股 @ {stock['price']}元 = {revenue:.0f}元")
        return True
    
    def get_status(self, current_prices):
        """获取账户状态"""
        holdings_value = 0
        holdings_detail = []
        for code, pos in self.positions.items():
            for s in current_prices:
                if s['code'] == code:
                    current_value = s['price'] * pos['shares']
                    profit = (s['price'] - pos['avg_cost']) * pos['shares']
                    profit_pct = (s['price'] / pos['avg_cost'] - 1) * 100
                    holdings_value += current_value
                    holdings_detail.append({
                        'name': s['name'],
                        'code': code,
                        'shares': pos['shares'],
                        'avg_cost': pos['avg_cost'],
                        'current_price': s['price'],
                        'profit': profit,
                        'profit_pct': profit_pct
                    })
        
        total_assets = self.cash + holdings_value
        total_profit = total_assets - self.initial_capital
        total_profit_pct = (total_assets / self.initial_capital - 1) * 100
        
        return {
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total_assets': total_assets,
            'total_profit': total_profit,
            'total_profit_pct': total_profit_pct,
            'holdings': holdings_detail
        }

# ============ 主程序 ============
if __name__ == '__main__':
    print("=" * 50)
    print("🐉 小龙量化 - 模拟盘测试")
    print("=" * 50)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 股票池
    stock_pool = [
        'sh600519',  # 贵州茅台
        'sh601318',  # 中国平安
        'sz000858',  # 五粮液
        'sh600036',  # 招商银行
        'sz002714',  # 牧原股份
        'sh600276',  # 恒瑞医药
        'sz000333',  # 美的集团
        'sh601888',  # 中国中免
    ]
    
    # 获取实时行情
    print("📊 获取实时行情...")
    stocks = get_stock_price(stock_pool)
    
    # 显示行情
    print("\n【今日行情】")
    print("-" * 50)
    for s in stocks:
        emoji = "🔴" if s['change_pct'] > 0 else "🟢" if s['change_pct'] < 0 else "⚪"
        print(f"{emoji} {s['name']:　<6} {s['price']:>8.2f}元  {s['change_pct']:>+6.2f}%  PE:{s['pe']:.1f}")
    
    # 评分
    print("\n【多因子评分】")
    print("-" * 50)
    scored_stocks = [(s, score_stock(s)) for s in stocks]
    scored_stocks.sort(key=lambda x: x[1], reverse=True)
    for s, score in scored_stocks:
        bar = "█" * (score // 5)
        print(f"{s['name']:　<6} {score:>3}分 {bar}")
    
    # 模拟交易
    print("\n【模拟交易】")
    print("-" * 50)
    account = PaperTrading(initial_capital=100000)
    
    # 买入评分最高的3只
    buy_candidates = [s for s, score in scored_stocks if score >= 65][:3]
    for s in buy_candidates:
        shares = 100 if s['price'] > 100 else 200  # 茅台买1手，其他买2手
        account.buy(s, shares)
    
    # 显示账户状态
    print("\n【模拟盘状态】")
    print("-" * 50)
    status = account.get_status(stocks)
    print(f"💰 总资产: {status['total_assets']:>12,.0f}元")
    print(f"💵 可用资金: {status['cash']:>10,.0f}元")
    print(f"📈 持仓市值: {status['holdings_value']:>10,.0f}元")
    profit_emoji = "🟢" if status['total_profit'] >= 0 else "🔴"
    print(f"{profit_emoji} 总盈亏: {status['total_profit']:>+12,.0f}元 ({status['total_profit_pct']:+.2f}%)")
    
    if status['holdings']:
        print("\n【持仓明细】")
        print("-" * 50)
        for h in status['holdings']:
            emoji = "🟢" if h['profit'] >= 0 else "🔴"
            print(f"{emoji} {h['name']:　<6} {h['shares']}股 @ {h['avg_cost']:.2f} → {h['current_price']:.2f}  盈亏:{h['profit']:>+.0f}元({h['profit_pct']:+.1f}%)")
    
    print("\n✅ 测试完成！")
