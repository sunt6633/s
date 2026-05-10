# -*- coding: utf-8 -*-
"""
模拟交易引擎 v8.0 - 金融助手
执行买卖操作，管理仓位，计算收益

【进化v8.0 - 梁文锋量化思想 + 智能风控体系】
核心理念："用科学的方法建立系统性的投资优势"

一、认知基石
- 决策方式：用数量化方法而非凭感觉
- "一定有办法对价格建模"

二、三大核心策略
1. 高频量化套利（基础稳利）
2. 趋势跟踪（放大收益）
3. 风险对冲（控回撤）

三、因子配置（梁文锋标准）
- 量价因子：40%
- 基本面因子：30%
- 另类数据：20%
- 市场情绪：10%

四、风控体系（v8.0新增）
- 熔断机制：单日跌5%/连续3天下跌/极端行情一键清仓
- 智能仓位：根据大盘环境动态调整（牛8满/震荡8成/熊5成/暴跌2成）
- 交易信号：六档信号（止损/强烈买入/买入/持有/观望/卖出）
- 风险预算：单日最大亏损3%/单周8%暂停
- 量价异动：量比2倍预警/缩量30%预警

升级日期：2026-04-15
"""

import json
import os
import random
import requests
from datetime import datetime, time
from copy import deepcopy
from qveris_api_manager import get_current_api_key, switch_api, get_all_apis, BASE_URL

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")

# QVeris API 配置（从管理器获取）
QVERIS_BASE_URL = BASE_URL

# 缓存搜索ID，避免每次都搜索
_cached_search_id = None
_stock_tool_id = "caidazi.get_real_time_record.execute.v1.7a43f96e"

