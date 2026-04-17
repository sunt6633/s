"""测试tushare Pro接口"""
import tushare as ts

# 设置token
TOKEN = 'b2ae612709358581d1a15ab4d67a02e2a0b01ea23a830454833419b6'
ts.set_token(TOKEN)
pro = ts.pro_api()

print('=' * 60)
print('tushare Pro 接口测试')
print('=' * 60)

# 日线数据
print('\n[中国平安 601318]')
df = pro.daily(ts_code='601318.SH', start_date='20260401', end_date='20260417')
print(df)

print('\n[兴业银行 601166]')
df = pro.daily(ts_code='601166.SH', start_date='20260401', end_date='20260417')
print(df)

print('\n[贵州茅台 600519]')
df = pro.daily(ts_code='600519.SH', start_date='20260401', end_date='20260417')
print(df)

# 保存token配置
print('\n[保存token配置]')
with open('D:/for workbuddy/finance_bot/tushare_token.py', 'w') as f:
    f.write('TUSHARE_TOKEN = "b2ae612709358581d1a15ab4d67a02e2a0b01ea23a830454833419b6"\n')
print('token已保存')
