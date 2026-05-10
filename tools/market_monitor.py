# -*- coding: utf-8 -*-
"""
盘中实时监控系统 - 金融助手
交易时段（9:30-11:30, 13:00-15:00）实时监控，一旦触发条件立即执行交易
"""

import sys
import os
import json
import time
import random
from datetime import datetime, time as dtime
from threading import Thread, Event

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading_engine import load_portfolio, save_portfolio, execute_trade, update_positions_value
from learning_engine import engine

# 配置
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_config.json")

class MarketMonitor:
    def __init__(self):
        self.load_config()
        self.stop_event = Event()
        self.portfolio = None
        self.trade_notifications = []
        
    def load_config(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'check_interval': 600,      # 检查间隔（秒），默认10分钟
                'trading_hours': [           # 交易时段
                    {'start': '09:30', 'end': '11:30'},
                    {'start': '13:00', 'end': '15:00'}
                ],
                'auto_trade': True,          # 自动交易开关
                'notify_on_trade': True,     # 交易通知开关
                'max_concurrent_trades': 3, # 单次最多交易数
            }
    
    def save_config(self):
        """保存配置"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def is_trading_time(self):
        """判断是否在交易时间内"""
        now = datetime.now()
        current_time = now.time()
        
        # 周末休市
        if now.weekday() >= 5:  # 周六、周日
            return False
        
        for period in self.config['trading_hours']:
            start = dtime.fromisoformat(period['start'])
            end = dtime.fromisoformat(period['end'])
            if start <= current_time <= end:
                return True
        return False
    
    def simulate_price_change(self, price, volatility=0.02):
        """模拟实时价格变动"""
        change = random.uniform(-volatility, volatility)
        return round(price * (1 + change), 2)
    
    def check_and_trade(self):
        """检查持仓和市场，执行交易"""
        if not self.is_trading_time():
            return []
        
        self.portfolio = load_portfolio()
        trades = []
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 盘中检查 ===")
        
        # 1. 检查持仓（止损/止盈/卖出信号）
        position_trades = self._check_positions()
        trades.extend(position_trades)
        
        # 2. 检查买入机会
        if self.config['auto_trade']:
            buy_trades = self._check_buy_opportunities()
            trades.extend(buy_trades)
        
        # 3. 记录学习数据
        for trade in trades:
            self._record_learning(trade)
        
        # 4. 保存更新后的持仓
        if trades:
            self.portfolio = update_positions_value(self.portfolio)
            save_portfolio(self.portfolio)
            self._notify_trades(trades)
        
        return trades
    
    def _check_positions(self):
        """检查持仓，触发条件则卖出"""
        trades = []
        params = self.portfolio.get('settings', {})
        stop_loss = params.get('stop_loss', 0.08)
        profit_target = params.get('profit_target', 0.15)
        
        print(f"\n--- 持仓检查 ({len(self.portfolio['positions'])} 只) ---")
        
        for pos in self.portfolio['positions'][:]:
            # 模拟实时价格
            current_price = self.simulate_price_change(pos.get('current_price', pos['avg_cost']))
            profit_rate = (current_price - pos['avg_cost']) / pos['avg_cost']
            
            # 更新持仓价格
            pos['current_price'] = current_price
            
            # 使用学习引擎判断卖出
            sell_signal = engine.get_sell_signals(pos, current_price, {})
            
            print(f"  {pos['name']}: {current_price}元 ({profit_rate*100:+.1f}%) - {sell_signal['reason']}")
            
            if sell_signal['action'] == 'sell':
                trade = execute_trade(self.portfolio, pos, 'sell', current_price)
                trade['reason'] = sell_signal['reason']
                trade['urgency'] = sell_signal['urgency']
                trade['trade_type'] = 'position_exit'
                trades.append(trade)
                
                urgency_mark = "🔴" if sell_signal['urgency'] == 'high' else "🟡"
                print(f"    {urgency_mark} 卖出: {pos['name']} @ {current_price}元")
                
                # 记录卖出结果用于学习
                if pos.get('buy_price'):
                    engine.record_sell_result(
                        pos['code'],
                        pos['buy_price'],
                        current_price,
                        sell_signal['reason']
                    )
        
        return trades
    
    def _check_buy_opportunities(self):
        """检查买入机会"""
        trades = []
        
        # 检查是否还有仓位空间
        max_positions = self.portfolio['settings'].get('pool_size', 10)
        current_positions = len(self.portfolio['positions'])
        available_slots = max_positions - current_positions
        
        if available_slots <= 0:
            print("\n--- 买入检查: 仓位已满 ---")
            return []
        
        # 检查资金
        available_capital = self.portfolio['portfolio']['current_capital'] * 0.8
        if available_capital < 2000:
            print("\n--- 买入检查: 资金不足 ---")
            return []
        
        print(f"\n--- 买入机会扫描 ({available_slots} 个空位) ---")
        
        # 获取候选股票池
        stock_pool = self.portfolio.get('stock_pool', [])
        
        # 排除已有持仓
        existing_codes = [p['code'] for p in self.portfolio['positions']]
        candidates = [s for s in stock_pool if s.get('code') not in existing_codes]
        
        # 使用学习引擎筛选买入信号
        buy_signals = engine.get_buy_signals(candidates, {})
        
        max_buy = min(available_slots, self.config['max_concurrent_trades'], len(buy_signals))
        
        for signal in buy_signals[:max_buy]:
            stock = signal['stock']
            current_price = self.simulate_price_change(stock.get('price', 100))
            
            # 执行买入
            trade = execute_trade(self.portfolio, stock, 'buy', current_price)
            trade['confidence'] = signal['confidence']
            trade['factors'] = signal['factors']
            trade['trade_type'] = 'new_position'
            trades.append(trade)
            
            # 记录买入价格用于后续追踪
            for pos in self.portfolio['positions']:
                if pos['code'] == stock['code']:
                    pos['buy_price'] = current_price
                    pos['peak_profit'] = 0
            
            print(f"  [买入] {stock['name']} @ {current_price}元")
            print(f"     信号强度: {signal['confidence']*100:.0f}%")
            print(f"     因素: {'; '.join(signal['factors'][:2])}")
        
        return trades
    
    def _record_learning(self, trade):
        """记录交易供学习"""
        engine.record_trade({
            'code': trade.get('code'),
            'name': trade.get('name'),
            'action': trade.get('action'),
            'price': trade.get('price'),
            'shares': trade.get('shares'),
            'amount': trade.get('amount'),
            'reason': trade.get('reason'),
            'trade_type': trade.get('trade_type'),
            'confidence': trade.get('confidence'),
            'factors': trade.get('factors', [])
        })
    
    def _notify_trades(self, trades):
        """生成交易通知"""
        for trade in trades:
            action_text = "买入" if trade['action'] == 'buy' else "卖出"
            msg = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'type': 'trade',
                'content': f"{action_text} {trade['name']} {trade['shares']}股 @ {trade['price']}元\n原因: {trade['reason']}"
            }
            self.trade_notifications.append(msg)
    
    def run_continuous(self):
        """持续运行监控"""
        print("=" * 60)
        print("  盘中实时监控系统启动")
        print(f"  检查间隔: {self.config['check_interval']}秒")
        print("  交易时段: 9:30-11:30, 13:00-15:00")
        print("=" * 60)
        
        while not self.stop_event.is_set():
            if self.is_trading_time():
                trades = self.check_and_trade()
                
                # 显示当前状态
                self._show_status()
            else:
                current_time = datetime.now().strftime('%H:%M')
                weekday = datetime.now().weekday()
                day_names = ['一', '二', '三', '四', '五', '六', '日']
                
                if weekday < 5:
                    print(f"[{current_time}] 非交易时段，等待中...")
                else:
                    print(f"[{current_time}] 周末休市，停止监控")
                    break
            
            # 等待下次检查
            self.stop_event.wait(self.config['check_interval'])
        
        print("\n监控系统已停止")
    
    def _show_status(self):
        """显示当前状态"""
        if self.portfolio:
            p = self.portfolio['portfolio']
            positions = self.portfolio['positions']
            print(f"\n[当前状态]")
            print(f"   总资产: {p['total_value']:.2f}元")
            print(f"   持仓: {len(positions)}只")
            print(f"   现金: {p['current_capital']:.2f}元")
    
    def stop(self):
        """停止监控"""
        self.stop_event.set()
    
    def get_notifications(self):
        """获取待发送的通知"""
        notifications = self.trade_notifications.copy()
        self.trade_notifications.clear()
        return notifications


def start_monitor():
    """启动监控"""
    monitor = MarketMonitor()
    
    try:
        monitor.run_continuous()
    except KeyboardInterrupt:
        print("\n收到停止信号...")
        monitor.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次检查模式
        monitor = MarketMonitor()
        trades = monitor.check_and_trade()
        if trades:
            print(f"\n执行了 {len(trades)} 笔交易")
        else:
            print("\n本次检查无交易")
    else:
        # 持续监控模式
        start_monitor()
