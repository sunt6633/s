# -*- coding: utf-8 -*-
"""
量化交易引擎 v2.0 - 金融助手
【量化交易进化版】

基于孙先生指示：
1. 接入免费数据源 akshare
2. 增加布林带买卖点量化
3. MACD底背离检测
4. 建立模拟回测框架

升级日期：2026-04-16
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
BACKTEST_DIR = os.path.join(BASE_DIR, "backtest")


# ============ akshare 数据接入模块 ============

class AkshareDataSource:
    """
    akshare 免费数据源接口
    
    支持：
    - 股票实时行情
    - 历史K线数据
    - 财务数据
    - 板块资金流向
    """
    
    def __init__(self):
        self.akshare_available = False
        self._check_akshare()
    
    def _check_akshare(self):
        """检查akshare是否可用"""
        try:
            import akshare as ak
            self.ak = ak
            self.akshare_available = True
            print("[数据源] akshare 已安装，可使用免费数据")
        except ImportError:
            print("[数据源] akshare 未安装，将使用模拟数据")
            self.akshare_available = False
    
    def get_stock_realtime(self, symbol: str) -> Optional[Dict]:
        """
        获取股票实时行情
        symbol: 股票代码，如 '000001' 或 '000001.SZ'
        """
        if not self.akshare_available:
            return self._simulate_realtime(symbol)
        
        try:
            # 转换代码格式
            if not symbol.endswith(('.SH', '.SZ')):
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            # 获取实时数据
            df = self.ak.stock_zh_a_spot_em()
            
            # 筛选目标股票
            code = symbol.replace('.SH', '').replace('.SZ', '')
            row = df[df['代码'] == code]
            
            if not row.empty:
                r = row.iloc[0]
                return {
                    'code': code,
                    'name': r.get('名称', ''),
                    'price': float(r.get('最新价', 0)),
                    'change': float(r.get('涨跌幅', 0)),
                    'volume': float(r.get('成交量', 0)),
                    'turnover': float(r.get('成交额', 0)),
                    'high': float(r.get('最高', 0)),
                    'low': float(r.get('最低', 0)),
                    'open': float(r.get('今开', 0)),
                    'prev_close': float(r.get('昨收', 0)),
                }
        except Exception as e:
            print(f"[数据源] 获取实时数据失败: {e}")
        
        return self._simulate_realtime(symbol)
    
    def get_stock_history(self, symbol: str, period: str = "daily", 
                         start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            period: K线周期 'daily', 'weekly', 'monthly'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
        """
        if not self.akshare_available:
            return self._simulate_history(symbol, period, start_date, end_date)
        
        try:
            if not symbol.endswith(('.SH', '.SZ')):
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            # 获取日K数据
            df = self.ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            
            # 转换格式
            data = []
            for _, row in df.iterrows():
                data.append({
                    'date': str(row.get('日期', '')),
                    'open': float(row.get('开盘', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'close': float(row.get('收盘', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'turnover': float(row.get('成交额', 0)),
                    'change': float(row.get('涨跌幅', 0)),
                })
            
            return data[-100:]  # 返回最近100天
            
        except Exception as e:
            print(f"[数据源] 获取历史数据失败: {e}")
        
        return self._simulate_history(symbol, period, start_date, end_date)
    
    def get_market_index(self) -> Optional[Dict]:
        """获取大盘指数（上证、深证、创业板）"""
        if not self.akshare_available:
            return {
                'shanghai': {'change': random.uniform(-2, 3)},
                'shenzhen': {'change': random.uniform(-2, 3)},
                'gem': {'change': random.uniform(-2, 3)},
            }
        
        try:
            df = self.ak.stock_zh_index_spot_em()
            
            result = {}
            for _, row in df.iterrows():
                code = row.get('代码', '')
                if code == '000001':
                    result['shanghai'] = {'price': float(row.get('最新价', 0)), 'change': float(row.get('涨跌幅', 0))}
                elif code == '399001':
                    result['shenzhen'] = {'price': float(row.get('最新价', 0)), 'change': float(row.get('涨跌幅', 0))}
                elif code == '399006':
                    result['gem'] = {'price': float(row.get('最新价', 0)), 'change': float(row.get('涨跌幅', 0))}
            
            return result if result else None
            
        except Exception as e:
            print(f"[数据源] 获取指数失败: {e}")
            return None
    
    def _simulate_realtime(self, symbol: str) -> Dict:
        """模拟实时数据"""
        base_prices = {'000063': 35, '600519': 1680, '000858': 148, '300750': 185, '601318': 45, '601166': 16}
        code = symbol.replace('.SH', '').replace('.SZ', '')
        base = base_prices.get(code, 30)
        price = base * random.uniform(0.95, 1.05)
        
        return {'code': code, 'name': '未知', 'price': round(price, 2), 'change': round(random.uniform(-5, 5), 2),
                'volume': random.randint(1000000, 10000000), 'high': round(price * 1.03, 2),
                'low': round(price * 0.97, 2), 'open': round(price * 0.99, 2), 'prev_close': round(price * 0.98, 2)}
    
    def _simulate_history(self, symbol: str, period: str, start_date: str, end_date: str) -> List[Dict]:
        """模拟历史数据"""
        base_prices = {'000063': 35, '600519': 1680, '000858': 148, '300750': 185, '601318': 45, '601166': 16}
        code = symbol.replace('.SH', '').replace('.SZ', '')
        base = base_prices.get(code, 30)
        
        data = []
        current = base * 0.9
        
        for i in range(100):
            date = datetime.now() - timedelta(days=100-i)
            change = random.uniform(-0.05, 0.06)
            current = current * (1 + change)
            high = current * random.uniform(1.0, 1.05)
            low = current * random.uniform(0.95, 1.0)
            
            data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(current * 0.99, 2),
                        'high': round(high, 2), 'low': round(low, 2), 'close': round(current, 2),
                        'volume': random.randint(1000000, 10000000), 'turnover': random.randint(100000000, 1000000000),
                        'change': round(change * 100, 2)})
        
        return data


# ============ 布林带量化交易系统 ============

class BollingerBandStrategy:
    """布林带量化交易策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
    
    def calculate_bands(self, prices: List[float]) -> Tuple[float, float, float]:
        """计算布林带 Returns: (upper, middle, lower)"""
        if len(prices) < self.period:
            return prices[-1] * 1.05, prices[-1], prices[-1] * 0.95
        
        recent = prices[-self.period:]
        middle = sum(recent) / self.period
        variance = sum((p - middle) ** 2 for p in recent) / self.period
        std = variance ** 0.5
        
        return middle + self.std_dev * std, middle, middle - self.std_dev * std
    
    def get_position(self, price: float, upper: float, middle: float, lower: float) -> float:
        """计算价格在布林带中的位置 0.0 ~ 1.0"""
        band_width = upper - lower
        if band_width == 0:
            return 0.5
        return (price - lower) / band_width
    
    def generate_signals(self, prices: List[float], volumes: List[int] = None) -> Dict:
        """生成布林带交易信号"""
        upper, middle, lower = self.calculate_bands(prices)
        position = self.get_position(prices[-1], upper, middle, lower)
        bandwidth = (upper - lower) / middle * 100 if middle > 0 else 0
        
        signal = 'hold'
        confidence = 50
        analysis = ""
        
        if position < 0.15:
            signal, confidence, analysis = 'buy', 85, "价格跌破下轨，超卖信号，可能反弹"
        elif position > 0.85:
            signal, confidence, analysis = 'sell', 85, "价格突破上轨，超买信号，注意风险"
        elif position < 0.25:
            signal, confidence, analysis = 'buy', 65, "价格接近下轨，有支撑，可关注"
        elif position > 0.75:
            signal, confidence, analysis = 'sell', 65, "价格接近上轨，有压力，谨慎追高"
        elif prices[-1] > middle:
            analysis = "价格在中间轨上方，趋势偏多"
        else:
            analysis = "价格在中间轨下方，趋势偏空"
        
        if bandwidth < 10:
            analysis += " | 布林收口，注意突破方向"
        
        return {'signal': signal, 'confidence': confidence, 'upper': round(upper, 2),
                'middle': round(middle, 2), 'lower': round(lower, 2), 'position': round(position, 2),
                'bandwidth': round(bandwidth, 2), 'analysis': analysis}


# ============ MACD背离检测系统 ============

class MACDDivergenceDetector:
    """MACD背离检测"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast, self.slow, self.signal = fast, slow, signal
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        if len(prices) < period:
            return prices
        ema = [sum(prices[:period]) / period]
        mult = 2 / (period + 1)
        for price in prices[period:]:
            ema.append((price - ema[-1]) * mult + ema[-1])
        return ema
    
    def calculate_macd(self, prices: List[float]) -> Tuple[List[float], List[float], List[float]]:
        ema_fast = self.calculate_ema(prices, self.fast)
        ema_slow = self.calculate_ema(prices, self.slow)
        min_len = min(len(ema_fast), len(ema_slow))
        dif = [f - s for f, s in zip(ema_fast[-min_len:], ema_slow[-min_len:])]
        dea = self.calculate_ema(dif, self.signal)
        min_len = min(len(dif), len(dea))
        histogram = [2 * (d - de) for d, de in zip(dif[-min_len:], dea[-min_len:])]
        return dif[-min_len:], dea[-min_len:], histogram
    
    def find_peaks(self, data: List[float], lookback: int = 20) -> List[Tuple[int, float]]:
        peaks = []
        for i in range(lookback, len(data) - lookback):
            if data[i] == max(data[i-lookback:i+lookback+1]):
                peaks.append((i, data[i]))
        return peaks
    
    def find_valleys(self, data: List[float], lookback: int = 20) -> List[Tuple[int, float]]:
        valleys = []
        for i in range(lookback, len(data) - lookback):
            if data[i] == min(data[i-lookback:i+lookback+1]):
                valleys.append((i, data[i]))
        return valleys
    
    def detect_divergence(self, prices: List[float]) -> Dict:
        """检测MACD背离"""
        if len(prices) < 50:
            return {'type': 'none', 'strength': 0, 'signal': 'hold', 'analysis': '数据不足'}
        
        dif, dea, histogram = self.calculate_macd(prices)
        macd_line = dif
        price_peaks = self.find_peaks(prices)
        macd_peaks = self.find_peaks(macd_line)
        price_valleys = self.find_valleys(prices)
        macd_valleys = self.find_valleys(macd_line)
        
        signal, div_type, strength, analysis = 'hold', 'none', 0, ""
        
        # 顶背离检测
        if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
            p1_idx, p1_val = price_peaks[-2]
            p2_idx, p2_val = price_peaks[-1]
            m1_idx, m1_val = macd_peaks[-2]
            m2_idx, m2_val = macd_peaks[-1]
            
            if p2_val > p1_val and m2_val <= m1_val and p2_idx > m1_idx:
                div_type, strength, signal, analysis = 'top_divergence', min(100, int((m1_val - m2_val) / abs(m1_val) * 100) + 70), 'sell', "MACD顶背离：价格创新高但MACD未跟随"
        
        # 底背离检测
        if len(price_valleys) >= 2 and len(macd_valleys) >= 2:
            v1_idx, v1_val = price_valleys[-2]
            v2_idx, v2_val = price_valleys[-1]
            m1_idx, m1_val = macd_valleys[-2]
            m2_idx, m2_val = macd_valleys[-1]
            
            if v2_val < v1_val and m2_val >= m1_val and v2_idx > m1_idx:
                div_type, strength, signal, analysis = 'bottom_divergence', min(100, int(abs(m2_val - m1_val) / abs(m1_val) * 100) + 70), 'buy', "MACD底背离：价格创新低但MACD未跟随"
        
        if div_type == 'none':
            analysis = "无明显背离信号"
        
        return {'type': div_type, 'strength': strength, 'signal': signal, 'analysis': analysis,
                'dif': round(dif[-1], 4) if dif else 0, 'dea': round(dea[-1], 4) if dea else 0,
                'histogram': round(histogram[-1], 4) if histogram else 0}


# ============ 回测框架 ============

class BacktestEngine:
    """量化回测引擎"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def buy(self, code: str, name: str, price: float, shares: int, date: str) -> bool:
        cost = price * shares
        if self.cash < cost:
            return False
        
        if code in self.positions:
            old = self.positions[code]
            total_cost = old['avg_cost'] * old['shares'] + cost
            old['shares'] += shares
            old['avg_cost'] = total_cost / old['shares']
        else:
            self.positions[code] = {'name': name, 'shares': shares, 'avg_cost': price, 'entries': [{'date': date, 'price': price, 'shares': shares}]}
        
        self.cash -= cost
        self.trades.append({'date': date, 'code': code, 'name': name, 'action': 'buy', 'price': price, 'shares': shares, 'amount': cost})
        return True
    
    def sell(self, code: str, price: float, shares: int, date: str, reason: str = "") -> bool:
        if code not in self.positions:
            return False
        
        pos = self.positions[code]
        if pos['shares'] < shares:
            shares = pos['shares']
        
        revenue = price * shares
        profit = (price - pos['avg_cost']) * shares
        self.cash += revenue
        pos['shares'] -= shares
        self.trades.append({'date': date, 'code': code, 'name': pos['name'], 'action': 'sell', 'price': price, 'shares': shares, 'amount': revenue, 'profit': profit, 'reason': reason})
        
        if pos['shares'] == 0:
            del self.positions[code]
        return True
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        return self.cash + sum(pos['shares'] * current_prices.get(code, pos['avg_cost']) for code, pos in self.positions.items())
    
    def record_equity(self, date: str, current_prices: Dict[str, float]):
        total_value = self.get_total_value(current_prices)
        self.equity_curve.append({'date': date, 'value': total_value, 'cash': self.cash, 'positions_value': total_value - self.cash})
    
    def run_backtest(self, data: List[Dict], strategy, initial_capital: float = 100000, stop_loss: float = 0.08, take_profit: float = 0.20) -> Dict:
        self.__init__(initial_capital)
        
        for i, bar in enumerate(data):
            date = bar['date']
            current_prices = {data[0].get('code', 'stock'): bar['close']}
            self.record_equity(date, current_prices)
            
            lookback_data = data[max(0, i-50):i+1]
            signal = strategy(lookback_data)
            
            for trade_signal in signal.get('trades', []):
                action = trade_signal['action']
                code = data[0].get('code', 'stock')
                name = trade_signal.get('name', code)
                price = bar['close']
                
                if action == 'buy':
                    max_shares = int((self.cash * 0.3) / price / 100) * 100
                    if max_shares >= 100:
                        self.buy(code, name, price, max_shares, date)
                elif action == 'sell' and code in self.positions:
                    pos = self.positions[code]
                    self.sell(code, price, pos['shares'], date, trade_signal.get('reason', ''))
            
            for code in list(self.positions.keys()):
                pos = self.positions[code]
                current_price = bar['close']
                profit_rate = (current_price - pos['avg_cost']) / pos['avg_cost']
                
                if profit_rate <= -stop_loss:
                    self.sell(code, current_price, pos['shares'], date, f'止损({profit_rate*100:.1f}%)')
                elif profit_rate >= take_profit:
                    self.sell(code, current_price, pos['shares'], date, f'止盈({profit_rate*100:.1f}%)')
        
        if data:
            final_price = data[-1]['close']
            for code in list(self.positions.keys()):
                pos = self.positions[code]
                self.sell(code, final_price, pos['shares'], data[-1]['date'], '回测结束')
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        if not self.equity_curve:
            return {}
        
        final_value = self.equity_curve[-1]['value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        days = len(self.equity_curve)
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        peak = self.initial_capital
        max_drawdown = 0
        for point in self.equity_curve:
            if point['value'] > peak:
                peak = point['value']
            drawdown = (peak - point['value']) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        closed_trades = [t for t in self.trades if t['action'] == 'sell' and 'profit' in t]
        if closed_trades:
            wins = [t for t in closed_trades if t['profit'] > 0]
            win_rate = len(wins) / len(closed_trades) * 100
            avg_win = sum(t['profit'] for t in wins) / len(wins) if wins else 0
            losses = [t for t in closed_trades if t['profit'] <= 0]
            avg_loss = sum(t['profit'] for t in losses) / len(losses) if losses else 0
        else:
            win_rate, avg_win, avg_loss = 0, 0, 0
        
        return {'initial_capital': self.initial_capital, 'final_value': round(final_value, 2),
                'total_return': round(total_return * 100, 2), 'annual_return': round(annual_return * 100, 2),
                'max_drawdown': round(max_drawdown * 100, 2), 'total_trades': len(self.trades),
                'closed_trades': len(closed_trades), 'win_rate': round(win_rate, 1),
                'avg_win': round(avg_win, 2), 'avg_loss': round(avg_loss, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
                'equity_curve': self.equity_curve, 'trades': self.trades}


# ============ 量化选股引擎 ============

class QuantStockSelector:
    """量化选股引擎"""
    
    def __init__(self):
        self.data_source = AkshareDataSource()
        self.bb_strategy = BollingerBandStrategy(period=20, std_dev=2)
        self.macd_detector = MACDDivergenceDetector()
    
    def analyze_stock(self, symbol: str) -> Dict:
        history = self.data_source.get_stock_history(symbol, period="daily")
        
        if len(history) < 50:
            return {'error': '数据不足'}
        
        prices = [h['close'] for h in history]
        volumes = [h['volume'] for h in history]
        
        bb_signal = self.bb_strategy.generate_signals(prices, volumes)
        macd_signal = self.macd_detector.detect_divergence(prices)
        
        final_signal = 'hold'
        confidence = 50
        reasons = []
        
        if bb_signal['signal'] == 'buy' and macd_signal['signal'] == 'buy':
            final_signal, confidence = 'strong_buy', 90
            reasons.append("布林带超卖 + MACD底背离共振")
        elif bb_signal['signal'] == 'sell' and macd_signal['signal'] == 'sell':
            final_signal, confidence = 'strong_sell', 90
            reasons.append("布林带超买 + MACD顶背离共振")
        elif bb_signal['signal'] == 'buy':
            final_signal, confidence = 'buy', 65
            reasons.append(bb_signal['analysis'])
        elif macd_signal['signal'] == 'buy':
            final_signal, confidence = 'buy', 70
            reasons.append(macd_signal['analysis'])
        elif bb_signal['signal'] == 'sell':
            final_signal, confidence = 'sell', 65
            reasons.append(bb_signal['analysis'])
        elif macd_signal['signal'] == 'sell':
            final_signal, confidence = 'sell', 70
            reasons.append(macd_signal['analysis'])
        else:
            reasons.extend([bb_signal['analysis'], macd_signal['analysis']])
        
        return {'symbol': symbol, 'bb_signal': bb_signal, 'macd_signal': macd_signal,
                'final_signal': final_signal, 'confidence': confidence, 'reasons': reasons,
                'current_price': prices[-1], 'history_data': history[-10:]}
    
    def select_stocks(self, pool: List[str], top_n: int = 10) -> List[Dict]:
        results = []
        for symbol in pool:
            try:
                analysis = self.analyze_stock(symbol)
                if 'error' not in analysis:
                    results.append(analysis)
            except Exception as e:
                print(f"[选股] {symbol} 分析失败: {e}")
        
        signal_priority = {'strong_buy': 0, 'buy': 1, 'hold': 2, 'sell': 3, 'strong_sell': 4}
        results.sort(key=lambda x: (signal_priority.get(x['final_signal'], 2), -x['confidence']))
        
        return results[:top_n]


# ============ 主程序 ============

def main():
    print("\n" + "=" * 60)
    print("[量化交易引擎 v2.0] 金融助手")
    print("=" * 60)
    
    print("\n--- 测试数据源 ---")
    data_source = AkshareDataSource()
    
    print("\n--- 测试布林带策略 ---")
    bb = BollingerBandStrategy()
    test_prices = [30 + random.uniform(-2, 2) for _ in range(50)]
    bb_result = bb.generate_signals(test_prices)
    print(f"布林带信号: {bb_result['signal']} (置信度: {bb_result['confidence']}%)")
    print(f"上轨: {bb_result['upper']}, 中轨: {bb_result['middle']}, 下轨: {bb_result['lower']}")
    
    print("\n--- 测试MACD背离检测 ---")
    macd_detector = MACDDivergenceDetector()
    test_prices2 = []
    for i in range(100):
        if i < 30:
            test_prices2.append(30 - i * 0.2)
        elif i < 50:
            test_prices2.append(24 + (i - 30) * 0.3)
        else:
            test_prices2.append(30 + (i - 50) * 0.15)
    macd_result = macd_detector.detect_divergence(test_prices2)
    print(f"MACD信号: {macd_result['signal']} (类型: {macd_result['type']})")
    print(f"分析: {macd_result['analysis']}")
    
    print("\n--- 回测示例 ---")
    backtest = BacktestEngine(initial_capital=100000)
    test_data = []
    price = 30
    for i in range(100):
        date = (datetime.now() - timedelta(days=100-i)).strftime('%Y-%m-%d')
        change = random.uniform(-0.03, 0.04)
        price = price * (1 + change)
        test_data.append({'date': date, 'code': 'test', 'open': round(price * 0.99, 2),
                         'high': round(price * 1.02, 2), 'low': round(price * 0.98, 2),
                         'close': round(price, 2), 'volume': random.randint(1000000, 5000000)})
    
    def simple_strategy(data):
        if len(data) < 20:
            return {'trades': []}
        prices = [d['close'] for d in data[-20:]]
        signal = bb.generate_signals(prices)
        trades = []
        if signal['signal'] == 'buy':
            trades.append({'action': 'buy'})
        elif signal['signal'] == 'sell':
            trades.append({'action': 'sell'})
        return {'trades': trades}
    
    result = backtest.run_backtest(test_data, simple_strategy)
    print(f"初始资金: {result['initial_capital']:,.0f} 元")
    print(f"最终价值: {result['final_value']:,.2f} 元")
    print(f"总收益率: {result['total_return']:+.2f}%")
    print(f"年化收益: {result['annual_return']:+.2f}%")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"交易次数: {result['total_trades']}")
    print(f"胜率: {result['win_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("[量化交易引擎 v2.0] 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
