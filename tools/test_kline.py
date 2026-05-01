"""测试历史K线数据接口"""
import requests
import re

def get_tx_kline(code, count=100):
    """腾讯财经K线数据"""
    if code.startswith('6'):
        tx_code = 'sh' + code
    else:
        tx_code = 'sz' + code
    
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq&param={tx_code},day,,,{count},qfq'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.text
        
        match = re.search(r'"data":\{.*?"day":\[(.*?)\]', data, re.DOTALL)
        if match:
            days = match.group(1)
            rows = re.findall(r'\[([^\]]+)\]', days)
            print(f'{code} 腾讯财经 最近{len(rows)}个交易日:')
            for row in rows[-5:]:
                parts = row.split(',')
                print(f"  {parts[0]}: 收{parts[4]} 开{parts[1]} 高{parts[2]} 低{parts[3]}")
            return rows
    except Exception as e:
        print(f'腾讯失败: {e}')
    return None

def get_sina_kline(code, count=100):
    """新浪财经K线"""
    if code.startswith('6'):
        sina_code = 'sh' + code
    else:
        sina_code = 'sz' + code
    
    url = f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=5&datalen={count}'
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data:
            print(f'{code} 新浪财经 最近{len(data)}条日K:')
            for d in data[-5:]:
                print(f"  {d['day']}: 收{d['close']} 开{d['open']} 高{d['high']} 低{d['low']}")
            return data
    except Exception as e:
        print(f'新浪失败: {e}')
    return None

if __name__ == '__main__':
    print("=" * 50)
    print("测试历史K线数据接口")
    print("=" * 50)
    
    # 腾讯财经
    print("\n[腾讯财经]")
    get_tx_kline('601318', 20)  # 中国平安
    get_tx_kline('601166', 20)  # 兴业银行
    
    # 新浪财经
    print("\n[新浪财经]")
    get_sina_kline('601318', 20)
    get_sina_kline('601166', 20)