def _get_search_id():
    """获取并缓存搜索ID"""
    global _cached_search_id
    if _cached_search_id:
        return _cached_search_id
    
    try:
        headers = {
            'Authorization': f'Bearer {get_current_api_key()}',
            'Content-Type': 'application/json'
        }
        data = {'query': 'A股股票实时价格查询', 'limit': 1}
        response = requests.post(f'{QVERIS_BASE_URL}/search', headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            _cached_search_id = result.get('search_id')
            return _cached_search_id
    except Exception as e:
        print(f"[警告] 获取搜索ID失败: {e}")
    return None

def get_realtime_price(code):
    """
    【重要】获取股票实时价格
    执行交易前必须调用此函数获取最新价格
    
    Args:
        code: 股票代码（如 "601318"）
    Returns:
        float: 最新价格，失败返回None
    """
    # 转换代码格式
    symbol = code
    if not symbol.endswith(('.SH', '.SZ')):
        if symbol.startswith('6'):
            symbol = f'{symbol}.SH'
        elif symbol.startswith(('0', '3')):
            symbol = f'{symbol}.SZ'
    
    search_id = _get_search_id()
    if not search_id:
        return None
    
    try:
        headers = {
            'Authorization': f'Bearer {get_current_api_key()}',
            'Content-Type': 'application/json'
        }
        call_data = {
            'search_id': search_id,
            'parameters': {'symbol': symbol},
            'max_response_size': 20480
        }
        
        response = requests.post(
            f'{QVERIS_BASE_URL}/tools/execute?tool_id={_stock_tool_id}',
            headers=headers,
            json=call_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('result', {}).get('data', {}).get('result', '')
            
            # 解析表格数据，提取最新价
            # 格式: | 股票代码 | 股票名称 | ... | 最新价（元） | ...
            lines = data.split('\n')
            for line in lines:
                if symbol.replace('.SH', '.SH').replace('.SZ', '.SZ') in line and '|' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    # 股票代码在parts[0]，最新价在parts[3]
                    if len(parts) >= 4:
                        try:
                            price = float(parts[3])
                            return price
                        except:
                            pass
    except Exception as e:
        print(f"[警告] 获取{symbol}实时价格失败: {e}")
    
    return None

# ============ A股交易时间定义 ============
TRADING_MORNING_START = time(9, 30)   # 上午开盘
TRADING_MORNING_END = time(11, 30)   # 上午休市
TRADING_AFTERNOON_START = time(13, 0) # 下午开盘
TRADING_AFTERNOON_END = time(15, 0)   # 下午休市

def is_trading_time():
    """
    检查当前是否在A股交易时间内
    
    A股交易时间：
    - 上午：9:30 - 11:30
    - 下午：13:00 - 15:00
    - 收盘后、周末、节假日都不能交易
    
    返回: (bool, str) - (是否在交易时间, 原因说明)
    """
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()  # 0=周一, 6=周日
    
    # 周末不能交易
    if weekday >= 5:
        return False, f"周末不能交易（今天是{'周' + str(weekday - 5) if weekday == 6 else '六'}）"
    
    # 上午交易时间
    if TRADING_MORNING_START <= current_time <= TRADING_MORNING_END:
        return True, f"上午交易时间 9:30-11:30"
    
    # 下午交易时间
    if TRADING_AFTERNOON_START <= current_time <= TRADING_AFTERNOON_END:
        return True, f"下午交易时间 13:00-15:00"
    
    # 不在交易时间内
    if current_time < TRADING_MORNING_START:
        return False, f"还没开盘（9:30才开）"
    elif current_time > TRADING_AFTERNOON_END:
        return False, f"已收盘（15:00已过）"
    elif TRADING_MORNING_END < current_time < TRADING_AFTERNOON_START:
        return False, f"中午休市（11:30-13:00）"
    
    return False, "非交易时间"

# ============ v8.0 新增：智能风控与仓位管理 ============
# 进化内容：
# 1. 智能仓位管理 - 根据大盘/情绪动态调整
# 2. 交易信号系统 - 明确买入/持有/卖出/观望信号
# 3. 风险预算控制 - 每日最大亏损上限
# 4. 量价异动监控 - 成交量异常预警

# 【v8.0 智能仓位管理】
# 根据大盘环境动态调整仓位
POSITION_BY_MARKET = {
    'bull': 1.0,      # 牛市：满仓
    'normal': 0.8,    # 震荡：8成仓
    'bear': 0.5,      # 熊市：5成仓
    'crash': 0.2,     # 暴跌：2成仓或空仓
}

# 【v8.0 风险预算控制】
# 每日最大亏损控制
DAILY_RISK_BUDGET = {
    'max_daily_loss': 0.03,      # 单日最大亏损3%即止损
    'max_weekly_loss': 0.08,     # 单周最大亏损8%暂停交易
    'max_positions': 5,          # 最多持仓5只
    'min_profit_protect': 0.02,  # 盈利超2%设置保本止损
}

# 【v8.0 量价异动监控】
VOLUME_ALERT = {
    'volume_surge': 2.0,         # 成交量超过均量2倍预警
    'volume_shrink': 0.3,        # 成交量低于均量30%预警
    'price_surge': 0.05,         # 单日涨幅超5%预警
    'price_crash': -0.05,        # 单日跌幅超5%预警
}

# 【v8.0 交易信号定义】
TRADE_SIGNALS = {
    'STRONG_BUY': {'action': 'buy', 'priority': 1, 'desc': '强烈买入'},
    'BUY': {'action': 'buy', 'priority': 2, 'desc': '建议买入'},
    'HOLD': {'action': 'hold', 'priority': 3, 'desc': '持有观望'},
    'WATCH': {'action': 'watch', 'priority': 4, 'desc': '密切关注'},
    'SELL': {'action': 'sell', 'priority': 5, 'desc': '建议卖出'},
    'STOP_LOSS': {'action': 'stop_loss', 'priority': 0, 'desc': '止损出局'},
}

# ============ v7.0 新增：梁文锋式严格风控 ============
# 基于梁文锋三大核心理念：
# 1. 高频量化套利（基础稳利）
# 2. 趋势跟踪（放大收益）
# 3. 风险对冲（控回撤）

# 【熔断机制】- 梁文锋核心风控
FUSION_CONFIG = {
    # 单票仓位上限（总资金的10%）
    'max_single_position_ratio': 0.10,
    
    # 单日跌幅熔断（触发即止损）
    'daily_loss_fusion': 0.05,  # 单日跌5%触发熔断止损
    
    # 连续下跌熔断（3连跌强制止损）
    'consecutive_loss_days': 3,
    'consecutive_loss_fusion': 0.03,  # 连续3天累计跌3%触发熔断
    
    # 极端行情熔断（大盘暴跌时一键清仓）
    'market_crash_threshold': 0.03,  # 大盘单日跌3%视为极端行情
    'market_crash_action': 'close_all',  # 动作：清仓
    
    # 盈利回撤保护
    'profit_hwm_protection': 0.10,  # 从最高盈利回撤10%即止损
}

# 仓位分配策略
POSITION_ALLOCATION = {
    'high_freq': 0.30,     # 高频套利策略：30%资金
    'trend': 0.50,          # 趋势跟踪策略：50%资金
    'hedge': 0.20,          # 对冲策略：20%资金（预留）
}

# 趋势跟踪止损
TREND_STOP_LOSS = {
    'consecutive_down_2': 0.04,  # 连续2天下跌，止损4%
    'consecutive_down_3': 0.02,  # 连续3天下跌，止损2%
    'single_day_loss_3': 0.03,   # 单日跌3%，止损3%
}

# ============ v6.0 原有配置 ============
# 分批止盈策略（v6.0 优化版）
PROFIT_TAKING_LEVELS = [
    {'profit_rate': 0.08, 'sell_ratio': 0.25, 'stop_loss': 0.03},   # 盈利8%，卖25%，止损上调到3%
    {'profit_rate': 0.15, 'sell_ratio': 0.30, 'stop_loss': 0.08},   # 盈利15%，累计卖55%，止损上调到8%
    {'profit_rate': 0.25, 'sell_ratio': 0.30, 'stop_loss': 0.15},   # 盈利25%，累计卖85%，止损上调到15%
    {'profit_rate': 0.40, 'sell_ratio': 0.15, 'stop_loss': 0.20},  # 盈利40%，清仓
]

# 初始止损线
INITIAL_STOP_LOSS = 0.08  # 8%

# 波动率调整阈值
VOLATILITY_THRESHOLD_HIGH = 0.05   # 高波动阈值
VOLATILITY_THRESHOLD_LOW = 0.02    # 低波动阈值
HIGH_VOL_POSITION_MULTIPLIER = 0.7  # 高波动仓位打7折
LOW_VOL_POSITION_MULTIPLIER = 1.2   # 低波动仓位加2成

# v6.0 动态止损因子
DYNAMIC_STOP_LOSS_FACTOR = {
    'profit_<5%': {'stop_loss': 0.08, 'description': '盈利<5%，止损8%'},
    'profit_5-10%': {'stop_loss': 0.03, 'description': '盈利5-10%，止损3%'},
    'profit_10-20%': {'stop_loss': 0.00, 'description': '盈利10-20%，保本'},
    'profit_20-30%': {'stop_loss': -0.08, 'description': '盈利20-30%，回撤8%保护'},
    'profit_>30%': {'stop_loss': -0.10, 'description': '盈利>30%，回撤10%保护'},
}

# 波动率调整
VOLATILITY_THRESHOLD_HIGH = 0.05   # 高波动阈值
VOLATILITY_THRESHOLD_LOW = 0.02    # 低波动阈值
HIGH_VOL_POSITION_MULTIPLIER = 0.7  # 高波动仓位打7折
LOW_VOL_POSITION_MULTIPLIER = 1.2   # 低波动仓位加2成

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

# ============ v7.0 新增：熔断机制 ============
def check_fusion_stop(position, market_status=None):
    """
    【v7.0 梁文锋式熔断机制】
    
    检查是否触发熔断止损
    
    返回: (是否触发, 触发原因, 建议操作)
    """
    fusion = FUSION_CONFIG
    trend = TREND_STOP_LOSS
    
    # 1. 检查单日跌幅熔断
    daily_change = position.get('daily_change', 0)
    if daily_change <= -fusion['daily_loss_fusion']:
        return True, f"单日跌幅{daily_change*100:.1f}%触发熔断", "立即止损"
    
    # 2. 检查连续下跌熔断
    consecutive_down = position.get('consecutive_down_days', 0)
    if consecutive_down >= fusion['consecutive_loss_days']:
        # 计算累计跌幅
        cost = position.get('avg_cost', 0)
        current = position.get('current_price', 0)
        if cost > 0:
            total_loss = (cost - current) / cost
            if total_loss >= fusion['consecutive_loss_fusion']:
                return True, f"连续{consecutive_down}天下跌触发熔断", "立即止损"
    
    # 3. 检查极端行情熔断（大盘暴跌）
    if market_status and market_status.get('is_crash', False):
        return True, f"大盘暴跌{market_status.get('change', 0)*100:.1f}%，极端行情熔断", "一键清仓"
    
    # 4. 检查趋势跟踪止损
    if consecutive_down >= 3:
        return True, f"连续3天下跌，趋势破坏", "止损出局"
    elif consecutive_down >= 2:
        # 连续2天下跌，设置预警
        return False, f"连续2天下跌，密切关注", "密切监控"
    
    # 5. 检查盈利回撤保护（从高点回撤超过阈值）
    profit_hwm = position.get('profit_high_water_mark', 0)  # 盈利高点
    current_profit = position.get('profit_rate', 0)
    if profit_hwm > 0 and current_profit < (profit_hwm - fusion['profit_hwm_protection']):
        return True, f"盈利从{profit_hwm:.1f}%回撤超过10%，保护利润", "止盈出局"
    
    return False, "未触发熔断", "正常持有"

def generate_trade_signal(stock, day_change_history=[]):
    """
    【v8.0 智能交易信号系统】

    返回六种信号：STRONG_BUY / BUY / HOLD / WATCH / SELL / STOP_LOSS

    信号生成逻辑（梁文锋量化思想）：
    1. 严格风控优先 - 触发止损立即出局
    2. 多因子验证 - 量价+基本面+情绪综合判断
    3. 趋势跟随 - 不抄底不摸顶
    4. 机器执行 - 信号即决策，不犹豫
    """
    change_rate = stock.get('change_rate', 0)
    score = stock.get('score', 70)
    volume_ratio = stock.get('volume_ratio', 1.0)  # 量比

    # 获取技术指标
    tech = stock.get('tech', {})
    kdj = tech.get('kdj', {})
    rsi = tech.get('rsi', 50)
    macd = tech.get('macd', {})

    k = kdj.get('k', 50)
    d = kdj.get('d', 50)
    j = kdj.get('j', 50)
    macd_value = macd.get('value', 0)
    macd_signal = macd.get('signal', 0)

    # ===== 第一层：止损信号（最高优先级） =====
    # 触发任何止损条件，立即出局
    if change_rate <= -VOLUME_ALERT['price_crash']:
        return 'STOP_LOSS'  # 暴跌5%+，止损出局

    # ===== 第二层：卖出信号 =====
    # RSI严重超买
    if rsi > 80:
        return 'SELL'
    # 涨幅过大不追高
    if change_rate > 6:
        return 'SELL'
    # 基本面恶化
    if score < 60:
        return 'SELL'

    # ===== 第三层：观望信号 =====
    # KDJ空头（趋势向下）
    if k < d and k < 50:
        return 'WATCH'
    # RSI偏高
    if rsi > 70:
        return 'WATCH'
    # 涨幅偏大
    if change_rate > 4:
        return 'WATCH'
    # 量能萎缩（出货迹象）
    if volume_ratio < VOLUME_ALERT['volume_shrink']:
        return 'WATCH'

    # ===== 第四层：强烈买入信号 =====
    # 同时满足：超跌 + 优质 + KDJ金叉 + 量能放大
    if (change_rate < -3 and score > 80 and
        k > d and k < 40 and volume_ratio > 1.5):
        return 'STRONG_BUY'

    # ===== 第五层：买入信号 =====
    # 跌多了 + 基本面好 + 趋势向上
    if change_rate < -2 and score > 75 and k > d:
        return 'BUY'

    # ===== 第六层：持有 =====
    return 'HOLD'


def get_market_position(index_change):
    """
    【v8.0 智能仓位管理】

    根据大盘环境动态调整仓位

    Args:
        index_change: 大盘涨跌幅（如 0.02 表示涨2%）
    Returns:
        (仓位比例, 市场状态描述)
    """
    if index_change >= 0.02:
        return POSITION_BY_MARKET['bull'], "牛市行情，可加重仓"
    elif index_change >= -0.01:
        return POSITION_BY_MARKET['normal'], "震荡行情，保持8成仓"
    elif index_change >= -0.03:
        return POSITION_BY_MARKET['bear'], "偏弱行情，控制5成仓"
    else:
        return POSITION_BY_MARKET['crash'], "暴跌行情，清仓或空仓"


def check_volume_alert(volume_ratio, change_rate):
    """
    【v8.0 量价异动监控】

    检查量价异动，预警潜在风险或机会
    """
    alerts = []

    # 放量上涨（健康）
    if volume_ratio >= VOLUME_ALERT['volume_surge'] and change_rate > 0:
        alerts.append(("量能放大", "主力介入，看涨"))

    # 放量下跌（危险）
    if volume_ratio >= VOLUME_ALERT['volume_surge'] and change_rate < -2:
        alerts.append(("放量下跌", "警惕！可能继续下杀"))

    # 缩量上涨（虚涨）
    if volume_ratio < VOLUME_ALERT['volume_shrink'] and change_rate > 2:
        alerts.append(("缩量上涨", "上涨乏力，警惕回调"))

    # 缩量下跌（观望）
    if volume_ratio < VOLUME_ALERT['volume_shrink'] and change_rate < -2:
        alerts.append(("缩量下跌", "抛压不重，暂观"))

    return alerts


def get_signal_priority(signal):
    """
    【v8.0 信号优先级】

    用于排序多只股票的信号优先级
    """
    signal_priorities = {
        'STOP_LOSS': 0,    # 最高：必须止损
        'STRONG_BUY': 1,   # 其次：强烈买入
        'BUY': 2,          # 买入
        'HOLD': 3,         # 持有
        'WATCH': 4,        # 观望
        'SELL': 5,         # 卖出
    }
    return signal_priorities.get(signal, 99)

def can_sell(position):
    """
    检查是否可以卖出（A股T+1制度）
    当天买入的股票当天不能卖出
    """
    today = datetime.now().strftime("%Y-%m-%d")
    buy_date = position.get('buy_date', '')
    
    if buy_date == today:
        return False, f"T+1限制：{position['name']}是今日买入，需等到明天才能卖出"
    
    return True, ""

def execute_trade(portfolio, stock, action, current_price):
    """执行交易（仅在A股交易时间内有效）"""
    
    # 【重要修复】严格检查交易时间
    can_trade, time_reason = is_trading_time()
    if not can_trade:
        print(f"[系统] [警告] 非交易时间，拒绝执行！原因：{time_reason}")
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "code": stock['code'],
            "name": stock['name'],
            "action": action,
            "price": current_price,
            "shares": 0,
            "amount": 0,
            "reason": f"非交易时间：{time_reason}"
        }
    
    # 【重要修复】执行前获取实时价格
    realtime_price = get_realtime_price(stock['code'])
    if realtime_price:
        current_price = realtime_price
        print(f"[实时价格] {stock['name']}: {current_price}元 ({datetime.now().strftime('%H:%M:%S')})")
    else:
        print(f"[警告] 无法获取实时价格，使用参考价: {current_price}元")
    
    trade_record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "code": stock['code'],
        "name": stock['name'],
        "action": action,
        "price": current_price,
        "shares": 0,
        "amount": 0,
        "reason": ""
    }

    if action == 'buy':
        total_capital = portfolio['portfolio']['current_capital']
        
        # 计算可用资金（保留20%现金）
        available = total_capital * 0.8
        if available < 1000:
            trade_record['reason'] = "资金不足"
            return trade_record

        # 检查是否已有持仓
        existing = next((p for p in portfolio['positions'] if p['code'] == stock['code']), None)
        
        # 如果已有持仓，计算总股数（加仓）
        if existing:
            # 今日已买过，不能再加仓（实际规则是今日买的不能卖，但可以加仓）
            # 为简化模拟，限制同一股票每日只操作一次
            today = datetime.now().strftime("%Y-%m-%d")
            if existing.get('last_buy_date') == today:
                trade_record['reason'] = f"今日已买入{existing['name']}，明日再操作"
                return trade_record
            
            # 检查单票仓位上限（梁文锋核心理念：单票不超过总资金10%）
            existing_value = existing['shares'] * existing['current_price']
            if existing_value >= total_capital * FUSION_CONFIG['max_single_position_ratio']:
                trade_record['reason'] = f"单票仓位已达上限({FUSION_CONFIG['max_single_position_ratio']*100:.0f}%)，不再加仓"
                return trade_record
        
        # 【v7.0 梁文锋式仓位管理】
        # 单票仓位上限 = 总资金 * 10%
        max_single_position = total_capital * FUSION_CONFIG['max_single_position_ratio']
        
        # 如果已有持仓，加上现有价值
        if existing:
            existing_value = existing['shares'] * existing['current_price']
            remaining_quota = max_single_position - existing_value
            max_per_stock = min(available, remaining_quota)
        else:
            max_per_stock = min(available, max_single_position)
        
        # 每只股票最多投入单票仓位上限
        max_per_stock = min(max_per_stock, 20000)
        shares = int(max_per_stock / current_price / 100) * 100  # 整手

        if shares > 0:
            cost = shares * current_price
            trade_record['shares'] = shares
            trade_record['amount'] = cost
            trade_record['reason'] = f"买入{shares}股，成本{cost}元"

            # 更新持仓
            if existing:
                total_cost = existing['avg_cost'] * existing['shares'] + cost
                total_shares = existing['shares'] + shares
                existing['avg_cost'] = round(total_cost / total_shares, 2)
                existing['shares'] = total_shares
                existing['current_price'] = current_price
                existing['last_buy_date'] = datetime.now().strftime("%Y-%m-%d")
            else:
                portfolio['positions'].append({
                    "code": stock['code'],
                    "name": stock['name'],
                    "shares": shares,
                    "avg_cost": current_price,
                    "current_price": current_price,
                    "buy_date": datetime.now().strftime("%Y-%m-%d"),
                    "last_buy_date": datetime.now().strftime("%Y-%m-%d"),
                    "sector": stock.get('sector', '')
                })

            portfolio['portfolio']['current_capital'] -= cost
        else:
            trade_record['reason'] = "资金不足以买入整手"

    elif action == 'sell':
        # 查找持仓
        position = next((p for p in portfolio['positions'] if p['code'] == stock['code']), None)
        if position:
            # 检查T+1限制
            can_sell_flag, t1_reason = can_sell(position)
            if not can_sell_flag:
                trade_record['reason'] = t1_reason
                return trade_record
            
            sell_shares = position['shares']
            revenue = sell_shares * current_price
            profit = (current_price - position['avg_cost']) * sell_shares

            trade_record['shares'] = sell_shares
            trade_record['amount'] = revenue
            trade_record['profit'] = round(profit, 2)
            trade_record['reason'] = f"卖出{sell_shares}股，盈利{profit:.2f}元"

            # 更新资金和持仓
            portfolio['portfolio']['current_capital'] += revenue
            portfolio['positions'].remove(position)
        else:
            trade_record['reason'] = "无持仓"

    return trade_record

