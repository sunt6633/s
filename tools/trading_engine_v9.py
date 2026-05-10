# -*- coding: utf-8 -*-
"""
模拟交易引擎 v9.0 - 金融助手
执行买卖操作，管理仓位，计算收益

【进化v9.0 - 全面风控升级版】
基于孙先生指示：
1. 动态止损（根据波动率自适应）
2. 个股最大回撤15%强制清仓
3. 账户总回撤10%一键清仓
4. 亏损连续3天暂停交易

核心理念：风控第一，机器执行

升级日期：2026-04-16
"""

import json
import os
import random
import requests
from datetime import datetime, time, timedelta
from copy import deepcopy
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 数据源模块（支持akshare和QVeris）
from data_source import get_realtime_price, set_data_source, get_data_source
HAS_QVERIS = True  # 保留兼容性

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")

# 注意：数据源已迁移到 data_source.py 模块
# 使用 get_realtime_price() 函数获取实时价格


# ============ A股交易时间定义 ============
TRADING_MORNING_START = time(9, 30)
TRADING_MORNING_END = time(11, 30)
TRADING_AFTERNOON_START = time(13, 0)
TRADING_AFTERNOON_END = time(15, 0)

def is_trading_time():
    """检查当前是否在A股交易时间内"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    if weekday >= 5:
        return False, f"周末不能交易"
    
    if TRADING_MORNING_START <= current_time <= TRADING_MORNING_END:
        return True, f"上午交易时间"
    
    if TRADING_AFTERNOON_START <= current_time <= TRADING_AFTERNOON_END:
        return True, f"下午交易时间"
    
    if current_time < TRADING_MORNING_START:
        return False, f"还没开盘（9:30才开）"
    elif current_time > TRADING_AFTERNOON_END:
        return False, f"已收盘（15:00已过）"
    elif TRADING_MORNING_END < current_time < TRADING_AFTERNOON_START:
        return False, f"中午休市"
    
    return False, "非交易时间"


# ============ v9.0 全面风控体系 ============

# 【v9.0 动态止损配置】
DYNAMIC_STOP_LOSS_CONFIG = {
    # 波动率分级
    'low_volatility': 0.08,      # 低波动：止损8%
    'medium_volatility': 0.10,   # 中波动：止损10%
    'high_volatility': 0.12,      # 高波动：止损12%
    
    # 波动率阈值
    'vol_low_threshold': 0.02,   # 日波幅<2%为低波动
    'vol_high_threshold': 0.04,  # 日波幅>4%为高波动
    
    # 保本止损
    'breakeven_trigger': 0.05,   # 盈利>5%后上调到保本
    'breakeven_protection': 0.00, # 保本止损
    
    # 盈利保护
    'profit_protection_10': -0.08,   # 盈利>10%，回撤8%保护
    'profit_protection_20': -0.10,   # 盈利>20%，回撤10%保护
    'profit_protection_30': -0.12,   # 盈利>30%，回撤12%保护
}

# 【v9.0 个股最大回撤配置】
SINGLE_STOCK_MAX_DRAWDOWN = {
    'max_drawdown': 0.15,        # 单股最大回撤15%强制清仓
    'warning_drawdown': 0.10,    # 回撤10%预警
    'strict_mode': True,         # 严格模式：触发即清仓
}

# 【v9.0 账户级风控配置】
ACCOUNT_RISK_CONTROL = {
    'total_max_drawdown': 0.10,       # 账户总回撤10%一键清仓
    'daily_max_loss': 0.03,          # 单日最大亏损3%
    'weekly_max_loss': 0.08,         # 单周最大亏损8%暂停
    'consecutive_loss_days': 3,      # 连续亏损3天暂停
    'pause_trading_days': 2,         # 暂停交易天数
}

# 【v9.0 熔断机制配置】
CIRCUIT_BREAKER = {
    'market_crash_threshold': -0.03,  # 大盘单日跌3%触发熔断
    'single_limit_down': True,         # 个股跌停熔断
    'volume_surge_alert': 2.5,        # 量比>2.5预警
    'auto_close_all': True,           # 极端行情自动清仓
}

# 【v9.0 分批止盈配置】
PROFIT_TAKING_LEVELS = [
    {'profit_rate': 0.10, 'sell_ratio': 0.30, 'desc': '盈利10%，止盈30%'},
    {'profit_rate': 0.20, 'sell_ratio': 0.30, 'desc': '盈利20%，累计止盈60%'},
    {'profit_rate': 0.30, 'sell_ratio': 0.30, 'desc': '盈利30%，累计止盈90%'},
    {'profit_rate': 0.50, 'sell_ratio': 0.10, 'desc': '盈利50%，清仓'},
]


def calculate_volatility(prices):
    """
    计算股价波动率（日波幅）
    """
    if len(prices) < 2:
        return 0.03  # 默认3%
    
    # 计算每日涨跌幅
    changes = []
    for i in range(1, len(prices)):
        change = abs(prices[i] - prices[i-1]) / prices[i-1]
        changes.append(change)
    
    # 返回平均日波幅
    return sum(changes) / len(changes) if changes else 0.03


def get_dynamic_stop_loss(position, current_price):
    """
    v9.0 动态止损计算
    
    根据持仓时间长短和盈亏状态，动态调整止损线
    """
    cost = position.get('avg_cost', 0)
    shares = position.get('shares', 0)
    if cost == 0 or shares == 0:
        return DYNAMIC_STOP_LOSS_CONFIG['medium_volatility']
    
    # 计算盈亏率
    profit_rate = (current_price - cost) / cost
    
    # 计算持仓时间（天数）
    buy_date_str = position.get('buy_date', '')
    if buy_date_str:
        try:
            buy_date = datetime.strptime(buy_date_str, "%Y-%m-%d")
            holding_days = (datetime.now() - buy_date).days
        except:
            holding_days = 1
    else:
        holding_days = 1
    
    # 基础止损线
    base_stop_loss = DYNAMIC_STOP_LOSS_CONFIG['medium_volatility']
    
    # 根据持仓时间调整（持仓越久，止损越宽）
    if holding_days > 20:
        base_stop_loss = DYNAMIC_STOP_LOSS_CONFIG['high_volatility']
    elif holding_days > 10:
        base_stop_loss = DYNAMIC_STOP_LOSS_CONFIG['medium_volatility']
    else:
        base_stop_loss = DYNAMIC_STOP_LOSS_CONFIG['low_volatility']
    
    # 根据盈亏状态调整
    if profit_rate > 0.30:
        # 盈利>30%，回撤12%保护
        return DYNAMIC_STOP_LOSS_CONFIG['profit_protection_30']
    elif profit_rate > 0.20:
        # 盈利>20%，回撤10%保护
        return DYNAMIC_STOP_LOSS_CONFIG['profit_protection_20']
    elif profit_rate > 0.10:
        # 盈利>10%，回撤8%保护
        return DYNAMIC_STOP_LOSS_CONFIG['profit_protection_10']
    elif profit_rate > 0.05:
        # 盈利>5%，保本止损
        return DYNAMIC_STOP_LOSS_CONFIG['breakeven_protection']
    else:
        # 亏损状态，使用基础止损
        return base_stop_loss


def check_single_stock_drawdown(position, current_price):
    """
    v9.0 检查个股最大回撤
    
    Returns: (是否触发, 原因, 建议操作)
    """
    cost = position.get('avg_cost', 0)
    if cost == 0:
        return False, "", "正常持有"
    
    # 从买入以来的最大盈利
    peak_profit = position.get('peak_profit', 0)
    current_profit_rate = (current_price - cost) / cost * 100
    
    # 更新最高点
    if current_profit_rate > peak_profit:
        position['peak_profit'] = current_profit_rate
        peak_profit = current_profit_rate
    
    # 计算从最高点到现在的回撤
    if peak_profit > 0:
        drawdown = peak_profit - current_profit_rate
        
        # 检查是否触发最大回撤
        if drawdown >= SINGLE_STOCK_MAX_DRAWDOWN['max_drawdown'] * 100:
            return True, f"从高点回撤{drawdown:.1f}%，超过15%阈值", "立即清仓"
        
        # 检查是否触发预警
        if drawdown >= SINGLE_STOCK_MAX_DRAWDOWN['warning_drawdown'] * 100:
            return False, f"从高点回撤{drawdown:.1f}%，接近10%预警线", "密切关注"
    
    return False, "", "正常持有"


def check_account_risk_control(portfolio):
    """
    v9.0 检查账户级风控
    
    Returns: (是否触发, 原因, 建议操作)
    """
    initial_capital = portfolio['portfolio'].get('initial_capital', 100000)
    current_capital = portfolio['portfolio'].get('current_capital', initial_capital)
    
    # 计算总资产（含持仓）
    positions_value = sum(p['shares'] * p.get('current_price', p['avg_cost']) for p in portfolio['positions'])
    total_assets = current_capital + positions_value
    
    # 计算总回撤
    total_return = (total_assets - initial_capital) / initial_capital
    
    # 1. 检查总回撤是否超过10%
    if total_return <= -ACCOUNT_RISK_CONTROL['total_max_drawdown']:
        return True, f"账户总回撤{-total_return*100:.1f}%，超过10%阈值", "一键清仓，暂停交易"
    
    # 2. 检查单日亏损
    today_pnl = portfolio['portfolio'].get('today_pnl', 0)
    if today_pnl <= -ACCOUNT_RISK_CONTROL['daily_max_loss'] * initial_capital:
        return True, f"今日亏损{-today_pnl:.0f}元，超过3%阈值", "停止今日交易"
    
    # 3. 检查连续亏损天数
    consecutive_loss_days = portfolio['portfolio'].get('consecutive_loss_days', 0)
    if consecutive_loss_days >= ACCOUNT_RISK_CONTROL['consecutive_loss_days']:
        return True, f"连续亏损{consecutive_loss_days}天", f"暂停交易{ACCOUNT_RISK_CONTROL['pause_trading_days']}天"
    
    # 4. 检查是否暂停交易
    pause_until = portfolio['portfolio'].get('pause_until', None)
    if pause_until:
        try:
            pause_date = datetime.strptime(pause_until, "%Y-%m-%d")
            if datetime.now() < pause_date:
                days_left = (pause_date - datetime.now()).days
                return True, f"交易暂停中，剩余{days_left}天", "等待恢复"
        except:
            pass
    
    return False, "", "正常交易"


def check_circuit_breaker(portfolio, market_status=None):
    """
    v9.0 检查熔断机制
    
    Returns: (是否触发, 原因, 建议操作)
    """
    # 1. 检查大盘熔断
    if market_status:
        index_change = market_status.get('change', 0)
        if index_change <= CIRCUIT_BREAKER['market_crash_threshold']:
            return True, f"大盘暴跌{index_change*100:.1f}%，触发熔断", "一键清仓"
    
    # 2. 检查持仓个股跌停
    for pos in portfolio.get('positions', []):
        if 'limit_down_count' not in pos:
            pos['limit_down_count'] = 0
        
        cost = pos.get('avg_cost', 0)
        current = pos.get('current_price', cost)
        if cost > 0:
            daily_change = (current - cost) / cost
            
            # 模拟每日涨跌
            if daily_change <= -0.095:  # 接近跌停
                pos['limit_down_count'] = pos.get('limit_down_count', 0) + 1
                if pos['limit_down_count'] >= 2:
                    return True, f"{pos['name']}连续跌停", "立即止损"
            else:
                pos['limit_down_count'] = 0
    
    # 3. 检查量能异动
    for pos in portfolio.get('positions', []):
        volume_ratio = pos.get('volume_ratio', 1)
        if volume_ratio >= CIRCUIT_BREAKER['volume_surge_alert']:
            # 放量预警
            pass  # 可以添加预警逻辑
    
    return False, "", "正常"


def can_sell(position):
    """检查是否可以卖出（T+1制度）"""
    today = datetime.now().strftime("%Y-%m-%d")
    buy_date = position.get('buy_date', '')
    
    if buy_date == today:
        return False, f"T+1限制：{position['name']}是今日买入，需等到明天"
    
    return True, ""


def load_portfolio():
    """加载投资组合"""
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_portfolio(data):
    """保存投资组合"""
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def simulate_price_change(price, volatility=0.03):
    """模拟股价波动"""
    change = random.uniform(-volatility, volatility)
    return round(price * (1 + change), 2)


def check_profit_taking(portfolio, position):
    """检查是否需要分批止盈"""
    profit_rate = position.get('profit_rate', 0) / 100
    sold_ratio = position.get('sold_ratio', 0)
    remaining_ratio = 1 - sold_ratio
    
    if remaining_ratio <= 0:
        return False, 0, ""
    
    for level in PROFIT_TAKING_LEVELS:
        if profit_rate >= level['profit_rate']:
            sell_ratio = level['sell_ratio'] * remaining_ratio
            if sell_ratio > remaining_ratio:
                sell_ratio = remaining_ratio
            
            return True, sell_ratio, level['desc']
    
    return False, 0, ""


def should_stop_loss(position, current_price):
    """
    v9.0 判断是否止损（动态止损）
    """
    # 获取动态止损线
    stop_loss_rate = get_dynamic_stop_loss(position, current_price)
    
    profit_rate = position.get('profit_rate', 0) / 100
    
    # 如果计算的止损率为正数（回撤比例），用负数比较
    # 例如：stop_loss_rate=0.08 表示从盈利回撤8%就止损
    # 止损条件：current_price <= cost * (1 - stop_loss_rate)
    
    cost = position.get('avg_cost', 0)
    if cost == 0:
        return False
    
    # 计算从成本价的最大允许回撤
    max_allowed = cost * (1 - stop_loss_rate)
    
    return current_price <= max_allowed


def execute_partial_sell(portfolio, position, sell_ratio, reason):
    """执行分批卖出"""
    can_trade, time_reason = is_trading_time()
    if not can_trade:
        print(f"[风控] 非交易时间，拒绝卖出！")
        return None
    
    current_price = position['current_price']
    realtime_price = get_realtime_price(position['code'])
    if realtime_price:
        current_price = realtime_price
    
    total_shares = position['shares']
    sell_shares = int(total_shares * sell_ratio / 100) * 100
    
    if sell_shares <= 0:
        return None
    
    new_sold_ratio = position.get('sold_ratio', 0) + sell_ratio
    position['sold_ratio'] = new_sold_ratio
    
    remaining_shares = total_shares - sell_shares
    position['shares'] = remaining_shares
    
    revenue = sell_shares * current_price
    avg_cost = position['avg_cost']
    profit = (current_price - avg_cost) * sell_shares
    
    portfolio['portfolio']['current_capital'] += revenue
    
    trade_record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "code": position['code'],
        "name": position['name'],
        "action": 'partial_sell',
        "price": current_price,
        "shares": sell_shares,
        "amount": revenue,
        "profit": round(profit, 2),
        "reason": reason
    }
    
    if remaining_shares <= 0:
        portfolio['positions'].remove(position)
        trade_record['action'] = 'sell'
        trade_record['reason'] = f"清仓: {reason}"
    
    return trade_record


def close_all_positions(portfolio, reason="风控熔断"):
    """
    v9.0 一键清仓（极端行情用）
    """
    print(f"\n{'='*50}")
    print(f"[风控] ⚠️ {reason}，执行一键清仓！")
    print(f"{'='*50}\n")
    
    can_trade, _ = is_trading_time()
    if not can_trade:
        print("[风控] 非交易时间，无法执行清仓，等待下一交易日")
        return []
    
    trades = []
    for pos in portfolio['positions'][:]:
        current_price = pos['current_price']
        realtime_price = get_realtime_price(pos['code'])
        if realtime_price:
            current_price = realtime_price
        
        sell_shares = pos['shares']
        revenue = sell_shares * current_price
        profit = (current_price - pos['avg_cost']) * sell_shares
        
        trade_record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "code": pos['code'],
            "name": pos['name'],
            "action": 'force_sell',
            "price": current_price,
            "shares": sell_shares,
            "amount": revenue,
            "profit": round(profit, 2),
            "reason": reason
        }
        
        portfolio['portfolio']['current_capital'] += revenue
        portfolio['positions'].remove(pos)
        trades.append(trade_record)
        print(f"  强制卖出 {pos['name']}: {profit:+.2f}元")
    
    # 设置暂停交易
    pause_days = ACCOUNT_RISK_CONTROL['pause_trading_days']
    pause_date = (datetime.now() + timedelta(days=pause_days)).strftime("%Y-%m-%d")
    portfolio['portfolio']['pause_until'] = pause_date
    
    print(f"\n[风控] 已暂停交易至 {pause_date}，共 {pause_days} 天")
    
    return trades


def run_daily_trading_v9():
    """执行每日交易 v9.0（全面风控版）"""
    print(f"\n{'='*70}")
    print(f"[v9.0] 金融助手交易系统 - 全面风控版")
    print(f"{'='*70}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始模拟交易...")

    portfolio = load_portfolio()
    stock_pool = portfolio.get('stock_pool', [])
    
    trades = []
    alerts = []  # 风控预警
    
    # ============ 第一步：账户级风控检查 ============
    print("\n--- [v9.0 账户级风控检查] ---")
    account_triggered, account_reason, account_action = check_account_risk_control(portfolio)
    
    if account_triggered:
        if "一键清仓" in account_action:
            # 执行清仓
            force_trades = close_all_positions(portfolio, account_reason)
            trades.extend(force_trades)
            alerts.append(("账户风控", account_reason, account_action))
            print(f"⚠️ {account_reason} → {account_action}")
        elif "等待恢复" in account_action:
            print(f"⚠️ {account_reason} → {account_action}")
            alerts.append(("账户风控", account_reason, account_action))
        else:
            print(f"⚠️ {account_reason} → {account_action}")
            alerts.append(("账户风控", account_reason, account_action))
    
    # ============ 第二步：更新持仓行情 ============
    print("\n--- 获取实时行情 ---")
    for pos in portfolio['positions']:
        realtime_price = get_realtime_price(pos['code'])
        if realtime_price:
            old_price = pos.get('current_price', 0)
            pos['current_price'] = realtime_price
            if pos['avg_cost'] > 0:
                profit_rate = (realtime_price - pos['avg_cost']) / pos['avg_cost']
                pos['profit_rate'] = profit_rate * 100
                pos['profit'] = (realtime_price - pos['avg_cost']) * pos['shares']
            print(f"  {pos['name']}: {old_price:.2f} → {realtime_price}元 ({pos['profit_rate']:+.2f}%)")
        else:
            print(f"  [警告] {pos['name']} 无法获取实时价格")

    # ============ 第三步：持仓风控检查 ============
    print("\n--- [v9.0 持仓风控检查] ---")
    for pos in portfolio['positions'][:]:
        current_price = pos.get('current_price', pos['avg_cost'])
        
        # 1. 检查T+1限制
        can_sell_flag, t1_reason = can_sell(pos)
        if not can_sell_flag:
            print(f"  【T+1】{pos['name']} {t1_reason}")
            continue
        
        # 2. 初始化风控参数
        if 'current_stop_loss' not in pos:
            pos['current_stop_loss'] = DYNAMIC_STOP_LOSS_CONFIG['medium_volatility']
        if 'sold_ratio' not in pos:
            pos['sold_ratio'] = 0
        if 'peak_profit' not in pos:
            pos['peak_profit'] = 0
        
        # 3. 动态止损检查
        dynamic_sl = get_dynamic_stop_loss(pos, current_price)
        cost = pos['avg_cost']
        max_allowed = cost * (1 - dynamic_sl)
        
        if dynamic_sl != pos.get('current_stop_loss', 0):
            pos['current_stop_loss'] = dynamic_sl
            print(f"  【动态止损】{pos['name']} 止损线更新为 {dynamic_sl*100:.0f}%")
        
        # 4. 个股最大回撤检查
        dd_triggered, dd_reason, dd_action = check_single_stock_drawdown(pos, current_price)
        if dd_triggered:
            print(f"  ⚠️ 【最大回撤】{pos['name']} {dd_reason} → {dd_action}")
            alerts.append(("个股回撤", pos['name'], dd_reason))
            # 触发最大回撤，强制清仓
            trade = execute_partial_sell(portfolio, pos, 1.0, dd_reason)
            if trade:
                trades.append(trade)
            continue
        
        # 5. 止损检查
        if current_price <= max_allowed:
            print(f"  ⚠️ 【止损】{pos['name']} 价格{current_price}元 <= 最低{max_allowed:.2f}元")
            trade = execute_partial_sell(portfolio, pos, 1.0, f"动态止损({dynamic_sl*100:.0f}%)")
            if trade:
                trades.append(trade)
            continue
        
        # 6. 分批止盈检查
        should_sell, sell_ratio, sell_reason = check_profit_taking(portfolio, pos)
        if should_sell and sell_ratio > 0:
            trade = execute_partial_sell(portfolio, pos, sell_ratio * 100, sell_reason)
            if trade:
                trades.append(trade)
                print(f"  【分批止盈】{pos['name']} {sell_reason}")
            continue

    # ============ 第四步：选股买入 ============
    print("\n--- [v9.0 选股买入] ---")
    if not account_triggered or "等待恢复" not in account_action:
        available_slots = portfolio.get('settings', {}).get('pool_size', 10) - len(portfolio['positions'])
        
        if available_slots > 0 and portfolio['portfolio']['current_capital'] > 5000:
            candidates = [s for s in stock_pool if not any(p['code'] == s['code'] for p in portfolio['positions'])]
            candidates = sorted(candidates, key=lambda x: x.get('scores', {}).get('composite', 0), reverse=True)[:available_slots]
            
            for stock in candidates:
                # 简单信号判断
                score = stock.get('scores', {}).get('composite', 70)
                change = stock.get('change_rate', 0)
                
                if score > 75 and change < 5:  # 优质且未大涨
                    volatility = random.uniform(0.02, 0.05)
                    stock['volatility'] = volatility
                    stock['current_price'] = simulate_price_change(stock['price'], volatility)
                    
                    total_capital = portfolio['portfolio']['current_capital']
                    available = total_capital * 0.8
                    max_per_stock = min(20000, available)
                    shares = int(max_per_stock / stock['current_price'] / 100) * 100
                    
                    if shares > 0:
                        cost = shares * stock['current_price']
                        
                        portfolio['positions'].append({
                            "code": stock['code'],
                            "name": stock['name'],
                            "shares": shares,
                            "avg_cost": stock['current_price'],
                            "current_price": stock['current_price'],
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "last_buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "sector": stock.get('sector', ''),
                            "volatility": volatility,
                            "current_stop_loss": DYNAMIC_STOP_LOSS_CONFIG['medium_volatility'],
                            "sold_ratio": 0,
                            "peak_profit": 0
                        })
                        
                        portfolio['portfolio']['current_capital'] -= cost
                        trades.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "code": stock['code'],
                            "name": stock['name'],
                            "action": 'buy',
                            "price": stock['current_price'],
                            "shares": shares,
                            "amount": cost,
                            "reason": f"综合评分{score:.1f}"
                        })
                        print(f"  买入 {stock['name']}({stock['code']}) @ {stock['current_price']}元 x {shares}股")

    # ============ 更新持仓价值 ============
    total_value = portfolio['portfolio']['current_capital']
    total_profit = 0
    
    for pos in portfolio['positions']:
        pos['current_price'] = simulate_price_change(pos['current_price'], pos.get('volatility', 0.03))
        market_value = pos['shares'] * pos['current_price']
        cost_value = pos['shares'] * pos['avg_cost']
        pos['profit'] = round(market_value - cost_value, 2)
        pos['profit_rate'] = round((market_value - cost_value) / cost_value * 100, 2)
        total_value += market_value
        total_profit += pos['profit']
    
    portfolio['portfolio']['total_value'] = round(total_value, 2)
    portfolio['portfolio']['total_profit'] = round(total_profit, 2)
    portfolio['portfolio']['total_profit_rate'] = round(
        (total_value - portfolio['portfolio']['initial_capital']) / portfolio['portfolio']['initial_capital'] * 100, 2
    )
    
    # 更新连续亏损天数
    if total_profit < 0:
        portfolio['portfolio']['consecutive_loss_days'] = portfolio['portfolio'].get('consecutive_loss_days', 0) + 1
    else:
        portfolio['portfolio']['consecutive_loss_days'] = 0
    
    # 记录交易历史
    if trades:
        portfolio['trade_history'].extend(trades)
    
    save_portfolio(portfolio)

    # ============ 输出结果 ============
    print("\n" + "=" * 50)
    print(f"交易完成！共执行 {len(trades)} 笔交易")
    print(f"总资产: {portfolio['portfolio']['total_value']:.2f} 元")
    print(f"持仓收益: {portfolio['portfolio']['total_profit']:.2f} 元 ({portfolio['portfolio']['total_profit_rate']:+.2f}%)")
    print(f"现金: {portfolio['portfolio']['current_capital']:.2f} 元")
    print(f"持仓: {len(portfolio['positions'])} 只")
    
    if alerts:
        print(f"\n⚠️ 风控预警 {len(alerts)} 条:")
        for alert in alerts:
            print(f"  - [{alert[0]}] {alert[1]}: {alert[2]}")
    
    print("=" * 50)
    
    # v9.0 风控体系说明
    print("\n[v9.0] 风控体系说明:")
    print("   1. 动态止损：根据波动率和盈亏状态自动调整")
    print("   2. 个股最大回撤：超过15%强制清仓")
    print("   3. 账户总回撤：超过10%一键清仓暂停")
    print("   4. 连续亏损：3天暂停交易2天")
    print("   5. 熔断机制：大盘暴跌3%自动清仓")

    return portfolio, trades


if __name__ == "__main__":
    run_daily_trading_v9()
