# -*- coding: utf-8 -*-
"""
QVeris API 管理模块
支持多API轮换使用，均衡消耗积分
"""

# API列表（按优先级排序）
API_KEYS = [
    "sk-pjcd0aHC4wuOTxfJM1N7g7MRyVtxIXze_DwM-ycO9d0",  # 主用（有2089积分）
    "sk-IyZdtwa93h9l4UJVz0Bay3tZS15VAtcoa6gkD68ws2M",  # 备用（积分耗尽）
]

# 当前使用的API索引
_current_index = 0

def get_current_api_key():
    """获取当前API Key"""
    global _current_index
    return API_KEYS[_current_index]

def switch_api():
    """切换到下一个API"""
    global _current_index
    _current_index = (_current_index + 1) % len(API_KEYS)
    return API_KEYS[_current_index]

def get_all_apis():
    """获取所有API"""
    return API_KEYS.copy()

# Base URL
BASE_URL = "https://qveris.ai/api/v1"
