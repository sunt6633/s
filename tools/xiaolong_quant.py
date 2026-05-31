# -*- coding: utf-8 -*-
"""
小龙量化 - 模拟盘 v1.0
数据源：腾讯财经（免费稳定）
初始资金：50,000元
"""
import requests
import json
import os
from datetime import datetime

# ============ 配置 ============
INITIAL_CAPITAL = 50000  # 初始资金5万
PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")

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
                'volume': float(parts[36]) if parts[36] else 0,
                'amount': float(parts[37]) if parts[37] else 0,
                'high': float(parts[33]) if parts[33] else 0,
                'low': float(parts[34]) if parts[34] else 0,
                'open': float(parts[5]) if parts[5] else 0,
                'pe': float(parts[39]) if parts[39] else 0,
            })
    return stocks

# ============ 多因子选股 ============
def score_stock(stock):
    """多因子评分系统"""
    score = 50
    
    # 涨跌幅因子
    change = stock['change_pct']
    if 0 < change < 3:
        score += 10
    elif 3 <= change < 5:
        score += 15
    elif change >= 5:
        score += 5
    elif -3 < change < 0:
        score -= 5
    elif change <= -3:
        score -= 15
    
    # 市盈率因子
    pe = stock['pe']
    if 10 < pe < 20:
        score += 15
    elif 20 <= pe < 30:
        score += 10
    elif pe >= 50:
        score -= 10
    
    # 成交量因子
    if stock['volume'] > 10000 and change > 0:
        score += 10
    
    return min(100, max(0, score))

# ============ 模拟盘 ============
class PaperTrading:
    def __init__(self, initial_capital=INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.load()
    
    def load(self):
        """加载持仓"""
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cash = data.get('cash', self.initial_capital)
                self.positions = data.get('positions', {})
                self.trades = data.get('trades', [])
        else:
            self.cash = self.initial_capital
            self.positions = {}
            self.trades = []
    
    def save(self):
        """保存持仓"""
        data = {
            'cash': self.cash,
            'positions': self.positions,
            'trades': self.trades[-100:],  # 只保留最近100笔交易
            'last_update': datetime.now().isoformat()
        }
        with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def buy(self, stock, shares=100):
        """买入"""
        cost = stock['price'] * shares * 1.0003  # 加手续费
        if cost > self.cash:
            print(f"  ❌ 资金不足，需要{cost:.0f}元，只有{self.cash:.0f}元")
            return False
        
        self.cash -= cost
        code = stock['code']
        if code in self.positions:
            old = self.positions[code]
            total_shares = old['shares'] + shares
            avg_cost = (old['avg_cost'] * old['shares'] + stock['price'] * shares) / total_shares
            self.positions[code] = {'shares': total_shares, 'avg_cost': round(avg_cost, 2)}
        else:
            self.positions[code] = {'shares': shares, 'avg_cost': stock['price']}
        
        self.trades.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': '买入',
            'stock': f"{stock['name']}({code})",
            'price': stock['price'],
            'shares': shares
        })
        self.save()
        print(f"  ✅ 买入 {stock['name']} {shares}股 @ {stock['price']}元")
        return True
    
    def sell(self, stock, shares=100):
        """卖出"""
        code = stock['code']
        if code not in self.positions or self.positions[code]['shares'] < shares:
            print(f"  ❌ 持仓不足")
            return False
        
        revenue = stock['price'] * shares * 0.9997  # 减手续费
        self.cash += revenue
        
        profit = (stock['price'] - self.positions[code]['avg_cost']) * shares
        self.positions[code]['shares'] -= shares
        if self.positions[code]['shares'] == 0:
            del self.positions[code]
        
        self.trades.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': '卖出',
            'stock': f"{stock['name']}({code})",
            'price': stock['price'],
            'shares': shares,
            'profit': round(profit, 2)
        })
        self.save()
        print(f"  ✅ 卖出 {stock['name']} {shares}股 @ {stock['price']}元  盈亏:{profit:+.0f}元")
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
                    profit_pct = (s['price'] / pos['avg_cost'] - 1) * 100 if pos['avg_cost'] > 0 else 0
                    holdings_value += current_value
                    holdings_detail.append({
                        'name': s['name'],
                        'code': code,
                        'shares': pos['shares'],
                        'avg_cost': pos['avg_cost'],
                        'current_price': s['price'],
                        'market_value': current_value,
                        'profit': profit,
                        'profit_pct': profit_pct
                    })
        
        total_assets = self.cash + holdings_value
        total_profit = total_assets - self.initial_capital
        total_profit_pct = (total_assets / self.initial_capital - 1) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total_assets': total_assets,
            'total_profit': total_profit,
            'total_profit_pct': total_profit_pct,
            'holdings': holdings_detail
        }

# ============ 主程序 ============
def run_analysis():
    """运行分析"""
    print("=" * 50)
    print("🐉 小龙量化 - 模拟盘")
    print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
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
    
    # 获取行情
    stocks = get_stock_price(stock_pool)
    
    # 评分排序
    scored = [(s, score_stock(s)) for s in stocks]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    print("\n📊 行情评分:")
    for s, score in scored:
        emoji = "🔴" if s['change_pct'] > 0 else "🟢"
        print(f"  {emoji} {s['name']:　<6} {s['price']:>8.2f}元 {s['change_pct']:>+6.2f}%  评分:{score}")
    
    # 模拟盘状态
    account = PaperTrading()
    status = account.get_status(stocks)
    
    print(f"\n💰 账户状态:")
    print(f"  总资产: {status['total_assets']:>12,.0f}元")
    print(f"  可用:   {status['cash']:>10,.0f}元")
    print(f"  持仓:   {status['holdings_value']:>10,.0f}元")
    p_emoji = "🟢" if status['total_profit'] >= 0 else "🔴"
    print(f"  盈亏:   {p_emoji} {status['total_profit']:>+.0f}元 ({status['total_profit_pct']:+.2f}%)")
    
    if status['holdings']:
        print("\n📈 持仓明细:")
        for h in status['holdings']:
            e = "🟢" if h['profit'] >= 0 else "🔴"
            print(f"  {e} {h['name']:　<6} {h['shares']}股 成本{h['avg_cost']:.2f} 现价{h['current_price']:.2f} {h['profit']:>+.0f}元")
    
    # 交易建议
    print("\n💡 交易建议:")
    buy_list = [s for s, score in scored if score >= 75]
    for s in buy_list[:2]:
        if s['code'] not in account.positions:
            shares = 100 if s['price'] > 100 else 200
            print(f"  建议买入: {s['name']} {shares}股 (评分{score_stock(s)})")
    
    return status

if __name__ == '__main__':
    run_analysis()
