"""
金小融交易记录与资金计算
正确追踪买卖操作，计算实际盈亏
"""
import json
from datetime import datetime
from pathlib import Path

PORTFOLIO_FILE = 'D:/for workbuddy/finance_bot/portfolio.json'
TRADE_FILE = 'D:/for workbuddy/finance_bot/trades.json'

class TradeRecorder:
    """交易记录器"""
    
    def __init__(self):
        self.trades = self._load_trades()
    
    def _load_trades(self):
        """加载交易记录"""
        if Path(TRADE_FILE).exists():
            with open(TRADE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'trades': [],
            'initial_capital': 100000,
            'cash': 100000,  # 可用资金
            'invested': 0,    # 已投入资金
            'total_sell': 0   # 卖出总收入
        }
    
    def _save_trades(self):
        """保存交易记录"""
        with open(TRADE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.trades, f, ensure_ascii=False, indent=2)
    
    def buy(self, code, name, price, shares):
        """记录买入"""
        amount = price * shares
        trade = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'BUY',
            'code': code,
            'name': name,
            'price': price,
            'shares': shares,
            'amount': amount
        }
        self.trades['trades'].append(trade)
        self.trades['cash'] -= amount
        self.trades['invested'] += amount
        self._save_trades()
        return trade
    
    def sell(self, code, name, price, shares):
        """记录卖出"""
        amount = price * shares
        trade = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'SELL',
            'code': code,
            'name': name,
            'price': price,
            'shares': shares,
            'amount': amount
        }
        self.trades['trades'].append(trade)
        self.trades['cash'] += amount
        self.trades['invested'] -= price * shares  # 减少投入（按成本价计算）
        self.trades['total_sell'] += amount
        self._save_trades()
        return trade
    
    def calculate_portfolio_value(self, positions):
        """计算当前总资产"""
        market_value = sum(p['current_price'] * p['shares'] for p in positions)
        return self.trades['cash'] + market_value
    
    def get_summary(self):
        """获取资金汇总"""
        return {
            'initial_capital': self.trades['initial_capital'],
            'cash': self.trades['cash'],
            'invested': self.trades['invested'],
            'total_sell': self.trades['total_sell'],
            'trade_count': len(self.trades['trades'])
        }
    
    def print_summary(self, positions):
        """打印资金汇总"""
        summary = self.get_summary()
        market_value = sum(p['current_price'] * p['shares'] for p in positions)
        total_value = summary['cash'] + market_value
        profit = total_value - summary['initial_capital']
        profit_rate = profit / summary['initial_capital'] * 100
        
        print("=" * 60)
        print("金小融资金账户")
        print("=" * 60)
        print(f"  初始资金:     {summary['initial_capital']:,.2f}元")
        print(f"  可用现金:     {summary['cash']:,.2f}元")
        print(f"  持仓市值:     {market_value:,.2f}元")
        print(f"  ─────────────────────────")
        print(f"  当前总资产:   {total_value:,.2f}元")
        print(f"  总盈亏:       {profit:+,.2f}元 ({profit_rate:+.2f}%)")
        print(f"  ─────────────────────────")
        print(f"  卖出总收入:   {summary['total_sell']:,.2f}元")
        print(f"  交易次数:     {summary['trade_count']}次")
        print("=" * 60)
        
        return total_value, profit, profit_rate
    
    def init_from_portfolio(self, positions):
        """从现有持仓初始化交易记录"""
        # 检查是否已有交易记录
        if len(self.trades['trades']) > 0:
            print("已有交易记录，跳过初始化")
            return
        
        # 添加历史买入记录
        for pos in positions:
            self.buy(
                code=pos['code'],
                name=pos['name'],
                price=pos['avg_cost'],
                shares=pos['shares']
            )
        
        # 添加止盈卖出记录（200股平安@59.72）
        self.sell(
            code='601318',
            name='中国平安',
            price=59.72,
            shares=200
        )
        
        print("已从现有持仓初始化交易记录")


def main():
    print("=" * 60)
    print("金小融资金系统初始化")
    print("=" * 60)
    
    recorder = TradeRecorder()
    
    # 加载持仓
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    positions = data['positions']
    
    # 初始化交易记录
    recorder.init_from_portfolio(positions)
    
    # 显示汇总
    recorder.print_summary(positions)
    
    # 打印交易流水
    print("\n交易记录:")
    for t in recorder.trades['trades']:
        sign = '+' if t['action'] == 'SELL' else '-'
        print(f"  [{t['time']}] {t['action']} {t['name']} {t['shares']}股@{t['price']} = {sign}{t['amount']:,.2f}元")


if __name__ == '__main__':
    main()
