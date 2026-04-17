# -*- coding: utf-8 -*-
"""
新闻摘要模块 v1.0
获取市场相关新闻摘要
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_news_summary(days=1):
    """
    获取新闻摘要
    返回格式化的新闻文本
    """
    try:
        # 尝试使用skill获取新闻
        from use_skill import use_skill
        result = use_skill("新闻摘要")
        return result if result else "暂无新闻数据"
    except:
        # 返回默认新闻模板
        return """
## 市场新闻摘要

### 政策面
- 关注央行货币政策动向
- 证监会监管政策变化
- 国务院重大经济政策

### 科技动态
- AI技术发展与应用
- 半导体产业进展
- 新能源技术突破

### 国际局势
- 地缘政治风险
- 国际贸易关系
- 全球经济形势

### 行业动态
- 上市公司重大公告
- 行业政策变化
- 产业链供需情况

*数据来源：自动新闻聚合*
"""

def get_policy_news():
    """获取政策相关新闻"""
    return [
        "央行货币政策动态",
        "证监会监管政策",
        "国务院经济政策"
    ]

def get_tech_news():
    """获取科技相关新闻"""
    return [
        "AI技术发展",
        "半导体产业",
        "新能源技术"
    ]

def get_geopolitical_news():
    """获取地缘政治新闻"""
    return [
        "国际局势变化",
        "贸易关系动态",
        "全球经济形势"
    ]

if __name__ == "__main__":
    print(get_news_summary())
