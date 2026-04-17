"""
金小融实时行情自动更新
使用新浪财经接口，自动获取持仓股票实时价格
"""
import requests
import json
from datetime import datetime

def get_realtime_prices(codes_dict):
    """
    获取实时行情
    codes_dict: {'000063': '中兴通讯', '601318': '中国平安', '601166': '兴业银行'}
    """
    # 构造新浪接口代码
    sina_codes = []
    for code in codes_dict.keys():
        if code.startswith('0') or code.startswith('3'):
            sina_codes.append(f'sz{code}')
        else:
            sina_codes.append(f'sh{code}')
    
    url = f'https://hq.sinajs.cn/list={",".join(sina_codes)}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'gbk'
        
        results = {}
        lines = r.text.strip().split('\n')
        code_list = list(codes_dict.keys())
        
        for i, line in enumerate(lines):
            if i < len(code_list):
                code = code_list[i]
                name = codes_dict[code]
                
                # 解析数据
                if '=' in line:
                    data_str = line.split('=')[1].strip('";\n\r ')
                    parts = data_str.split(',')
                    
                    if len(parts) >= 32:
                        results[code] = {
                            'name': name,
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'current': float(parts[3]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'volume': int(parts[8]),
                            'date': parts[30],
                            'time': parts[31],
                        }
        
        return results
        
    except Exception as e:
        print(f'获取行情失败: {e}')
        return None


def update_portfolio():
    """更新持仓数据"""
    with open('portfolio.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    codes = {p['code']: p['name'] for p in data['positions']}
    prices = get_realtime_prices(codes)
    
    if not prices:
        print('获取行情失败')
        return False
    
    print('=' * 60)
    print(f'实时行情更新 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)
    print('标的        现价      涨跌      涨跌幅      状态')
    print('-' * 60)
    
    total_profit = 0
    
    for pos in data['positions']:
        code = pos['code']
        if code in prices:
            p = prices[code]
            pos['current_price'] = p['current']
            pos['current_price_time'] = f"{p['date']} {p['time']}"
            
            market_value = p['current'] * pos['shares']
            cost = pos['avg_cost'] * pos['shares']
            pos['profit'] = market_value - cost
            pos['profit_rate'] = (pos['profit'] / cost) * 100
            pos['market_value'] = market_value
            total_profit += pos['profit']
            
            change = p['current'] - p['close']
            change_rate = (change / p['close']) * 100
            
            if pos['profit_rate'] >= 15:
                status = '止盈信号'
            elif pos['profit_rate'] <= -8:
                status = '止损信号'
            else:
                status = '正常'
            
            emoji = '+' if change > 0 else '-' if change < 0 else '='
            print(f"{p['name']:<10} {p['current']:>8.2f} {change:>+8.2f} {change_rate:>+10.2f}% {emoji} {status}")
    
    data['portfolio']['current_capital'] = data['portfolio']['initial_capital'] + total_profit
    data['portfolio']['total_profit'] = total_profit
    data['portfolio']['total_profit_rate'] = (total_profit / data['portfolio']['initial_capital']) * 100
    
    print('-' * 60)
    print(f"总盈亏: {total_profit:+,.2f}元 ({total_profit/data['portfolio']['initial_capital']*100:+.2f}%)")
    print(f"总资产: {data['portfolio']['current_capital']:,.2f}元")
    
    with open('portfolio.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print('=' * 60)
    print('数据已更新')
    
    return True


if __name__ == '__main__':
    update_portfolio()
