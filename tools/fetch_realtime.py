import requests
import json

# 获取实时行情
stocks = ['601318.SH', '601166.SH']

for ts_code in stocks:
    url = 'https://www.codebuddy.cn/v2/tool/financedata'
    data = {
        'api_name': 'rt_k',
        'params': {'ts_code': ts_code},
        'fields': ''
    }
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        
        if result.get('code') == 0:
            fields = result['data']['fields']
            items = result['data']['items']
            if items:
                item = items[0]
                name = item[1]  # name
                close = item[6]  # close (最新价)
                change = ((close - item[2]) / item[2] * 100) if item[2] else 0  # 涨跌幅
                print(f'{name} {ts_code}: 最新价={close}, 涨跌幅={change:+.2f}%')
        else:
            print(f'{ts_code}: 获取失败 - {result.get("msg")}')
    except Exception as e:
        print(f'{ts_code}: 请求错误 - {e}')
