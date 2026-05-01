# -*- coding: utf-8 -*-
"""测试备用API - 查看完整返回数据"""
import requests
import json

api_key = 'sk-pjcd0aHC4wuOTxfJM1N7g7MRyVtxIXze_DwM-ycO9d0'
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

BASE_URL = 'https://qveris.ai/api/v1'

print("=== 测试备用API - 完整数据 ===\n")

# 获取搜索ID
search_data = {'query': 'A股股票实时价格查询', 'limit': 1}
try:
    resp = requests.post(f'{BASE_URL}/search', headers=headers, json=search_data, timeout=15)
    result = resp.json()
    search_id = result.get('search_id')
    print(f"搜索ID: {search_id}")

    if search_id:
        # 获取中国平安价格 - 尝试带.SH后缀
        tool_id = "caidazi.get_real_time_record.execute.v1.7a43f96e"
        call_data = {
            'parameters': {'symbol': '601318.SH'},
            'search_id': search_id,
            'max_response_size': 20480
        }
        resp2 = requests.post(
            f'{BASE_URL}/tools/execute?tool_id={tool_id}',
            headers=headers,
            json=call_data,
            timeout=15
        )
        result2 = resp2.json()

        # 打印完整result字段
        result_text = result2.get('result', {}).get('data', {}).get('result', '')
        print("完整返回:")
        print(result_text)
        print("\n\n--- 分析 ---")
        print(f"result字段长度: {len(result_text)}")
        print(f"行数: {len(result_text.split(chr(10)))}")
except Exception as e:
    print(f'请求失败: {e}')
    import traceback
    traceback.print_exc()
