"""
金小融数据源模块
支持多数据源：tushare Pro > 新浪财经 > akshare
"""
import requests
import json
from pathlib import Path

# tushare Pro配置
TUSHARE_TOKEN = 'b2ae612709358581d1a15ab4d67a02e2a0b01ea23a830454833419b6'


class DataSource:
    """金小融数据源管理器"""
    
    def __init__(self):
        self.ts = None
        self._init_tushare()
    
    def _init_tushare(self):
        """初始化tushare Pro"""
        try:
            import tushare as ts
            ts.set_token(TUSHARE_TOKEN)
            self.ts = ts.pro_api()
            print('[数据源] tushare Pro: 已连接')
        except ImportError:
            print('[数据源] tushare: 未安装')
            self.ts = None
        except Exception as e:
            print(f'[数据源] tushare Pro: {e}')
            self.ts = None
    
    def get_daily(self, code, start_date=None, end_date=None):
        """获取日线数据
        
        优先级: tushare Pro > 新浪财经 > akshare
        """
        # 标准化代码格式
        ts_code = self._to_ts_code(code)
        
        # 尝试tushare Pro
        if self.ts:
            try:
                df = self.ts.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    return self._df_to_records(df)
            except Exception as e:
                print(f'[数据源] tushare Pro失败: {e}')
        
        # 降级到新浪财经
        return self._get_sina_daily(code)
    
    def _to_ts_code(self, code):
        """转换为tushare格式"""
        code = code.strip()
        if '.' in code:
            return code
        if code.startswith('6') or code.startswith('9'):
            return f'{code}.SH'
        else:
            return f'{code}.SZ'
    
    def _df_to_records(self, df):
        """DataFrame转records"""
        records = []
        for _, row in df.iterrows():
            records.append({
                'date': str(row['trade_date']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['vol']),
                'amount': float(row['amount']),
                'pct_chg': float(row['pct_chg']),
                'change': float(row['change'])
            })
        return records
    
    def _get_sina_daily(self, code, count=60):
        """新浪财经日线数据（备用）"""
        import requests
        
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
                    'volume': int(d['volume'])
                })
            return records
        except Exception as e:
            print(f'[数据源] 新浪财经失败: {e}')
            return []
    
    def get_realtime(self, codes):
        """获取实时行情"""
        if self.ts:
            try:
                # tushare Pro实时
                df = self.ts.daily(ts_code=self._to_ts_code(codes[0]), 
                                   trade_date='20260417')
                if df is not None and len(df) > 0:
                    return self._df_to_records(df)
            except:
                pass
        
        # 降级到新浪
        return self._get_sina_realtime(codes)
    
    def _get_sina_realtime(self, codes):
        """新浪实时行情"""
        import requests
        
        sina_codes = []
        for code in codes:
            if code.startswith('6'):
                sina_codes.append(f'sh{code}')
            else:
                sina_codes.append(f'sz{code}')
        
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
                if i < len(codes) and '=' in line:
                    code = codes[i]
                    parts = line.split('=')[1].strip('";\n\r ').split(',')
                    if len(parts) >= 32:
                        results[code] = {
                            'price': float(parts[3]),
                            'prev_close': float(parts[2]),
                            'open': float(parts[1]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'volume': int(parts[8])
                        }
            return results
        except Exception as e:
            print(f'[数据源] 新浪实时失败: {e}')
            return {}
    
    def calculate_ma(self, records, period=5):
        """计算均线"""
        if len(records) < period:
            return None
        closes = [r['close'] for r in records[-period:]]
        return sum(closes) / period
    
    def calculate_volatility(self, records, period=20):
        """计算波动率"""
        if len(records) < period:
            return None
        closes = [r['close'] for r in records[-period:]]
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return round(variance ** 0.5 * (252 ** 0.5), 4)


def main():
    """测试数据源"""
    ds = DataSource()
    
    print('\n' + '=' * 50)
    print('数据源测试')
    print('=' * 50)
    
    # 测试日线数据
    print('\n[中国平安 601318 日线]')
    data = ds.get_daily('601318', '20260401', '20260417')
    if data:
        print(f'获取 {len(data)} 条数据')
        for d in data:
            print(f"  {d['date']}: 收{d['close']} 涨跌{d.get('pct_chg', 0):.2f}%")
        
        # 计算指标
        ma5 = ds.calculate_ma(data, 5)
        ma10 = ds.calculate_ma(data, 10)
        vol = ds.calculate_volatility(data, 10)
        print(f'\n技术指标: MA5={ma5:.2f}, MA10={ma10:.2f}, 波动率={vol}')
    
    # 测试实时行情
    print('\n[实时行情]')
    realtime = ds.get_realtime(['601318', '601166'])
    for code, info in realtime.items():
        change = info['price'] - info['prev_close']
        pct = change / info['prev_close'] * 100
        print(f"  {code}: {info['price']} ({pct:+.2f}%)")


if __name__ == '__main__':
    main()