def update_positions_value(portfolio):
    """更新持仓市值"""
    total_value = portfolio['portfolio']['current_capital']
    total_profit = 0

    for pos in portfolio['positions']:
        # 模拟价格变动
        volatility = pos.get('volatility', 0.03)  # 默认波动率3%
        pos['current_price'] = simulate_price_change(pos['current_price'], volatility)
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

    return portfolio


# ============ v5.0 新增：智能止盈止损 ============

def check_profit_taking(portfolio, position):
    """
    v5.0 检查是否需要分批止盈
    返回: (是否止盈, 卖出比例, 原因)
    """
    profit_rate = position.get('profit_rate', 0) / 100  # 转换为小数
    
    # 获取已卖出比例
    sold_ratio = position.get('sold_ratio', 0)
    remaining_ratio = 1 - sold_ratio
    
    if remaining_ratio <= 0:
        return False, 0, ""
    
    # 遍历止盈层级
    for level in PROFIT_TAKING_LEVELS:
        if profit_rate >= level['profit_rate']:
            # 可以止盈
            sell_ratio = level['sell_ratio'] * remaining_ratio  # 按剩余比例计算
            if sell_ratio > remaining_ratio:
                sell_ratio = remaining_ratio
            
            return True, sell_ratio, f"盈利{profit_rate*100:.1f}%，止盈卖出{level['sell_ratio']*100:.0f}%(剩余的{sell_ratio*100:.0f}%)"
    
    return False, 0, ""


