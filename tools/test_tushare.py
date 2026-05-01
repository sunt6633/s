"""测试tushare数据接口"""
import tushare as ts

print("=" * 50)
print("tushare数据能力测试")
print("=" * 50)

# 实时行情
print("\n[实时行情]")
try:
    df = ts.get_realtime_quotes(['601318', '601166', '000063'])
    print(df[['code', 'name', 'price', 'volume', 'amount']])
except Exception as e:
    print(f"失败: {e}")

# 今日行情
print("\n[今日全部行情]")
try:
    df = ts.get_today_all()
    stocks = df[df['code'].isin(['601318', '601166', '000063'])]
    print(stocks[['code', 'name', 'price', 'changepercent', 'volume']])
except Exception as e:
    print(f"失败: {e}")

print("\n" + "=" * 50)
print("tushare说明:")
print("  - 基础版: 免费，实时行情、基础数据")
print("  - Pro版: 注册获取token，功能更全")
print("  - 注册地址: https://tushare.pro")
print("=" * 50)
