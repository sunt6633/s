#!/usr/bin/env python3
"""更新股票池实时行情"""
import json
import sys
sys.path.insert(0, 'D:/for workbuddy/finance_bot')
from data_source import DataSource

def main():
    ds = DataSource()
    
    # 读取现有股票池
    with open('D:/for workbuddy/finance_bot/portfolio.json', 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    pool = portfolio.get('stock_pool', [])
    print(f'当前股票池有 {len(pool)} 只股票')
    
    # 提取所有股票代码
    codes = [s['code'] for s in pool]
    
    # 批量获取实时行情
    print('正在获取实时行情...')
    realtime = ds.get_realtime(codes)
    
    # 更新股票池
    updated = 0
    for stock in pool:
        code = stock['code']
        if code in realtime:
            real = realtime[code]
            old_price = stock.get('price', 0)
            new_price = real['price']
            prev_close = real['prev_close']
            pct_chg = ((new_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            # 更新字段
            stock['price'] = new_price
            stock['prev_close'] = prev_close
            stock['change_rate'] = pct_chg
            stock['volume'] = real['volume']
            stock['update_time'] = real.get('time', '')
            
            updated += 1
    
    print(f'已更新 {updated} 只股票')
    
    # 保存更新后的数据
    portfolio['stock_pool'] = pool
    portfolio['portfolio']['last_pool_update'] = '2026-04-17 15:43:00'
    
    with open('D:/for workbuddy/finance_bot/portfolio.json', 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    
    print('已保存到 portfolio.json')
    
    # 显示更新后的部分数据
    print()
    print('=== 更新后的前10只股票 ===')
    print('代码      名称           价格       涨跌幅')
    print('-' * 45)
    for stock in pool[:10]:
        pct = stock.get('change_rate', 0)
        print(f"{stock['code']}  {stock['name']:<10}  {stock['price']:>10.2f}  {pct:>+8.2f}%")

if __name__ == '__main__':
    main()