def check_trailing_stop_loss(position):
    """
    v6.0 动态移动止损
    基于梁文锋理念：严格风控，机器执行

    动态调整逻辑：
    - 盈利<5%：止损8%
    - 盈利5-10%：止损3%
    - 盈利10-20%：保本
    - 盈利20-30%：回撤保护（止损移到盈利-8%）
    - 盈利>30%：强保护（止损移到盈利-10%）
    """
    profit_rate = position.get('profit_rate', 0) / 100
    current_stop_loss = position.get('current_stop_loss', INITIAL_STOP_LOSS)

    # 移动止损逻辑（v6.0 优化）
    new_stop_loss = current_stop_loss

    if profit_rate >= 0.30:  # 盈利>30%，止损移到盈利-10%
        new_stop_loss = 0.10
        desc = "盈利>30%，回撤保护"
    elif profit_rate >= 0.20:  # 盈利>20%，止损移到盈利-8%
        new_stop_loss = 0.08
        desc = "盈利>20%，回撤保护"
    elif profit_rate >= 0.10:  # 盈利>10%，止损移到保本
        new_stop_loss = 0.00
        desc = "盈利>10%，保本止损"
    elif profit_rate >= 0.05:  # 盈利>5%，止损3%
        new_stop_loss = 0.03
        desc = "盈利>5%，止损3%"
    else:
        new_stop_loss = INITIAL_STOP_LOSS  # 恢复初始止损8%
        desc = "盈利不足，保卫本金"

    if new_stop_loss != current_stop_loss:
        position['current_stop_loss'] = new_stop_loss
        return True, new_stop_loss
    
    return False, current_stop_loss


