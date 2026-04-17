# -*- coding: utf-8 -*-
"""竞价后点评数据收集脚本"""
import json
import urllib.request
from datetime import datetime

url = 'https://www.codebuddy.cn/v2/tool/financedata'

def call_api(api_name, params, fields=''):
    """调用金融API"""
    data = {'api_name': api_name, 'params': params}
    if fields:
        data['fields'] = fields
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. 涨停榜
print("="*60)
print("【1. 今日涨停榜】")
result = call_api('limit_list_ths', {'limit_type': '涨停池'}, 'ts_code,name,price,pct_chg,status,lu_desc,limit_order')
if result.get('code') == 0:
    fields = result['data']['fields']
    for i, item in enumerate(result['data']['items'][:15]):
        d = dict(zip(fields, item))
        print(f"{i+1}. {d['name']}({d['ts_code']}): {d['status']}, 原因={d['lu_desc'][:30] if d['lu_desc'] else 'N/A'}")

# 2. 跌停榜
print("\n" + "="*60)
print("【2. 今日跌停榜】")
result = call_api('limit_list_ths', {'limit_type': '跌停池'}, 'ts_code,name,price,pct_chg,lu_desc')
if result.get('code') == 0:
    fields = result['data']['fields']
    for i, item in enumerate(result['data']['items'][:10]):
        d = dict(zip(fields, item))
        print(f"{i+1}. {d['name']}({d['ts_code']}): 跌幅={d['pct_chg']:.2f}%")

# 3. 炸板股
print("\n" + "="*60)
print("【3. 今日炸板股】")
result = call_api('limit_list_ths', {'limit_type': '炸板池'}, 'ts_code,name,price,pct_chg,open_num')
if result.get('code') == 0:
    fields = result['data']['fields']
    for i, item in enumerate(result['data']['items'][:10]):
        d = dict(zip(fields, item))
        print(f"{i+1}. {d['name']}: 涨幅={d['pct_chg']:.2f}%, 炸板次数={d['open_num']}")

# 4. 连板股
print("\n" + "="*60)
print("【4. 连板强势股】")
result = call_api('limit_list_ths', {'limit_type': '连扳池'}, 'ts_code,name,status,lu_desc')
if result.get('code') == 0:
    fields = result['data']['fields']
    for i, item in enumerate(result['data']['items'][:10]):
        d = dict(zip(fields, item))
        print(f"{i+1}. {d['name']}: {d['status']}, 原因={d['lu_desc'][:25] if d['lu_desc'] else 'N/A'}")

# 5. 上证指数近期行情
print("\n" + "="*60)
print("【5. 上证指数近期走势】")
result = call_api('index_daily', {'ts_code': '000001.SH', 'end_date': '20260416'}, 'ts_code,trade_date,close,open,high,low,pct_change,vol,amount')
if result.get('code') == 0:
    fields = result['data']['fields']
    print("日期       收盘     开盘     最高     最低     涨跌%")
    for item in result['data']['items'][:5]:
        d = dict(zip(fields, item))
        pct = d.get('pct_change', 0)
        print(f"{d['trade_date']} {d['close']:8.2f} {d['open']:8.2f} {d['high']:8.2f} {d['low']:8.2f} {pct:+.2f}%")

# 6. 深证成指
print("\n" + "="*60)
print("【6. 深证成指近期走势】")
result = call_api('index_daily', {'ts_code': '399001.SZ', 'end_date': '20260416'}, 'trade_date,close,pct_change')
if result.get('code') == 0:
    fields = result['data']['fields']
    for item in result['data']['items'][:3]:
        d = dict(zip(fields, item))
        pct = d.get('pct_change', 0)
        print(f"{d['trade_date']}: 收盘={d['close']:.2f}, 涨跌={pct:.2f}%")

# 7. 创业板指
print("\n" + "="*60)
print("【7. 创业板指近期走势】")
result = call_api('index_daily', {'ts_code': '399006.SZ', 'end_date': '20260416'}, 'trade_date,close,pct_change')
if result.get('code') == 0:
    fields = result['data']['fields']
    for item in result['data']['items'][:3]:
        d = dict(zip(fields, item))
        pct = d.get('pct_change', 0)
        print(f"{d['trade_date']}: 收盘={d['close']:.2f}, 涨跌={pct:.2f}%")

# 8. 中兴通讯
print("\n" + "="*60)
print("【8. 中兴通讯(000063)近期走势】")
result = call_api('daily', {'ts_code': '000063.SZ', 'end_date': '20260416', 'start_date': '20260410'}, 'trade_date,open,high,low,close,pct_change,vol,amount')
if result.get('code') == 0:
    fields = result['data']['fields']
    print("日期       开盘    最高    最低    收盘    涨跌%")
    for item in result['data']['items']:
        d = dict(zip(fields, item))
        pct = d.get('pct_change', 0)
        print(f"{d['trade_date']} {d['open']:6.2f} {d['high']:6.2f} {d['low']:6.2f} {d['close']:6.2f} {pct:+.2f}%")

print("\n" + "="*60)
print("数据获取完成")
