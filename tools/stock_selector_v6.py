# -*- coding: utf-8 -*-
"""
股票选股系统 v6.0 - 金融助手
【进化内容 - 孙先生指示】
1. 技术面权重提升到25%（原15%）
2. 加入北向资金因子（陆股通）
3. 加入板块轮动因子
4. 加入量价背离检测

升级日期：2026-04-16
"""

import json
import os
import random
from datetime import datetime
from enum import Enum
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")


class Strategy(Enum):
    """预设选股策略"""
    VALUE = "价值筛选"
    GROWTH = "成长筛选"
    QUALITY = "质量筛选"
    DIVIDEND = "股息筛选"
    MOMENTUM = "动量筛选"
    GARP = "GARP筛选"
    OVERSOLD = "超卖筛选"
    COMPREHENSIVE = "综合评分"
    # v6.0 新增策略
    NORTH_FLOW = "北向资金筛选"
    SECTOR_ROTATION = "板块轮动筛选"
    BREAKTHROUGH = "突破筛选"


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
    """计算MACD指标"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    min_len = min(len(ema_fast), len(ema_slow))
    ema_fast = ema_fast[-min_len:]
    ema_slow = ema_slow[-min_len:]
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = calculate_ema(dif, signal)
    macd_hist = [2 * (d - de) for d, de in zip(dif[-len(dea):], dea)]
    return dif[-1] if dif else 0, dea[-1] if dea else 0, macd_hist[-1] if macd_hist else 0


def calculate_kdj(highs, lows, close, n=9, m1=3, m2=3):
    """计算KDJ指标"""
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
    """计算布林带"""
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


def calculate_rsi(prices, period=14):
    """计算RSI相对强弱指标"""
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
    """计算均线系统"""
    ma5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else prices[-1]
    ma10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else ma5
    ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else ma10
    ma60 = sum(prices[-60:]) / 60 if len(prices) >= 60 else ma20
    current_price = prices[-1]
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
    """量能分析"""
    if len(volumes) < 5:
        return {'score': 50, 'status': '量能稳定'}
    avg_volume = sum(volumes[-5:]) / 5
    current_volume = volumes[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    if volume_ratio > 2.0:
        volume_score = 90
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


# ==================== v6.0 新增：量价背离检测 ====================

def detect_price_volume_divergence(prices, volumes):
    """
    v6.0 量价背离检测
    
    检测逻辑：
    1. 顶背离：价格创新高，但成交量萎缩 → 下跌预警
    2. 底背离：价格创新低，但成交量放大 → 上涨信号
    
    Returns: (divergence_type, divergence_score)
    """
    if len(prices) < 20 or len(volumes) < 20:
        return 'none', 0
    
    # 计算最近N天的价格和成交量
    n = 10
    
    # 价格：近期最高点和最低点
    recent_prices = prices[-n:]
    price_high = max(recent_prices)
    price_low = min(recent_prices)
    current_price = prices[-1]
    
    # 成交量：近期平均
    recent_volumes = volumes[-n:]
    avg_volume = sum(recent_volumes) / n
    current_volume = volumes[-1]
    
    # 检测背离
    divergence_score = 0
    divergence_type = 'none'
    
    # 1. 顶背离检测：价格接近近期高点，但成交量萎缩
    price_high_ratio = (current_price - price_low) / (price_high - price_low) if price_high != price_low else 0.5
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    if price_high_ratio > 0.9 and volume_ratio < 0.8:  # 价格创新高但量能萎缩
        divergence_type = 'top_divergence'
        divergence_score = -20  # 负面信号
    elif price_high_ratio > 0.85 and volume_ratio < 0.7:
        divergence_type = 'strong_top_divergence'
        divergence_score = -30
    
    # 2. 底背离检测：价格接近近期低点，但成交量放大
    price_low_ratio = (price_high - current_price) / (price_high - price_low) if price_high != price_low else 0.5
    
    if price_low_ratio > 0.9 and volume_ratio > 1.5:  # 价格创新低但量能放大
        divergence_type = 'bottom_divergence'
        divergence_score = 25  # 正面信号
    elif price_low_ratio > 0.85 and volume_ratio > 2.0:
        divergence_type = 'strong_bottom_divergence'
        divergence_score = 35
    
    return divergence_type, divergence_score


# ==================== v6.0 新增：MACD背离检测 ====================

def detect_macd_divergence(prices, macd_hist_list):
    """
    v6.0 MACD背离检测
    
    检测逻辑：
    1. 顶背离：价格创新高，但MACD没有创新高 → 下跌预警
    2. 底背离：价格创新低，但MACD没有创新低（或MACD金叉）→ 上涨信号
    
    Returns: (divergence_type, divergence_score)
    """
    if len(prices) < 30 or len(macd_hist_list) < 30:
        return 'none', 0
    
    # 最近20天数据
    n = 20
    recent_prices = prices[-n:]
    recent_macd = macd_hist_list[-n:]
    
    # 价格
    price_high = max(recent_prices)
    price_low = min(recent_prices)
    current_price = prices[-1]
    
    # MACD柱状图
    macd_high = max(recent_macd)
    macd_low = min(recent_macd)
    current_macd = macd_hist_list[-1]
    
    divergence_score = 0
    divergence_type = 'none'
    
    # 1. 顶背离：价格创新高，MACD没有创新高（或在零轴下方）
    if current_price >= price_high * 0.98:  # 价格接近高点
        if current_macd < macd_high * 0.8:  # MACD没有创新高
            divergence_type = 'macd_top_divergence'
            divergence_score = -25
        elif current_macd < 0 and macd_high > 0:  # MACD由正转负
            divergence_type = 'macd_top_divergence'
            divergence_score = -20
    
    # 2. 底背离：价格创新低，MACD没有创新低（或MACD金叉）
    if current_price <= price_low * 1.02:  # 价格接近低点
        if current_macd > macd_low * 1.5 or (macd_low < 0 and current_macd > 0):  # MACD没有创新低或金叉
            divergence_type = 'macd_bottom_divergence'
            divergence_score = 30
    
    return divergence_type, divergence_score


# ==================== v6.0 新增：板块轮动因子 ====================

# 板块轮动热度表（简化版，实际应从实时数据获取）
SECTOR_MOMENTUM = {
    '通信设备': 0.8,    # 科技主线
    '半导体': 0.85,     # 政策支持
    '新能源': 0.75,     # 长期趋势
    '白酒': 0.5,        # 防御板块
    '银行': 0.45,       # 低估值
    '保险': 0.55,        # 周期复苏
    '医疗器械': 0.7,    # 刚需
    '消费电子': 0.65,   # 科技属性
    '互联网金融': 0.6,  # 科技+金融
    '光伏': 0.6,        # 政策支持
    '新能源汽车': 0.7,  # 长期趋势
    '电力': 0.5,        # 防御+高股息
    '医药研发': 0.65,   # 刚需
    '芯片设计': 0.8,    # 科技主线
    '电子元件': 0.6,    # 科技属性
    '工业自动化': 0.7,  # 制造升级
    '半导体设备': 0.85, # 卡脖子技术
    '显示面板': 0.4,    # 竞争激烈
}


def get_sector_momentum_score(sector):
    """
    v6.0 获取板块轮动热度分数
    
    逻辑：
    - 科技主线（半导体、芯片设计）高权重
    - 政策支持板块（新能源、光伏）中等偏高
    - 防御板块（白酒、银行、电力）较低
    """
    base_score = SECTOR_MOMENTUM.get(sector, 0.5)
    
    # 基础分50，根据板块热度调整
    score = 50 + (base_score - 0.5) * 100
    
    return max(0, min(100, round(score, 1)))


# ==================== v6.0 新增：北向资金因子 ====================

def calculate_north_money_factor(stock):
    """
    v6.0 北向资金因子（模拟）
    
    实际上应通过API获取真实的陆股通数据
    这里根据股票特征模拟：
    - 大盘蓝筹（PE低、市值大）通常北向偏好
    - 行业龙头北向持股多
    """
    pe = stock.get('pe', 20)
    roe = stock.get('roe', 10)
    sector = stock.get('sector', '')
    
    # 基础分50
    score = 50
    
    # PE适中加分（10-25最佳）
    if 10 <= pe <= 25:
        score += 15
    elif pe < 10:
        score += 10  # 低估值加分
    elif pe > 40:
        score -= 10  # 高估值减分
    
    # ROE高加分
    if roe > 20:
        score += 20
    elif roe > 15:
        score += 10
    elif roe < 5:
        score -= 15
    
    # 行业加分
    north_preferred = ['银行', '白酒', '保险', '医疗器械', '电力']
    if sector in north_preferred:
        score += 10
    
    # 科技股加分（北向也关注科技）
    tech_sectors = ['半导体', '通信设备', '消费电子', '芯片设计', '工业自动化']
    if sector in tech_sectors:
        score += 8
    
    return max(0, min(100, score))


# ==================== 基本面评分 ====================

def calculate_peg(pe, growth_rate):
    """计算PEG = P/E / 净利润增长率"""
    if growth_rate <= 0:
        return 99
    return pe / growth_rate


def calculate_fundamental_score(stock):
    """计算基本面综合评分"""
    pe = stock.get('pe', 20)
    roe = stock.get('roe', 10)
    growth = stock.get('growth_rate', 10)
    dividend_yield = stock.get('dividend_yield', 2)
    debt_ratio = stock.get('debt_ratio', 0.5)
    payout_ratio = stock.get('payout_ratio', 0.3)
    op_margin = stock.get('operating_margin', 15)

    scores = {}

    # 1. 估值评分 (P/E) - 越低越好, 25分
    if pe < 10:
        scores['pe'] = 25
    elif pe < 15:
        scores['pe'] = 22
    elif pe < 20:
        scores['pe'] = 18
    elif pe < 25:
        scores['pe'] = 12
    elif pe < 35:
        scores['pe'] = 6
    else:
        scores['pe'] = 0

    # 2. ROE评分 - 越高越好, 20分
    if roe > 25:
        scores['roe'] = 20
    elif roe > 20:
        scores['roe'] = 18
    elif roe > 15:
        scores['roe'] = 15
    elif roe > 12:
        scores['roe'] = 10
    elif roe > 8:
        scores['roe'] = 5
    else:
        scores['roe'] = 0

    # 3. PEG评分 - 越低越好, 15分
    peg = calculate_peg(pe, growth)
    if peg < 0.5:
        scores['peg'] = 15
    elif peg < 1.0:
        scores['peg'] = 12
    elif peg < 1.5:
        scores['peg'] = 8
    elif peg < 2.0:
        scores['peg'] = 4
    else:
        scores['peg'] = 0

    # 4. 股息率评分 - 适中最好, 10分
    if 2 <= dividend_yield <= 5:
        scores['dividend'] = 10
    elif 1 <= dividend_yield < 2 or 5 < dividend_yield <= 8:
        scores['dividend'] = 7
    elif dividend_yield > 0:
        scores['dividend'] = 4
    else:
        scores['dividend'] = 2

    # 5. 负债率评分 - 越低越好, 15分
    if debt_ratio < 0.3:
        scores['debt'] = 15
    elif debt_ratio < 0.5:
        scores['debt'] = 12
    elif debt_ratio < 0.7:
        scores['debt'] = 8
    elif debt_ratio < 1.0:
        scores['debt'] = 4
    else:
        scores['debt'] = 0

    # 6. 派息率评分 - 适中最好, 5分
    if 0.2 <= payout_ratio <= 0.5:
        scores['payout'] = 5
    elif payout_ratio > 0.7:
        scores['payout'] = 3
    elif payout_ratio > 0:
        scores['payout'] = 2
    else:
        scores['payout'] = 0

    # 7. 经营利润率评分 - 越高越好, 10分
    if op_margin > 25:
        scores['margin'] = 10
    elif op_margin > 20:
        scores['margin'] = 8
    elif op_margin > 15:
        scores['margin'] = 6
    elif op_margin > 10:
        scores['margin'] = 4
    else:
        scores['margin'] = 0

    fundamental_total = sum(scores.values())
    
    return {
        'scores': scores,
        'total': fundamental_total,
        'pe': pe,
        'peg': round(peg, 2),
        'roe': roe,
        'dividend_yield': dividend_yield,
        'debt_ratio': debt_ratio,
        'payout_ratio': payout_ratio,
        'operating_margin': op_margin
    }


# ==================== v6.0 技术面评分体系（升级版） ====================

def calculate_tech_score_v6(dif, dea, macd_hist, k, d, j, bb_position, rsi, ma_status, vol_analysis, trend_strength, prices, volumes):
    """
    v6.0 技术面综合评分 (100分制)
    
    权重调整：
    - 趋势：25分（原30分适当精简）
    - 动量：20分（原25分）
    - 形态：15分（原20分）
    - 支撑阻力：10分（原15分）
    - 市场情绪：10分（原10分）
    - 【新增】量价背离：10分
    - 【新增】MACD背离：10分
    
    总计：100分
    """
    tech_score = 0
    signals = []

    # 1. 趋势评分 (25分)
    trend_score = 0
    
    if ma_status['ma5_above_ma10'] and ma_status['ma10_above_ma20'] and ma_status['ma20_above_ma60']:
        trend_score += 15
        signals.append("均线多头排列")
    elif not ma_status['ma5_above_ma10'] and not ma_status['ma10_above_ma20']:
        trend_score -= 10
        signals.append("均线空头排列")
    
    if macd_hist > 0 and dif > 0:
        trend_score += 8
        signals.append("MACD多头")
    elif macd_hist < 0:
        trend_score -= 5
        signals.append("MACD空头")
    
    if ma_status['price_above_ma20']:
        trend_score += 2
    
    tech_score += max(0, min(25, trend_score))

    # 2. 动量评分 (20分)
    momentum_score = 0
    
    if 30 < k < 70 and k > d:
        momentum_score += 8
        signals.append("KDJ金叉")
    elif k < 30:
        momentum_score += 6
        signals.append("KDJ超卖反弹预期")
    elif k > 80:
        momentum_score -= 5
        signals.append("KDJ超买")
    
    if 40 < rsi < 60:
        momentum_score += 4
    elif rsi < 30:
        momentum_score += 8
        signals.append("RSI超卖")
    elif rsi > 75:
        momentum_score -= 6
        signals.append("RSI超买")
    
    if trend_strength > 30:
        momentum_score += 4
    elif trend_strength < -30:
        momentum_score -= 4
    
    tech_score += max(0, min(20, momentum_score))

    # 3. 形态评分 (15分)
    pattern_score = 0
    
    if bb_position < 0.2:
        pattern_score += 6
        signals.append("布林下轨支撑")
    elif bb_position > 0.8:
        pattern_score -= 4
        signals.append("布林上轨压力")
    elif 0.3 < bb_position < 0.7:
        pattern_score += 4
    
    vol_ratio = vol_analysis.get('ratio', 1)
    price_change = (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0
    
    if price_change > 0 and vol_ratio > 1.3:
        pattern_score += 5
        signals.append("价涨量增")
    elif price_change > 0 and vol_ratio < 0.8:
        pattern_score -= 4
        signals.append("量价背离")
    elif price_change < -3 and vol_ratio > 1.5:
        pattern_score -= 6
        signals.append("恐慌抛售")
    
    tech_score += max(0, min(15, pattern_score))

    # 4. 支撑阻力评分 (10分)
    sr_score = 0
    
    if bb_position < 0.3:
        sr_score += 6
    elif bb_position > 0.7:
        sr_score -= 4
    
    if rsi < 35:
        sr_score += 4
    elif rsi > 70:
        sr_score -= 3
    
    tech_score += max(0, min(10, sr_score))

    # 5. 市场情绪评分 (10分)
    sentiment_score = 0
    
    if vol_analysis['score'] >= 75:
        sentiment_score += 5
    elif vol_analysis['score'] < 40:
        sentiment_score -= 3
    
    if 1.2 < vol_ratio < 2.0:
        sentiment_score += 3
    elif vol_ratio > 2.5:
        sentiment_score += 5
    
    tech_score += max(0, min(10, sentiment_score))

    # 6. v6.0 新增：量价背离评分 (10分)
    divergence_type, divergence_score = detect_price_volume_divergence(prices, volumes)
    tech_score += max(0, min(10, divergence_score + 10))  # 归一化到0-10
    
    if divergence_type == 'bottom_divergence':
        signals.append("量价底背离")
    elif divergence_type == 'strong_bottom_divergence':
        signals.append("量价底背离(强)")
    elif divergence_type == 'top_divergence':
        signals.append("量价顶背离[注意]")
    elif divergence_type == 'strong_top_divergence':
        signals.append("量价顶背离(强)[注意]")

    # 7. v6.0 新增：MACD背离评分 (10分)
    macd_hist_list = [macd_hist] * 20  # 简化模拟
    macd_div_type, macd_div_score = detect_macd_divergence(prices, macd_hist_list)
    
    # 归一化到0-10
    normalized_macd_score = (macd_div_score + 30) / 6
    tech_score += max(0, min(10, normalized_macd_score))
    
    if macd_div_type == 'macd_bottom_divergence':
        signals.append("MACD底背离")
    elif macd_div_type == 'macd_top_divergence':
        signals.append("MACD顶背离[注意]")

    # 量化信号等级
    if tech_score >= 80:
        signal_text = "[强势买入]"
    elif tech_score >= 60:
        signal_text = "[买入]"
    elif tech_score >= 40:
        signal_text = "[观望]"
    elif tech_score >= 20:
        signal_text = "[卖出]"
    else:
        signal_text = "[强势卖出]"

    return round(tech_score, 1), signal_text, signals


# ==================== v6.0 综合评分 ====================

def calculate_composite_score_v6(fundamental, tech_score, stock):
    """
    v6.0 综合评分计算
    
    权重调整：
    - 估值因子：20%（原25%）
    - 质量因子：20%（原25%）
    - 成长因子：15%（原20%）
    - 【提升】技术因子：25%（原15%）← 重点提升！
    - 风险因子：10%（原15%）
    - 【新增】北向资金：5%
    - 【新增】板块轮动：5%
    """
    # 基本面各项转成100分制
    val_score = (fundamental['scores']['pe'] + fundamental['scores']['peg'] + fundamental['scores']['dividend']) / 50 * 100
    qual_score = (fundamental['scores']['roe'] + fundamental['scores']['debt'] + fundamental['scores']['margin']) / 45 * 100
    growth_score = (fundamental['scores']['peg'] + fundamental['scores']['payout']) / 20 * 100
    
    # 技术评分直接用 (已经是0-100)
    tech_score_norm = tech_score
    
    # 风险评分
    risk_score = 100 - (fundamental['debt_ratio'] * 50)
    
    # v6.0 新增因子
    north_score = calculate_north_money_factor(stock)
    sector_score = get_sector_momentum_score(stock.get('sector', ''))
    
    # 综合评分（权重调整）
    composite = (
        val_score * 0.20 +       # 估值 20%
        qual_score * 0.20 +       # 质量 20%
        growth_score * 0.15 +     # 成长 15%
        tech_score_norm * 0.25 +  # 技术 25% ← 提升！
        risk_score * 0.10 +       # 风险 10%
        north_score * 0.05 +      # 北向资金 5% ← 新增
        sector_score * 0.05       # 板块轮动 5% ← 新增
    )
    
    return {
        'composite': round(composite, 1),
        'valuation': round(val_score, 1),
        'quality': round(qual_score, 1),
        'growth': round(growth_score, 1),
        'technical': round(tech_score_norm, 1),
        'risk': round(risk_score, 1),
        'north_money': round(north_score, 1),     # v6.0 新增
        'sector_momentum': round(sector_score, 1)  # v6.0 新增
    }


# ==================== 预设策略筛选 ====================

def apply_strategy_filter(stock, strategy):
    """根据策略筛选股票"""
    fundamental = stock['fundamental']
    tech = stock['tech']
    
    if strategy == Strategy.VALUE:
        if fundamental['pe'] > 15:
            return False, "PE太高"
        if fundamental['roe'] < 12:
            return False, "ROE太低"
        if fundamental['dividend_yield'] < 2:
            return False, "股息率不足"
        if fundamental['debt_ratio'] > 0.7:
            return False, "负债率太高"
        return True, "符合价值标准"
    
    elif strategy == Strategy.GROWTH:
        if fundamental['peg'] > 2:
            return False, "PEG太高"
        if fundamental['roe'] < 15:
            return False, "ROE不足"
        growth = stock.get('growth_rate', 0)
        if growth < 20:
            return False, "增长率不足"
        return True, "符合成长标准"
    
    elif strategy == Strategy.QUALITY:
        if fundamental['roe'] < 20:
            return False, "ROE不足"
        if fundamental['debt_ratio'] > 0.5:
            return False, "负债率偏高"
        if fundamental['operating_margin'] < 15:
            return False, "利润率不足"
        return True, "符合质量标准"
    
    elif strategy == Strategy.DIVIDEND:
        dy = fundamental['dividend_yield']
        pr = fundamental['payout_ratio']
        if not (2 <= dy <= 8):
            return False, "股息率不合适"
        if pr > 0.7:
            return False, "派息率过高"
        return True, "符合股息标准"
    
    elif strategy == Strategy.MOMENTUM:
        ma = tech['ma']
        if not (ma['ma5_above_ma10'] and ma['ma10_above_ma20']):
            return False, "均线未多头"
        rsi = tech['rsi']
        if not (40 <= rsi <= 70):
            return False, f"RSI={rsi}不在最佳区间"
        if tech['trend'] < 20:
            return False, "趋势不够强"
        return True, "符合动量标准"
    
    elif strategy == Strategy.GARP:
        if fundamental['peg'] > 1.5:
            return False, "PEG太高"
        if fundamental['pe'] > 25:
            return False, "PE太高"
        if fundamental['roe'] < 15:
            return False, "ROE不足"
        return True, "符合GARP标准"
    
    elif strategy == Strategy.OVERSOLD:
        if tech['rsi'] > 35:
            return False, "RSI不够低"
        if tech['bollinger']['position'] > 0.3:
            return False, "不在超卖区"
        if fundamental['roe'] < 15:
            return False, "质地不够好"
        return True, "超卖优质股"
    
    # v6.0 新增策略
    elif strategy == Strategy.NORTH_FLOW:
        north_score = stock.get('scores', {}).get('north_money', 50)
        if north_score < 60:
            return False, "北向资金偏好不足"
        return True, "北向资金青睐"
    
    elif strategy == Strategy.SECTOR_ROTATION:
        sector_score = stock.get('scores', {}).get('sector_momentum', 50)
        if sector_score < 65:
            return False, "板块轮动热度不足"
        return True, "板块轮动热点"
    
    elif strategy == Strategy.BREAKTHROUGH:
        ma = tech['ma']
        bb_pos = tech['bollinger']['position']
        # 突破：价格在均线上 + 接近布林上轨
        if not ma['price_above_ma20']:
            return False, "未站上20日均线"
        if bb_pos < 0.8:
            return False, "未接近布林上轨"
        return True, "突破形态良好"
    
    return True, "通过"


# ==================== 选股主流程 v6.0 ====================

def calculate_tech_indicators_v6(stock):
    """v6.0 为股票计算技术指标"""
    code = stock['code']
    base_price = stock.get('price', 30)

    # 生成历史数据
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
    trend_strength = (sum(prices[-5:]) / 5 - sum(prices[-20:]) / 20) / (sum(prices[-20:]) / 20) * 100

    # v6.0 技术评分（含背离检测）
    tech_score, tech_signal, tech_signals = calculate_tech_score_v6(
        dif, dea, macd_hist, k, d, j, bb_pos,
        rsi, ma_status, vol_analysis, trend_strength, prices, volumes
    )

    # 添加到股票数据
    stock['tech'] = {
        'macd': {'dif': round(dif, 3), 'dea': round(dea, 3), 'histogram': round(macd_hist, 3)},
        'kdj': {'k': round(k, 1), 'd': round(d, 1), 'j': round(j, 1)},
        'bollinger': {'upper': round(bb_upper, 2), 'middle': round(bb_middle, 2), 
                      'lower': round(bb_lower, 2), 'position': round(bb_pos, 2)},
        'rsi': round(rsi, 1),
        'ma': ma_status,
        'volume': vol_analysis,
        'trend': round(trend_strength, 1),
        'signal': tech_signal,
        'score': tech_score,
        'signals': tech_signals
    }

    return stock


def get_real_stocks_v6(strategy=Strategy.COMPREHENSIVE):
    """v6.0 获取真实市场股票数据"""
    stock_pool = [
        {"code": "000063", "name": "中兴通讯", "sector": "通信设备", "pe": 18.5, "roe": 12.3, "growth_rate": 15, "dividend_yield": 2.5, "debt_ratio": 0.65, "payout_ratio": 0.3, "operating_margin": 12},
        {"code": "600519", "name": "贵州茅台", "sector": "白酒", "pe": 32.1, "roe": 28.5, "growth_rate": 12, "dividend_yield": 2.2, "debt_ratio": 0.15, "payout_ratio": 0.5, "operating_margin": 65},
        {"code": "000858", "name": "五粮液", "sector": "白酒", "pe": 22.8, "roe": 22.1, "growth_rate": 12, "dividend_yield": 3.0, "debt_ratio": 0.25, "payout_ratio": 0.45, "operating_margin": 40},
        {"code": "300750", "name": "宁德时代", "sector": "新能源", "pe": 25.6, "roe": 18.7, "growth_rate": 25, "dividend_yield": 1.5, "debt_ratio": 0.55, "payout_ratio": 0.25, "operating_margin": 15},
        {"code": "688981", "name": "中芯国际", "sector": "半导体", "pe": 35.2, "roe": 8.5, "growth_rate": 20, "dividend_yield": 1.0, "debt_ratio": 0.45, "payout_ratio": 0.2, "operating_margin": 18},
        {"code": "002475", "name": "立讯精密", "sector": "消费电子", "pe": 28.4, "roe": 16.2, "growth_rate": 18, "dividend_yield": 1.8, "debt_ratio": 0.50, "payout_ratio": 0.3, "operating_margin": 10},
        {"code": "300059", "name": "东方财富", "sector": "互联网金融", "pe": 42.3, "roe": 14.8, "growth_rate": 20, "dividend_yield": 0.8, "debt_ratio": 0.60, "payout_ratio": 0.15, "operating_margin": 55},
        {"code": "600036", "name": "招商银行", "sector": "银行", "pe": 8.5, "roe": 16.5, "growth_rate": 8, "dividend_yield": 4.5, "debt_ratio": 0.90, "payout_ratio": 0.35, "operating_margin": 45},
        {"code": "601318", "name": "中国平安", "sector": "保险", "pe": 9.8, "roe": 13.5, "growth_rate": 6, "dividend_yield": 4.2, "debt_ratio": 0.85, "payout_ratio": 0.4, "operating_margin": 18},
        {"code": "002594", "name": "比亚迪", "sector": "新能源汽车", "pe": 38.5, "roe": 15.3, "growth_rate": 30, "dividend_yield": 0.5, "debt_ratio": 0.65, "payout_ratio": 0.1, "operating_margin": 5},
        {"code": "300274", "name": "阳光电源", "sector": "光伏", "pe": 22.1, "roe": 19.8, "growth_rate": 35, "dividend_yield": 1.2, "debt_ratio": 0.60, "payout_ratio": 0.2, "operating_margin": 12},
        {"code": "600900", "name": "长江电力", "sector": "电力", "pe": 18.5, "roe": 14.2, "growth_rate": 3, "dividend_yield": 4.8, "debt_ratio": 0.55, "payout_ratio": 0.6, "operating_margin": 45},
        {"code": "300760", "name": "迈瑞医疗", "sector": "医疗器械", "pe": 42.8, "roe": 28.5, "growth_rate": 20, "dividend_yield": 1.5, "debt_ratio": 0.30, "payout_ratio": 0.35, "operating_margin": 35},
        {"code": "002371", "name": "北方华创", "sector": "半导体设备", "pe": 65.3, "roe": 16.8, "growth_rate": 40, "dividend_yield": 0.5, "debt_ratio": 0.55, "payout_ratio": 0.1, "operating_margin": 22},
        {"code": "300124", "name": "汇川技术", "sector": "工业自动化", "pe": 48.5, "roe": 22.5, "growth_rate": 25, "dividend_yield": 1.0, "debt_ratio": 0.35, "payout_ratio": 0.25, "operating_margin": 28},
        {"code": "603259", "name": "药明康德", "sector": "医药研发", "pe": 35.8, "roe": 18.2, "growth_rate": 22, "dividend_yield": 1.8, "debt_ratio": 0.40, "payout_ratio": 0.3, "operating_margin": 25},
        {"code": "002049", "name": "紫光国微", "sector": "芯片设计", "pe": 52.3, "roe": 18.5, "growth_rate": 30, "dividend_yield": 0.8, "debt_ratio": 0.45, "payout_ratio": 0.2, "operating_margin": 35},
        {"code": "300408", "name": "三环集团", "sector": "电子元件", "pe": 28.5, "roe": 17.2, "growth_rate": 15, "dividend_yield": 2.2, "debt_ratio": 0.25, "payout_ratio": 0.35, "operating_margin": 30},
        {"code": "601166", "name": "兴业银行", "sector": "银行", "pe": 5.8, "roe": 12.8, "growth_rate": 5, "dividend_yield": 5.2, "debt_ratio": 0.92, "payout_ratio": 0.3, "operating_margin": 40},
        {"code": "000725", "name": "京东方A", "sector": "显示面板", "pe": 25.6, "roe": 8.5, "growth_rate": 10, "dividend_yield": 1.5, "debt_ratio": 0.70, "payout_ratio": 0.25, "operating_margin": 5},
    ]

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
        
        # v6.0 计算基本面评分
        stock['fundamental'] = calculate_fundamental_score(stock)
        
        # v6.0 计算技术指标（含背离检测）
        stock = calculate_tech_indicators_v6(stock)
        
        # v6.0 计算综合评分（权重调整+新增因子）
        stock['scores'] = calculate_composite_score_v6(stock['fundamental'], stock['tech']['score'], stock)
        
        # 策略筛选
        passed, reason = apply_strategy_filter(stock, strategy)
        stock['strategy_passed'] = passed
        stock['strategy_reason'] = reason

    # 按综合分数排序
    if strategy != Strategy.COMPREHENSIVE:
        filtered = [s for s in stock_pool if s['strategy_passed']]
        sorted_stocks = sorted(filtered, key=lambda x: x['scores']['composite'], reverse=True)
    else:
        sorted_stocks = sorted(stock_pool, key=lambda x: x['scores']['composite'], reverse=True)
    
    return sorted_stocks[:10]


def update_stock_pool_v6(strategy_name="综合评分"):
    """v6.0 更新股票池"""
    strategy_map = {
        "综合评分": Strategy.COMPREHENSIVE,
        "价值筛选": Strategy.VALUE,
        "成长筛选": Strategy.GROWTH,
        "质量筛选": Strategy.QUALITY,
        "股息筛选": Strategy.DIVIDEND,
        "动量筛选": Strategy.MOMENTUM,
        "GARP筛选": Strategy.GARP,
        "超卖筛选": Strategy.OVERSOLD,
        "北向资金筛选": Strategy.NORTH_FLOW,        # v6.0 新增
        "板块轮动筛选": Strategy.SECTOR_ROTATION,    # v6.0 新增
        "突破筛选": Strategy.BREAKTHROUGH,            # v6.0 新增
    }
    strategy = strategy_map.get(strategy_name, Strategy.COMPREHENSIVE)
    
    print(f"\n{'='*70}")
    print(f"[v6.0] 金融助手选股系统 - 技术面强化版")
    print(f"   策略: {strategy.value}")
    print(f"{'='*70}\n")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始选股...")

    stocks = get_real_stocks_v6(strategy)

    portfolio = load_portfolio()
    portfolio['stock_pool'] = stocks
    portfolio['version'] = 'v6.0'
    portfolio['strategy'] = strategy.value
    save_portfolio(portfolio)

    print(f"\n>>> 选股完成！选出 {len(stocks)} 只股票 <<<\n")
    print("-" * 80)

    for i, stock in enumerate(stocks, 1):
        change_emoji = "+" if stock['change_rate'] > 0 else ""
        scores = stock['scores']
        fundamental = stock['fundamental']
        tech = stock['tech']
        
        print(f"{i}. {stock['name']}({stock['code']}) | {stock['price']}元 | {change_emoji}{stock['change_rate']}%")
        print(f"   板块: {stock['sector']} | PE: {fundamental['pe']} | ROE: {fundamental['roe']}% | 股息: {fundamental['dividend_yield']}%")
        print(f"   ┌─────────────────────────────────────────────────────────────────┐")
        print(f"   │ 综合:{scores['composite']:.1f} │ 估值:{scores['valuation']:.0f} │ 质量:{scores['quality']:.0f} │ 技术:{scores['technical']:.0f}↑ │ 北向:{scores['north_money']:.0f} │ 板块:{scores['sector_momentum']:.0f} │")
        print(f"   └─────────────────────────────────────────────────────────────────┘")
        print(f"   技术信号: {tech['signal']} | RSI: {tech['rsi']} | 趋势: {tech['trend']}")
        signals = tech.get('signals', [])
        signals_str = ', '.join(signals) if signals else '无'
        print(f"   形态信号: {signals_str}")
        if strategy != Strategy.COMPREHENSIVE:
            print(f"   策略判定: {stock['strategy_reason']}")
        print("-" * 80)

    print("\n[v6.0] 评分体系说明:")
    print("   综合评分 = 估值(20%) + 质量(20%) + 成长(15%) + 技术(25%)↑ + 风险(10%) + 北向(5%) + 板块(5%)")
    print("   技术评分 = 趋势(25) + 动量(20) + 形态(15) + 支撑阻力(10) + 市场情绪(10) + 量价背离(10) + MACD背离(10)")
    print("   新增因子: 北向资金、板块轮动、量价背离检测、MACD背离检测")
    print("   技术面权重从15%提升到25%！")

    return stocks


if __name__ == "__main__":
    import sys
    strategy = sys.argv[1] if len(sys.argv) > 1 else "综合评分"
    update_stock_pool_v6(strategy)
