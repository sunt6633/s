# -*- coding: utf-8 -*-
"""快速查询持仓股票价格"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_source import get_realtime_price_qveris

stocks = ['000063', '601318', '601166']  # 中兴通讯、中国平安、兴业银行

print("=" * 50)
print("持仓股票实时价格查询")
print("=" * 50)

for code in stocks:
    price = get_realtime_price_qveris(code)
    print(f"{code}: {price}")
