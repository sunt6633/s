import requests
import json

# QVeris API配置
API_KEY = "sk-IyZdtwa93h9l4UJVz0Bay3tZS15VAtcoa6gkD68ws2M"
BASE_URL = "https://qveris.com/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 获取中国平安和兴业银行实时行情
stocks = [
    ("601318.SH", "中国平安"),
    ("601166.SH", "兴业银行")
]

for ts_code, name in stocks:
    try:
        # 尝试获取实时行情
        url = f"{BASE_URL}/quote/stock/{ts_code}"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"{name}: {data}")
        else:
            # 尝试日线数据
            url = f"{BASE_URL}/quote/daily"
            params = {"code": ts_code, "limit": 1}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"{name}: {data}")
            else:
                print(f"{name}: API请求失败 - {resp.status_code}")
    except Exception as e:
        print(f"{name}: 请求错误 - {e}")