def should_stop_loss(position):
    """
    v5.0 判断是否止损（考虑移动止损）
    """
    profit_rate = position.get('profit_rate', 0) / 100
    stop_loss = position.get('current_stop_loss', INITIAL_STOP_LOSS)
    
    return profit_rate <= -stop_loss


def calculate_position_size(portfolio, stock, max_per_stock=20000):
    """
    v5.0 计算仓位大小（考虑波动率调整）
    """
    # 获取波动率
    volatility = stock.get('volatility', 0.03)
    
    # 波动率调整
    if volatility > VOLATILITY_THRESHOLD_HIGH:
        max_per_stock *= HIGH_VOL_POSITION_MULTIPLIER
    elif volatility < VOLATILITY_THRESHOLD_LOW:
        max_per_stock *= LOW_VOL_POSITION_MULTIPLIER
    
    # 保留20%现金
    available = portfolio['portfolio']['current_capital'] * 0.8
    actual_max = min(available, max_per_stock)
    
    return int(actual_max / stock['current_price'] / 100) * 100


def execute_partial_sell(portfolio, position, sell_ratio, reason):
    """
    v5.0 执行分批卖出
    """
    # 【重要】严格检查交易时间
    can_trade, time_reason = is_trading_time()
    if not can_trade:
        print(f"[系统] [警告] 非交易时间，拒绝卖出！原因：{time_reason}")
        return None
    
    # 【重要】执行前获取实时价格
    current_price = position['current_price']
    realtime_price = get_realtime_price(position['code'])
    if realtime_price:
        current_price = realtime_price
        print(f"[实时价格] {position['name']}: {current_price}元 ({datetime.now().strftime('%H:%M:%S')})")
    else:
        print(f"[警告] 无法获取实时价格，使用参考价: {current_price}元")
    
    total_shares = position['shares']
    sell_shares = int(total_shares * sell_ratio / 100) * 100  # 整手
    
    if sell_shares <= 0:
        return None
    
    # 计算已卖出比例
    new_sold_ratio = position.get('sold_ratio', 0) + sell_ratio
    position['sold_ratio'] = new_sold_ratio
    
    # 更新持仓
    remaining_shares = total_shares - sell_shares
    position['shares'] = remaining_shares
    
    # 计算收益
    revenue = sell_shares * current_price
    avg_cost = position['avg_cost']
    profit = (current_price - avg_cost) * sell_shares
    
    # 更新资金
    portfolio['portfolio']['current_capital'] += revenue
    
    # 交易记录
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
    
    # 如果全部卖出，从持仓中移除
    if remaining_shares <= 0:
        portfolio['positions'].remove(position)
        trade_record['action'] = 'sell'
        trade_record['reason'] = f"清仓: {reason}"
    
    return trade_record

