# -*- coding: utf-8 -*-
"""
小龙量化 - 专业版 v2.0
整合：腾讯数据源 + 布林带策略 + MACD背离 + 多因子评分
初始资金：50,000元
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

# ============ 配置 ============
INITIAL_CAPITAL = 50000
PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")

# ============ 腾讯数据源 ============
def get_realtime(stock_codes: List[str]) -> List[Dict]:
    """获取实时行情"""
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
                'prev_close': float(parts[4]) if parts[4] else 0,
                'open': float(parts[5]) if parts[5] else 0,
                'change_pct': float(parts[32]) if parts[32] else 0,
                'high': float(parts[33]) if parts[33] else 0,
                'low': float(parts[34]) if parts[34] else 0,
                'volume': float(parts[36]) if parts[36] else 0,
                'amount': float(parts[37]) if parts[37] else 0,
                'pe': float(parts[39]) if parts[39] else 0,
                'turnover': float(parts[38]) if parts[38] else 0,
            })
    return stocks

def get_kline(stock_code: str, days: int = 30) -> List[Dict]:
    """获取K线数据（腾讯日K）"""
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},day,,,{days},qfq'
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        code_key = stock_code
        stock_data = data.get('data', {}).get(code_key, {})
        klines = stock_data.get('qfqday', stock_data.get('day', []))
        
        result = []
        for k in klines:
            result.append({
                'date': k[0],
                'open': float(k[1]),
                'close': float(k[2]),
                'high': float(k[3]),
                'low': float(k[4]),
                'volume': float(k[5]) if len(k) > 5 else 0
            })
        return result
    except:
        return []

# ============ 技术指标 ============
def calc_ma(prices: List[float], period: int) -> float:
    """计算均线"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def calc_bollinger(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """计算布林带 (upper, middle, lower)"""
    if len(prices) < period:
        if prices:
            return prices[-1] * 1.05, prices[-1], prices[-1] * 0.95
        return 0, 0, 0
    
    recent = prices[-period:]
    middle = sum(recent) / period
    variance = sum((p - middle) ** 2 for p in recent) / period
    std = math.sqrt(variance)
    
    return middle + std_dev * std, middle, middle - std_dev * std

def calc_rsi(prices: List[float], period: int = 14) -> float:
    """计算RSI"""
    if len(prices) < period + 1:
        return 50
    
    gains = []
    losses = []
    for i in range(-period, 0):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(prices: List[float]) -> Tuple[float, float, float]:
    """计算MACD (DIF, DEA, MACD柱)"""
    if len(prices) < 26:
        return 0, 0, 0
    
    # EMA12
    ema12 = prices[0]
    for p in prices[1:]:
        ema12 = ema12 * 11/13 + p * 2/13
    
    # EMA26
    ema26 = prices[0]
    for p in prices[1:]:
        ema26 = ema26 * 25/27 + p * 2/27
    
    dif = ema12 - ema26
    
    # DEA (DIF的9日EMA)
    dea = dif * 0.2  # 简化计算
    
    macd = (dif - dea) * 2
    
    return dif, dea, macd

# ============ 专业评分系统 ============
def professional_score(stock: Dict, kline_data: List[Dict]) -> Dict:
    """专业多因子评分"""
    score = 50
    signals = []
    details = {}
    
    prices = [k['close'] for k in kline_data] if kline_data else [stock['price']]
    volumes = [k['volume'] for k in kline_data] if kline_data else [stock['volume']]
    
    # === 1. 价值因子 (25%) ===
    pe = stock['pe']
    if 0 < pe < 15:
        score += 15
        signals.append("PE低估")
    elif 15 <= pe < 25:
        score += 10
        signals.append("PE合理")
    elif pe >= 40:
        score -= 10
        signals.append("PE偏高")
    details['pe'] = pe
    
    # === 2. 技术因子 (40%) ===
    # 布林带
    upper, middle, lower = calc_bollinger(prices)
    current = stock['price']
    band_position = (current - lower) / (upper - lower) if upper != lower else 0.5
    
    if band_position < 0.2:
        score += 20
        signals.append("布林带下轨-超卖")
    elif band_position < 0.4:
        score += 10
        signals.append("布林带中下-可买")
    elif band_position > 0.8:
        score -= 15
        signals.append("布林带上轨-超买")
    details['bollinger_pos'] = f"{band_position:.0%}"
    
    # RSI
    rsi = calc_rsi(prices)
    if rsi < 30:
        score += 15
        signals.append("RSI超卖")
    elif rsi < 40:
        score += 8
    elif rsi > 70:
        score -= 12
        signals.append("RSI超买")
    details['rsi'] = f"{rsi:.1f}"
    
    # MACD
    dif, dea, macd = calc_macd(prices)
    if macd > 0 and dif > dea:
        score += 10
        signals.append("MACD金叉")
    elif macd < 0 and dif < dea:
        score -= 8
        signals.append("MACD死叉")
    details['macd'] = f"{macd:.2f}"
    
    # 均线
    ma5 = calc_ma(prices, 5)
    ma20 = calc_ma(prices, 20)
    if current > ma5 > ma20:
        score += 10
        signals.append("多头排列")
    elif current < ma5 < ma20:
        score -= 10
        signals.append("空头排列")
    
    # === 3. 量价因子 (20%) ===
    if len(volumes) >= 5:
        avg_vol = sum(volumes[-5:]) / 5
        current_vol = volumes[-1]
        if current_vol > avg_vol * 1.5 and stock['change_pct'] > 0:
            score += 12
            signals.append("放量上涨")
        elif current_vol > avg_vol * 1.5 and stock['change_pct'] < 0:
            score -= 10
            signals.append("放量下跌")
    
    # === 4. 动量因子 (15%) ===
    change = stock['change_pct']
    if 1 < change < 4:
        score += 8
    elif 4 <= change < 7:
        score += 5
    elif change > 7:
        score -= 3
        signals.append("涨幅过大")
    elif -3 < change < 0:
        score -= 3
    elif change < -5:
        score -= 12
        signals.append("大跌")
    
    score = min(100, max(0, score))
    
    return {
        'score': score,
        'signals': signals,
        'details': details,
        'recommendation': '强烈买入' if score >= 85 else '买入' if score >= 70 else '持有' if score >= 50 else '观望' if score >= 35 else '卖出'
    }

# ============ 模拟盘 ============
class PaperTrading:
    def __init__(self):
        self.initial_capital = INITIAL_CAPITAL
        self.load()
    
    def load(self):
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cash = data.get('cash', self.initial_capital)
                self.positions = data.get('positions', {})
                self.trades = data.get('trades', [])
                self.history = data.get('history', [])
        else:
            self.cash = self.initial_capital
            self.positions = {}
            self.trades = []
            self.history = []
    
    def save(self):
        data = {
            'cash': self.cash,
            'positions': self.positions,
            'trades': self.trades[-100:],
            'history': self.history[-30:],
            'last_update': datetime.now().isoformat()
        }
        with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def buy(self, stock: Dict, shares: int = 100) -> bool:
        cost = stock['price'] * shares * 1.0003
        if cost > self.cash:
            return False
        
        self.cash -= cost
        code = stock['code']
        if code in self.positions:
            old = self.positions[code]
            total = old['shares'] + shares
            avg = (old['avg_cost'] * old['shares'] + stock['price'] * shares) / total
            self.positions[code] = {'shares': total, 'avg_cost': round(avg, 2)}
        else:
            self.positions[code] = {'shares': shares, 'avg_cost': stock['price']}
        
        self.trades.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': '买入',
            'stock': stock['name'],
            'code': code,
            'price': stock['price'],
            'shares': shares
        })
        self.save()
        return True
    
    def sell(self, stock: Dict, shares: int = 100) -> bool:
        code = stock['code']
        if code not in self.positions or self.positions[code]['shares'] < shares:
            return False
        
        revenue = stock['price'] * shares * 0.9997
        self.cash += revenue
        
        profit = (stock['price'] - self.positions[code]['avg_cost']) * shares
        self.positions[code]['shares'] -= shares
        if self.positions[code]['shares'] == 0:
            del self.positions[code]
        
        self.trades.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': '卖出',
            'stock': stock['name'],
            'code': code,
            'price': stock['price'],
            'shares': shares,
            'profit': round(profit, 2)
        })
        self.save()
        return True
    
    def get_status(self, current_prices: List[Dict]) -> Dict:
        holdings_value = 0
        holdings = []
        for code, pos in self.positions.items():
            for s in current_prices:
                if s['code'] == code:
                    value = s['price'] * pos['shares']
                    profit = (s['price'] - pos['avg_cost']) * pos['shares']
                    pct = (s['price'] / pos['avg_cost'] - 1) * 100 if pos['avg_cost'] > 0 else 0
                    holdings_value += value
                    holdings.append({
                        'name': s['name'], 'code': code, 'shares': pos['shares'],
                        'avg_cost': pos['avg_cost'], 'current': s['price'],
                        'value': value, 'profit': profit, 'pct': pct
                    })
        
        total = self.cash + holdings_value
        profit = total - self.initial_capital
        pct = (total / self.initial_capital - 1) * 100
        
        return {
            'cash': self.cash, 'holdings_value': holdings_value,
            'total': total, 'profit': profit, 'pct': pct, 'holdings': holdings
        }

# ============ 主程序 ============
def run():
    print("=" * 55)
    print("🐉 小龙量化 - 专业版 v2.0")
    print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)
    
    # 股票池（蓝筹+白马）
    pool = [
        'sh600519',  # 贵州茅台
        'sz000858',  # 五粮液
        'sh601318',  # 中国平安
        'sh600036',  # 招商银行
        'sz000333',  # 美的集团
        'sh600276',  # 恒瑞医药
        'sz002714',  # 牧原股份
        'sh601888',  # 中国中免
        'sh600900',  # 长江电力
        'sz000651',  # 格力电器
    ]
    
    # 获取实时行情
    stocks = get_realtime(pool)
    
    # 获取K线并评分
    print("\n📊 专业分析:")
    print("-" * 55)
    
    results = []
    for i, s in enumerate(stocks):
        # 补充交易所前缀
        code_with_prefix = pool[i] if i < len(pool) else s['code']
        kline = get_kline(code_with_prefix, 60)
        analysis = professional_score(s, kline)
        results.append((s, analysis))
        
        emoji = "🔴" if s['change_pct'] > 0 else "🟢"
        signals_str = " ".join(analysis['signals'][:3]) if analysis['signals'] else "无信号"
        print(f"{emoji} {s['name']:　<6} {s['price']:>8.2f}元 {s['change_pct']:>+5.2f}%  "
              f"评分:{analysis['score']:>3}  {analysis['recommendation']:　<4}  {signals_str}")
    
    # 按评分排序
    results.sort(key=lambda x: x[1]['score'], reverse=True)
    
    print("\n🏆 评分排名:")
    print("-" * 55)
    for i, (s, a) in enumerate(results[:5], 1):
        print(f"  {i}. {s['name']:　<6} {a['score']}分  {a['recommendation']}  "
              f"BOLL:{a['details'].get('bollinger_pos','-')} RSI:{a['details'].get('rsi','-')}")
    
    # 账户状态
    account = PaperTrading()
    status = account.get_status(stocks)
    
    print(f"\n💰 模拟盘:")
    print("-" * 55)
    print(f"  总资产: {status['total']:>12,.0f}元")
    print(f"  可用:   {status['cash']:>10,.0f}元")
    print(f"  持仓:   {status['holdings_value']:>10,.0f}元")
    e = "🟢" if status['profit'] >= 0 else "🔴"
    print(f"  盈亏:   {e} {status['profit']:>+.0f}元 ({status['pct']:+.2f}%)")
    
    if status['holdings']:
        print("\n📈 持仓:")
        for h in status['holdings']:
            e = "🟢" if h['profit'] >= 0 else "🔴"
            print(f"  {e} {h['name']:　<6} {h['shares']}股 {h['avg_cost']:.2f}→{h['current']:.2f} {h['profit']:>+.0f}元({h['pct']:+.1f}%)")
    
    # 交易建议
    print("\n💡 操作建议:")
    print("-" * 55)
    for s, a in results[:3]:
        if a['score'] >= 75 and s['code'] not in account.positions:
            shares = 100 if s['price'] > 100 else 200 if s['price'] > 50 else 300
            print(f"  ✅ 建议买入: {s['name']} {shares}股 @ {s['price']}元 (评分{a['score']})")
    
    for s, a in results[-2:]:
        if a['score'] < 45 and s['code'] in account.positions:
            print(f"  ⚠️ 建议卖出: {s['name']} (评分{a['score']}，信号弱)")
    
    print("\n" + "=" * 55)
    return status

if __name__ == '__main__':
    run()
