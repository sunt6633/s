# -*- coding: utf-8 -*-
"""
盘前分析模块 v1.0 (2026-04-16)
孙先生新任务：集合竞价前的综合分析

功能：
1. 收集信息（政策面、重大事件、科技、战争等）
2. 综合分析市场前景
3. 预测评估受益/受损股票
4. 集合竞价结束后点评
5. 找出资金活跃股
"""

import sys
import os
from datetime import datetime
from news_summary import get_news_summary

# stock_picker 模块不存在，使用替代方案
try:
    from stock_picker import get_ai_stock_picks
except ImportError:
    def get_ai_stock_picks():
        return []

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_market_news():
    """获取市场相关新闻"""
    try:
        news = get_news_summary(days=1)
        return news
    except Exception as e:
        return f"新闻获取失败: {str(e)}"

def analyze_market_sentiment():
    """分析市场情绪"""
    try:
        # 获取当日涨跌停数量
        from stock_selector_v6 import get_limit_list
        up_limit, down_limit = get_limit_list()
        return up_limit, down_limit
    except:
        return None, None

def get_hot_sectors():
    """获取热门板块"""
    try:
        from stock_selector_v6 import get_sector_flow
        sectors = get_sector_flow()
        return sectors
    except:
        return []

def generate_pre_market_report():
    """
    生成盘前分析报告
    """
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""
# 📊 盘前分析报告
**日期**: {today}  
**生成时间**: {current_time}

---

## 一、市场情绪监测

| 指标 | 数据 |
|------|------|
| 涨跌停数量 | 涨停: - / 跌停: - |
| 热门板块 | 加载中... |
| 资金流向 | 加载中... |

---

## 二、政策与重大事件

**孙先生，以下信息需结合实时数据：**

1. **政策面**：关注官方政策发布（央行、证监会、国务院等）
2. **科技动态**：AI、半导体、新能源等领域重大突破
3. **地缘政治**：国际局势对A股的影响（如有战争、制裁等）
4. **重大事件**：上市公司重大公告、行业政策变化

---

## 三、综合分析预测

### 市场前景判断
- **整体趋势**: [待分析]
- **主要驱动因素**: [待分析]
- **风险提示**: [待分析]

### 受益板块/股票预测
| 板块 | 逻辑 | 关注股票 |
|------|------|----------|
| [待定] | [待分析] | [待定] |

### 可能受损板块/股票预警
| 板块 | 逻辑 | 关注股票 |
|------|------|----------|
| [待定] | [待分析] | [待定] |

---

## 四、集合竞价点评（9:25后更新）

竞价结束后填写：
- 高开/低开股票
- 竞价量能异常股
- 资金活跃方向

---

## 五、资金活跃股关注

**待竞价结束后分析**

---

*本报告由金小融自动生成，每日更新*
"""
    
    return report

def generate_post_auction_review():
    """
    生成集合竞价后点评
    """
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""
# ⚡ 集合竞价点评
**日期**: {today}  
**生成时间**: {current_time}（竞价结束后）

---

## 一、竞价概况

| 指标 | 观察 |
|------|------|
| 竞价涨跌 | [待观察] |
| 竞价量能 | [待观察] |
| 异常竞价 | [待观察] |

---

## 二、资金活跃方向

**重点关注以下方向：**

1. [ ] 科技主线（AI、半导体）
2. [ ] 新能源赛道
3. [ ] 防御板块（医药、消费）
4. [ ] 热点题材

---

## 三、当日交易策略建议

- **仓位建议**: [待定]
- **重点关注**: [待定]
- **风险提示**: [待定]

---

*金小融提醒：以上仅为分析参考，不构成投资建议*
"""
    
    return report

def save_report(content, filename):
    """保存报告"""
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "pre_market")
    os.makedirs(reports_dir, exist_ok=True)
    
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def run_pre_market_analysis():
    """执行盘前分析"""
    print("=" * 60)
    print("  金小融 - 盘前分析模块")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n[1/4] 收集市场信息...")
    news = get_market_news()
    
    print("\n[2/4] 分析市场情绪...")
    up_limit, down_limit = analyze_market_sentiment()
    
    print("\n[3/4] 获取热门板块...")
    sectors = get_hot_sectors()
    
    print("\n[4/4] 生成盘前报告...")
    report = generate_pre_market_report()
    today = datetime.now().strftime('%Y%m%d')
    filepath = save_report(report, f"pre_market_{today}.md")
    
    print(f"\n[OK] 盘前分析报告已生成: {filepath}")
    return report, filepath

def run_post_auction_review():
    """执行竞价后点评"""
    print("=" * 60)
    print("  金小融 - 竞价后点评")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    report = generate_post_auction_review()
    today = datetime.now().strftime('%Y%m%d')
    filepath = save_report(report, f"post_auction_{today}.md")
    
    print(f"\n[OK] 竞价点评已生成: {filepath}")
    return report, filepath

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='盘前分析模块')
    parser.add_argument('mode', choices=['pre', 'post'], help='pre: 盘前分析, post: 竞价后点评')
    args = parser.parse_args()
    
    if args.mode == 'pre':
        run_pre_market_analysis()
    else:
        run_post_auction_review()
