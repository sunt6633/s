# -*- coding: utf-8 -*-
"""
股票池管理器 - 金融助手
每日自动更新股票池数据

功能：
1. 调用v6.0选股系统获取最新评分
2. 获取实时行情数据
3. 保存股票池到stock_pool.json
4. 生成观察列表和推荐列表

运行时间：每日 08:30（开盘前）
"""

import json
import os
import sys
from datetime import datetime

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_POOL_FILE = os.path.join(BASE_DIR, "stock_pool.json")
SELECTOR_FILE = os.path.join(BASE_DIR, "stock_selector_v6.py")

def get_qveris_data(codes):
    """从QVeris API获取实时行情"""
    try:
        import requests
        
        api_key = "sk-IyZdtwa93h9l4UJVz0Bay3tZS15VAtcoa6gkD68ws2M"
        
        results = []
        for code in codes:
            # 转换代码格式
            if code.startswith("6"):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
            
            url = "https://qveris.com/api/v1/stock/daily"
            params = {
                "ts_code": ts_code,
                "api_key": api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data"):
                    item = data["data"][-1]  # 最新一天
                    results.append({
                        "code": code,
                        "price": item.get("close", 0),
                        "change_rate": item.get("pct_chg", 0),
                        "volume": item.get("vol", 0),
                        "turnover": item.get("turnover_rate", 0)
                    })
        return results
    except Exception as e:
        print(f"QVeris API调用失败: {e}")
        return []

def load_selector_module():
    """动态加载选股模块"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("selector", SELECTOR_FILE)
    selector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(selector)
    return selector

def update_stock_pool():
    """主函数：更新股票池"""
    print("=" * 50)
    print("📊 股票池更新任务启动")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 加载选股模块
    selector = load_selector_module()
    
    # 获取股票列表
    stock_pool = selector.get_real_stocks_v6()
    
    # 获取实时行情（简化处理，使用选股系统的价格）
    codes = [s["code"] for s in stock_pool]
    
    # 尝试获取QVeris数据
    market_data = get_qveris_data(codes)
    market_dict = {d["code"]: d for d in market_data}
    
    # 更新股票池数据
    updated_pool = []
    for stock in stock_pool:
        code = stock["code"]
        
        # 优先使用实时数据
        if code in market_dict:
            market = market_dict[code]
            stock["price"] = market.get("price", stock.get("price", 0))
            stock["change_rate"] = market.get("change_rate", 0)
        
        # 计算综合评分
        scores = stock.get("scores", {})
        composite = scores.get("composite", 0)
        
        updated_pool.append({
            "code": code,
            "name": stock["name"],
            "sector": stock["sector"],
            "price": stock.get("price", 0),
            "change_rate": stock.get("change_rate", 0),
            "change_rate_display": f"{stock.get('change_rate', 0):+.2f}%",
            "score": composite,
            "signal": stock.get("signal", "观望"),
            "fundamental": stock.get("fundamental", {}),
            "tech": stock.get("tech", {}),
            "scores": scores,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 按综合评分排序
    updated_pool.sort(key=lambda x: x["score"], reverse=True)
    
    # 添加排名
    for i, stock in enumerate(updated_pool):
        stock["rank"] = i + 1
    
    # 保存到文件
    result = {
        "update_date": datetime.now().strftime("%Y-%m-%d"),
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_stocks": len(updated_pool),
        "stocks": updated_pool,
        "top_picks": [s for s in updated_pool if s["score"] >= 55][:5],
        "watch_list": [s for s in updated_pool if 45 <= s["score"] < 55][:10]
    }
    
    with open(STOCK_POOL_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 股票池更新完成！")
    print(f"📊 总股票数: {len(updated_pool)}")
    print(f"⭐ 重点关注: {len(result['top_picks'])} 只")
    print(f"👀 观察列表: {len(result['watch_list'])} 只")
    print(f"📁 保存位置: {STOCK_POOL_FILE}")
    
    # 显示前5名
    print("\n🏆 TOP 5 股票：")
    print("-" * 60)
    for stock in result["top_picks"][:5]:
        print(f"{stock['rank']:2}. {stock['name']} ({stock['code']}) | "
              f"现价:{stock['price']} | 涨跌:{stock['change_rate_display']} | "
              f"评分:{stock['score']} | 信号:{stock['signal']}")
    
    return result

if __name__ == "__main__":
    update_stock_pool()
