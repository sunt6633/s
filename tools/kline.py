"""
金小融K线数据模块
数据来源：新浪财经
功能：获取日线、周线、月线历史数据，用于技术分析
"""
import requests
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

class KlineData:
    """K线数据获取器"""
    
    BASE_URL = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        })
    
    def _get_code(self, code):
        """转换代码格式"""
        if code.startswith('6') or code.startswith('9'):
            return f'sh{code}'
        else:
            return f'sz{code}'
    
    def get_daily(self, code, count=250, ma=5):
        """获取日K线数据
        
        Args:
            code: 股票代码（如 '601318'）
            count: 获取天数（默认1年交易日）
            ma: 均线周期
        
        Returns:
            list: K线数据列表
        """
        symbol = self._get_code(code)
        url = f'{self.BASE_URL}?symbol={symbol}&scale=240&ma={ma}&datalen={count}'
        
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f'获取日K线失败: {e}')
            return []
    
    def get_weekly(self, code, count=104):
        """获取周K线数据（2年）"""
        symbol = self._get_code(code)
        url = f'{self.BASE_URL}?symbol={symbol}&scale=1440&ma=5&datalen={count}'
        
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f'获取周K线失败: {e}')
            return []
    
    def get_monthly(self, code, count=120):
        """获取月K线数据（10年）"""
        symbol = self._get_code(code)
        url = f'{self.BASE_URL}?symbol={symbol}&scale=10080&ma=5&datalen={count}'
        
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f'获取月K线失败: {e}')
            return []
    
    def get_realtime(self, codes):
        """获取实时行情（多个股票）
        
        Args:
            codes: 股票代码列表，如 ['601318', '601166']
        
        Returns:
            dict: {code: {price, change, change_rate, volume, high, low, open, prev_close}}
        """
        sina_codes = [self._get_code(c) for c in codes]
        url = f'https://hq.sinajs.cn/list={",".join(sina_codes)}'
        
        try:
            r = self.session.get(url, timeout=10)
            r.encoding = 'gbk'
            
            results = {}
            lines = r.text.strip().split('\n')
            
            for i, line in enumerate(lines):
                if i < len(codes) and '=' in line:
                    code = codes[i]
                    data_str = line.split('=')[1].strip('";\n\r ')
                    parts = data_str.split(',')
                    
                    if len(parts) >= 32:
                        results[code] = {
                            'name': parts[0],
                            'open': float(parts[1]),
                            'prev_close': float(parts[2]),
                            'price': float(parts[3]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'volume': int(parts[8]),
                            'change': float(parts[3]) - float(parts[2]),
                            'change_rate': (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100
                        }
            
            return results
        except Exception as e:
            print(f'获取实时行情失败: {e}')
            return {}
    
    def to_dataframe(self, kline_data):
        """转换K线数据为DataFrame格式（字典列表）"""
        if not kline_data:
            return []
        
        rows = []
        for d in kline_data:
            rows.append({
                'date': d.get('day', ''),
                'open': float(d.get('open', 0)),
                'close': float(d.get('close', 0)),
                'high': float(d.get('high', 0)),
                'low': float(d.get('low', 0)),
                'volume': int(d.get('volume', 0)),
                'ma5': float(d.get('ma_price5', 0)) if 'ma_price5' in d else 0
            })
        
        return rows
    
    def save_csv(self, kline_data, filename):
        """保存为CSV文件"""
        rows = self.to_dataframe(kline_data)
        if not rows:
            print(f'无数据可保存')
            return False
        
        df = rows
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'open', 'close', 'high', 'low', 'volume', 'ma5'])
            writer.writeheader()
            writer.writerows(df)
        
        print(f'已保存 {len(rows)} 条数据到 {filename}')
        return True
    
    def get_ma(self, kline_data, period=5):
        """计算均线"""
        if len(kline_data) < period:
            return None
        
        closes = [float(d['close']) for d in kline_data]
        ma = sum(closes[-period:]) / period
        return round(ma, 2)
    
    def get_volatility(self, kline_data, period=20):
        """计算波动率"""
        if len(kline_data) < period:
            return None
        
        closes = [float(d['close']) for d in kline_data[-period:]]
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        
        return round(variance ** 0.5 * (252 ** 0.5), 4)  # 年化波动率


def main():
    """测试函数"""
    kline = KlineData()
    
    print("=" * 60)
    print("金小融K线数据测试")
    print("=" * 60)
    
    # 测试获取中国平安日K
    print("\n[中国平安 601318 日K线]")
    data = kline.get_daily('601318', count=60)
    if data:
        print(f"获取到 {len(data)} 条数据")
        print("\n最近10个交易日:")
        for d in data[-10:]:
            print(f"  {d['day']}: 收{d['close']} 开{d['open']} 高{d['high']} 低{d['low']} 量{d['volume']}")
        
        # 计算均线
        ma5 = kline.get_ma(data, 5)
        ma10 = kline.get_ma(data, 10)
        ma20 = kline.get_ma(data, 20)
        volatility = kline.get_volatility(data, 20)
        
        print(f"\n技术指标:")
        print(f"  MA5:  {ma5}")
        print(f"  MA10: {ma10}")
        print(f"  MA20: {ma20}")
        print(f"  波动率: {volatility}")
        
        # 保存CSV
        kline.save_csv(data, '601318_daily.csv')
    
    # 测试获取多只股票实时行情
    print("\n" + "=" * 60)
    print("[多股票实时行情]")
    realtime = kline.get_realtime(['601318', '601166', '000063'])
    for code, info in realtime.items():
        print(f"\n{info['name']} ({code}):")
        print(f"  现价: {info['price']}")
        print(f"  涨跌: {info['change']:+.2f} ({info['change_rate']:+.2f}%)")
        print(f"  今日: {info['open']} ~ {info['high']}/{info['low']}")


if __name__ == '__main__':
    main()