def run_daily_trading():
    """执行每日交易 v5.0"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始模拟交易...")

    portfolio = load_portfolio()
    stock_pool = portfolio.get('stock_pool', [])
    settings = portfolio.get('settings', {})

    trades = []

    # ============ v5.0: 先更新持仓的实时价格 ============
    print("\n--- 获取实时行情 ---")
    for pos in portfolio['positions']:
        realtime_price = get_realtime_price(pos['code'])
        if realtime_price:
            old_price = pos.get('current_price', 0)
            pos['current_price'] = realtime_price
            # 更新盈亏率
            if pos['avg_cost'] > 0:
                profit_rate = (realtime_price - pos['avg_cost']) / pos['avg_cost']
                pos['profit_rate'] = profit_rate
                profit = (realtime_price - pos['avg_cost']) * pos['shares']
                pos['profit'] = round(profit, 2)
            print(f"  {pos['name']}: {old_price:.2f} → {realtime_price}元 ({pos['profit_rate']*100:+.2f}%)")
        else:
            print(f"  [警告] {pos['name']} 无法获取实时价格")

    # ============ v5.0: 检查持仓 - 止盈止损 ============
    print("\n--- 检查持仓 [v5.0止盈止损] ---")
    for pos in portfolio['positions'][:]:
        # 检查T+1限制
        can_sell_flag, _ = can_sell(pos)
        
        if not can_sell_flag:
            print(f"【T+1限制】{pos['name']}是今日买入，需等到明天才能操作")
            continue
        
        # 初始化止损线（如果没有的话）
        if 'current_stop_loss' not in pos:
            pos['current_stop_loss'] = INITIAL_STOP_LOSS
        if 'sold_ratio' not in pos:
            pos['sold_ratio'] = 0
        
        # 检查移动止损
        moved, new_sl = check_trailing_stop_loss(pos)
        if moved:
            print(f"【移动止损】{pos['name']} 止损线上调至 {new_sl*100:.0f}%")
        
        # 检查分批止盈
        should_sell, sell_ratio, sell_reason = check_profit_taking(portfolio, pos)
        if should_sell and sell_ratio > 0:
            trade = execute_partial_sell(portfolio, pos, sell_ratio, sell_reason)
            if trade:
                trades.append(trade)
                print(f"【分批止盈】{pos['name']} {sell_reason}")
            continue  # 止盈后不检查止损
        
        # 检查止损
        if should_stop_loss(pos):
            trade = execute_partial_sell(portfolio, pos, 1.0, f"止损(亏损{pos['profit_rate']:.1f}%)")
            if trade:
                trades.append(trade)
                print(f"【止损】{pos['name']} 亏损{pos['profit_rate']:.1f}%")

    # ============ v5.0: 根据股票池选股买入 ============
    print("\n--- 选股买入 [v5.0仓位管理] ---")
    available_slots = settings.get('pool_size', 10) - len(portfolio['positions'])

    if available_slots > 0 and portfolio['portfolio']['current_capital'] > 5000:
        # 使用v5.0的综合评分
        candidates = [s for s in stock_pool if not any(p['code'] == s['code'] for p in portfolio['positions'])]
        candidates = sorted(candidates, key=lambda x: x.get('scores', {}).get('composite', 0), reverse=True)[:available_slots]

        for stock in candidates:
            action = generate_trade_signal(stock)
            if action == 'buy':
                # v5.0: 波动率调整仓位
                volatility = random.uniform(0.02, 0.05)  # 模拟波动率
                stock['volatility'] = volatility
                stock['current_price'] = simulate_price_change(stock['price'], volatility)
                
                # 计算仓位
                max_per_stock = 20000
                if volatility > VOLATILITY_THRESHOLD_HIGH:
                    max_per_stock *= HIGH_VOL_POSITION_MULTIPLIER
                    print(f"【仓位调整】{stock['name']}波动率高({volatility*100:.1f}%)，仓位降至{max_per_stock*100:.0f}元")
                
                # 执行买入
                trade = execute_trade(portfolio, stock, action, stock['current_price'])
                if trade['shares'] > 0:
                    trades.append(trade)
                    # 记录波动率和止损线
                    for pos in portfolio['positions']:
                        if pos['code'] == stock['code']:
                            pos['volatility'] = volatility
                            pos['current_stop_loss'] = INITIAL_STOP_LOSS
                            pos['sold_ratio'] = 0
                            break
                    print(f"买入: {stock['name']}({stock['code']}) @ {stock['current_price']}元 x {trade['shares']}股")

    # 更新持仓价值
    portfolio = update_positions_value(portfolio)

    # 记录交易历史
    if trades:
        portfolio['trade_history'].extend(trades)

    save_portfolio(portfolio)

    # 输出结果
    print("\n" + "=" * 50)
    print(f"交易完成！共执行 {len(trades)} 笔交易")
    print(f"总资产: {portfolio['portfolio']['total_value']:.2f} 元")
    print(f"持仓收益: {portfolio['portfolio']['total_profit']:.2f} 元 ({portfolio['portfolio']['total_profit_rate']:+.2f}%)")
    print(f"现金: {portfolio['portfolio']['current_capital']:.2f} 元")
    print(f"持仓: {len(portfolio['positions'])} 只")
    print("=" * 50)

    return portfolio, trades

if __name__ == "__main__":
    run_daily_trading()
