"""
金小融数据源模块 v2.0
多数据源融合：AKShare > QVeris > tushare > 新浪财经
数据更全、更快、更稳定
更新时间：2026-04-17
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time

class DataSource:
    """金小融多数据源管理器 v2.0"""
    
    def __init__(self):
        self.sources_priority = ['akshare', 'qveris', 'tushare', 'sina']
        self.source_status = {}
        self._init_all_sources()
    
    def _init_all_sources(self):
        """初始化所有数据源"""
        # 1. 初始化 AKShare（最优先，免费数据源）
        try:
            import akshare as ak
            self.ak = ak
            self.source_status['akshare'] = 'ready'
            print('[数据源] AKShare v1.18.55: OK')
        except ImportError:
            self.ak = None
            self.source_status['akshare'] = 'not_installed'
            print('[数据源] AKShare: [FAIL] 未安装')
        
        # 2. 初始化 QVeris（如果有）
        try:
            from qveris import QVerisClient
            self.qveris = QVerisClient()
            self.source_status['qveris'] = 'ready'
            print('[数据源] QVeris: [OK] 已就绪')
        except:
            self.qveris = None
            self.source_status['qveris'] = 'not_configured'
            print('[数据源] QVeris: [WARN] 未配置')
        
        # 3. 初始化 tushare
        try:
            import tushare as ts
            TUSHARE_TOKEN = 'b2ae612709358581d1a15ab4d67a02e2a0b01ea23a830454833419b6'
            ts.set_token(TUSHARE_TOKEN)
            self.ts = ts.pro_api()
            self.source_status['tushare'] = 'ready'
            print('[数据源] tushare Pro: [OK] 已就绪')
        except:
            self.ts = None
            self.source_status['tushare'] = 'failed'
            print('[数据源] tushare Pro: [FAIL] 失败')
    
    def get_stock_daily(self, symbol: str, period: str = "daily", 
                        start_date: str = None, end_date: str = None,
                        adjust: str = "qfq") -> List[Dict]:
        """
        获取股票日线数据（多数据源融合）
        
        Args:
            symbol: 股票代码，如 '000001' 或 '000001.SZ'
            period: 数据周期 'daily', 'weekly', 'monthly'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            adjust: 复权类型 'qfq'前复权 'hfq'后复权 'None'不复权
        
        Returns:
            包含OHLCV数据的列表
        """
        # 标准化代码
        symbol = self._normalize_symbol(symbol)
        
        # 尝试各数据源
        if self.ak:
            try:
                data = self._get_akshare_daily(symbol, period, start_date, end_date, adjust)
                if data:
                    print('[数据源] AKShare获取{}成功: {}条'.format(symbol, len(data)))
                    return data
            except Exception as e:
                print(f'[数据源] AKShare失败: {e}')
        
        # 降级到QVeris
        if self.qveris:
            try:
                data = self._get_qveris_daily(symbol, start_date, end_date)
                if data:
                    return data
            except:
                pass
        
        # 降级到新浪
        return self._get_sina_daily(symbol.replace('.SZ', '').replace('.SH', ''))
    
    def _normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码"""
        symbol = symbol.strip().upper()
        if '.' in symbol:
            return symbol
        if symbol.startswith('6') or symbol.startswith('9'):
            return f'{symbol}.SH'
        else:
            return f'{symbol}.SZ'
    
    def _get_akshare_daily(self, symbol: str, period: str, 
                           start_date: str, end_date: str, adjust: str) -> List[Dict]:
        """AKShare获取日线数据"""
        # 转换日期格式
        if not start_date:
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 解析代码
        code = symbol.split('.')[0]
        market = 'sh' if symbol.endswith('.SH') else 'sz'
        
        # AKShare接口
        period_map = {'daily': 'daily', 'weekly': 'weekly', 'monthly': 'monthly'}
        
        df = self.ak.stock_zh_a_hist(
            symbol=code,
            period=period_map.get(period, 'daily'),
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        if df is None or len(df) == 0:
            return []
        
        # 转换为标准格式
        records = []
        for _, row in df.iterrows():
            records.append({
                'date': str(row['日期']),
                'open': float(row['开盘']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'close': float(row['收盘']),
                'volume': float(row['成交量']),
                'amount': float(row['成交额']) if '成交额' in row else 0,
                'pct_chg': float(row['涨跌幅']) if '涨跌幅' in row else 0,
                'turnover': float(row['换手率']) if '换手率' in row else 0,
                'source': 'akshare'
            })
        
        return records
    
    def _get_qveris_daily(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """QVeris获取日线数据"""
        code = symbol.replace('.SZ', '').replace('.SH', '')
        
        result = self.qveris.query(
            table='daily',
            fields='trade_date,open,high,low,close,vol,amount,pct_chg',
            where=f"ts_code='{symbol}' AND trade_date>='{start_date}' AND trade_date<='{end_date}'",
            order='trade_date'
        )
        
        if result and 'data' in result:
            return result['data']
        return []
    
    def _get_sina_daily(self, code: str, count: int = 60) -> List[Dict]:
        """新浪财经日线数据（兜底）"""
        if code.startswith('6'):
            sina_code = f'sh{code}'
        else:
            sina_code = f'sz{code}'
        
        url = f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=5&datalen={count}'
        
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            data = r.json()
            
            records = []
            for d in data:
                records.append({
                    'date': d['day'],
                    'open': float(d['open']),
                    'high': float(d['high']),
                    'low': float(d['low']),
                    'close': float(d['close']),
                    'volume': int(d['volume']),
                    'source': 'sina'
                })
            return records
        except Exception as e:
            print(f'[数据源] 新浪财经失败: {e}')
            return []
    
    def get_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取实时行情（批量）"""
        results = {}
        
        # AKShare实时行情
        if self.ak:
            try:
                codes = [s.split('.')[0] for s in symbols]
                df = self.ak.stock_zh_a_spot_em()
                
                for code in codes:
                    row = df[df['代码'] == code]
                    if not row.empty:
                        r = row.iloc[0]
                        results[code] = {
                            'name': r['名称'],
                            'price': float(r['最新价']) if r['最新价'] != '-' else 0,
                            'change': float(r['涨跌额']) if r['涨跌额'] != '-' else 0,
                            'pct_chg': float(r['涨跌幅']) if r['涨跌幅'] != '-' else 0,
                            'open': float(r['今开']) if r['今开'] != '-' else 0,
                            'high': float(r['最高']) if r['最高'] != '-' else 0,
                            'low': float(r['最低']) if r['最低'] != '-' else 0,
                            'volume': float(r['成交量']) if r['成交量'] != '-' else 0,
                            'amount': float(r['成交额']) if r['成交额'] != '-' else 0,
                            'turnover': float(r['换手率']) if r['换手率'] != '-' else 0,
                            'pe': float(r['市盈率-动态']) if r['市盈率-动态'] != '-' else 0,
                            'source': 'akshare'
                        }
                if results:
                    print(f'[数据源] AKShare实时行情成功: {len(results)}只')
                    return results
            except Exception as e:
                print(f'[数据源] AKShare实时行情失败: {e}')
        
        # 降级到新浪
        return self._get_sina_realtime(symbols)
    
    def _get_sina_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """新浪实时行情（兜底）"""
        sina_codes = []
        for code in symbols:
            c = code.replace('.SZ', '').replace('.SH', '')
            if c.startswith('6'):
                sina_codes.append(f'sh{c}')
            else:
                sina_codes.append(f'sz{c}')
        
        url = f'https://hq.sinajs.cn/list={",".join(sina_codes)}'
        
        try:
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.sina.com.cn'
            }, timeout=10)
            r.encoding = 'gbk'
            
            results = {}
            lines = r.text.strip().split('\n')
            
            for i, line in enumerate(lines):
                if i < len(symbols) and '=' in line:
                    code = symbols[i].replace('.SZ', '').replace('.SH', '')
                    parts = line.split('=')[1].strip('";\n\r ').split(',')
                    
                    if len(parts) >= 32:
                        price = float(parts[3])
                        prev_close = float(parts[2])
                        change = price - prev_close
                        pct_chg = (change / prev_close * 100) if prev_close else 0
                        
                        results[code] = {
                            'name': parts[0],
                            'price': price,
                            'change': change,
                            'pct_chg': pct_chg,
                            'open': float(parts[1]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'volume': int(parts[8]),
                            'amount': float(parts[9]) if len(parts) > 9 else 0,
                            'source': 'sina'
                        }
            return results
        except Exception as e:
            print(f'[数据源] 新浪实时行情失败: {e}')
            return {}
    
    def get_money_flow(self, symbol: str) -> Dict:
        """获取资金流向数据（AKShare特色功能）"""
        if not self.ak:
            return {}
        
        try:
            code = symbol.replace('.SZ', '').replace('.SH', '').replace('.sz', '').replace('.sh', '')
            
            df = self.ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith('6') else "sz")
            
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                return {
                    'date': str(latest.get('日期', '')),
                    '主力净流入': float(latest.get('主力净流入-净额', 0)),
                    '散户净流入': float(latest.get('散户净流入-净额', 0)),
                    '主力净流入占比': float(latest.get('主力净流入-占比', 0)),
                    'source': 'akshare'
                }
        except Exception as e:
            print(f'[数据源] 资金流向获取失败: {e}')
        
        return {}
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        if not self.ak:
            return {}
        
        try:
            code = symbol.replace('.SZ', '').replace('.SH', '').replace('.sz', '').replace('.sh', '')
            
            df = self.ak.stock_info_a_code_name()
            row = df[df['code'] == code]
            
            if not row.empty:
                return {
                    'code': code,
                    'name': row.iloc[0]['name'],
                    'industry': '',  # 需要额外查询
                    'source': 'akshare'
                }
        except Exception as e:
            print(f'[数据源] 股票信息获取失败: {e}')
        
        return {}
    
    def get_market_hot(self) -> List[Dict]:
        """获取市场热点板块（AKShare特色功能）"""
        if not self.ak:
            return []
        
        try:
            # 东方财富板块排名
            df = self.ak.stock_board_concept_name_em()
            
            if df is not None and len(df) > 0:
                hot_list = []
                for _, row in df.head(20).iterrows():
                    hot_list.append({
                        'name': row['名称'],
                        'price_change': float(row['涨跌幅']) if '涨跌幅' in row else 0,
                        'volume': float(row['成交量']) if '成交量' in row else 0,
                        'turnover': float(row['换手率']) if '换手率' in row else 0,
                        'leader_stock': row.get('领涨股票', ''),
                        'source': 'akshare'
                    })
                return hot_list
        except Exception as e:
            print(f'[数据源] 热点板块获取失败: {e}')
        
        return []
    
    def calculate_technical_indicators(self, records: List[Dict]) -> Dict:
        """计算技术指标"""
        if len(records) < 5:
            return {}
        
        closes = [r['close'] for r in records]
        volumes = [r['volume'] for r in records]
        
        # 均线
        ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else 0
        ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else 0
        
        # RSI
        delta = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gain = sum([d for d in delta if d > 0])
        loss = abs(sum([d for d in delta if d < 0]))
        rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 100
        
        # MACD
        ema12 = self._calc_ema(closes, 12)
        ema26 = self._calc_ema(closes, 26)
        dif = ema12 - ema26
        dea = self._calc_ema([dif] * len(closes), 9) if len(closes) >= 9 else dif
        macd = (dif - dea) * 2
        
        # KDJ
        low9 = min([r['low'] for r in records[-9:]])
        high9 = max([r['high'] for r in records[-9:]])
        rsv = ((closes[-1] - low9) / (high9 - low9) * 100) if high9 != low9 else 50
        k = 50  # 简化计算
        d = 50
        j = 3 * k - 2 * d
        
        return {
            'ma5': round(ma5, 2),
            'ma10': round(ma10, 2),
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2),
            'ma_cross': {
                'ma5_above_ma10': ma5 > ma10,
                'ma10_above_ma20': ma10 > ma20,
                'ma20_above_ma60': ma20 > ma60
            },
            'rsi': round(rsi, 2),
            'macd': {
                'dif': round(dif, 3),
                'dea': round(dea, 3),
                'histogram': round(macd, 3)
            },
            'kdj': {'k': round(k, 2), 'd': round(d, 2), 'j': round(j, 2)},
            'volume_ratio': volumes[-1] / (sum(volumes[-5:]) / 5) if sum(volumes[-5:]) > 0 else 1
        }
    
    def _calc_ema(self, data: List[float], period: int) -> float:
        """计算指数移动平均"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def get_brief_status(self) -> str:
        """获取数据源状态摘要"""
        status = []
        for source, state in self.source_status.items():
            emoji = '[OK]' if state == 'ready' else ('[WARN]' if state != 'failed' else '[FAIL]')
            status.append(f"{emoji}{source}: {state}")
        return ' | '.join(status)


def test_multi_source():
    """测试多数据源"""
    ds = DataSource()
    
    print('\n' + '=' * 60)
    print('多数据源融合测试')
    print('=' * 60)
    
    # 1. 测试日线数据
    print('\n[1] 日线数据测试 - 中国平安 601318')
    data = ds.get_stock_daily('601318', start_date='20260401', end_date='20260417')
    if data:
        print(f'  [OK] 获取 {len(data)} 条数据')
        for d in data[-3:]:
            print(f"     {d['date']}: 收{d['close']} 涨跌{d.get('pct_chg', 0):+.2f}% 换手{d.get('turnover', 0):.2f}%")
    
    # 2. 测试实时行情
    print('\n[2] 实时行情测试')
    realtime = ds.get_realtime_quote(['601318', '600036', '000063'])
    for code, info in realtime.items():
        print(f"  {info.get('name', code)} ({code}): {info['price']} ({info['pct_chg']:+.2f}%)")
    
    # 3. 测试热点板块
    print('\n[3] 热点板块测试')
    hot = ds.get_market_hot()[:5]
    for h in hot:
        print(f"  {h['name']}: {h['price_change']:+.2f}%")
    
    # 4. 测试资金流向
    print('\n[4] 资金流向测试 - 中兴通讯 000063')
    flow = ds.get_money_flow('000063')
    if flow:
        print(f"  主力净流入: {flow.get('主力净流入', 0):,.0f}")
    
    # 5. 状态总结
    print('\n[5] 数据源状态')
    print(f"  {ds.get_brief_status()}")


if __name__ == '__main__':
    test_multi_source()
