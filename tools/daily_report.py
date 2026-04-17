# -*- coding: utf-8 -*-
"""
每日报告生成器 - 金融助手
生成交易报告并发送给孙先生
"""

import json
import os
from datetime import datetime

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", f"report_{datetime.now().strftime('%Y%m%d')}.md")

def load_portfolio():
    """加载投资组合"""
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_portfolio(data):
    """保存投资组合"""
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_report(portfolio, trades=None):
    """生成每日报告"""

    pf = portfolio['portfolio']
    positions = portfolio.get('positions', [])
    stock_pool = portfolio.get('stock_pool', [])
    trade_history = portfolio.get('trade_history', [])

    # 获取今日交易
    today = datetime.now().strftime("%Y-%m-%d")
    today_trades = [t for t in trade_history if t.get('date') == today] if trade_history else []

    report = f"""# 金融助手 - 每日股票模拟报告
## {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

---

## 一、账户概况

| 项目 | 数值 |
|------|------|
| 初始资金 | {pf['initial_capital']:.2f} 元 |
| 当前总资产 | {pf.get('total_value', pf['current_capital']):.2f} 元 |
| 持仓市值 | {pf.get('total_value', pf['current_capital']) - pf['current_capital']:.2f} 元 |
| 可用现金 | {pf['current_capital']:.2f} 元 |
| 总收益 | {pf['total_profit']:.2f} 元 |
| 收益率 | {pf['total_profit_rate']:+.2f}% |

---

## 二、今日交易

"""

    if today_trades:
        report += f"共执行 **{len(today_trades)}** 笔交易：\n\n"
        for t in today_trades:
            action_emoji = "买" if t['action'] == 'buy' else "卖"
            profit_str = f"，盈利{t['profit']:.2f}元" if t.get('profit') else ""
            report += f"- **{action_emoji}入** {t['name']}({t['code']}) @ {t['price']}元 × {t['shares']}股\n"
            report += f"  {t['reason']}{profit_str}\n\n"
    else:
        report += "今日无交易操作（观望中）\n\n"

    report += """---

## 三、持仓明细

"""

    if positions:
        report += "| 股票名称 | 代码 | 持仓数量 | 成本价 | 现价 | 盈亏金额 | 盈亏率 |\n"
        report += "|---------|------|---------|-------|------|---------|-------|\n"

        for pos in sorted(positions, key=lambda x: x.get('profit_rate', 0), reverse=True):
            profit_emoji = "+" if pos.get('profit_rate', 0) > 0 else ""
            report += f"| {pos['name']} | {pos['code']} | {pos['shares']}股 | {pos['avg_cost']:.2f} | {pos['current_price']:.2f} | {profit_emoji}{pos.get('profit', 0):.2f}元 | {profit_emoji}{pos.get('profit_rate', 0):.2f}% |\n"
    else:
        report += "暂无持仓（空仓观望）\n"

    report += """

---

## 四、自选股票池

"""

    if stock_pool:
        report += "今日重点关注以下10只股票：\n\n"
        for i, stock in enumerate(stock_pool[:10], 1):
            change_emoji = "+" if stock.get('change_rate', 0) > 0 else ""
            report += f"{i}. **{stock['name']}**({stock['code']}) - {stock['sector']}\n"
            report += f"   现价: {stock['price']:.2f}元 | {change_emoji}{stock.get('change_rate', 0):.2f}%\n"
    else:
        report += "暂无自选股票\n"

    report += f"""

---

## 五、操作建议

"""

    if positions:
        report += "**持仓建议：**\n"
        for pos in positions:
            profit_rate = pos.get('profit_rate', 0)
            if profit_rate >= 15:
                report += f"- {pos['name']}: 盈利已达{profit_rate:.1f}%，建议考虑止盈\n"
            elif profit_rate <= -8:
                report += f"- {pos['name']}: 亏损已达{profit_rate:.1f}%，建议关注止损\n"
            else:
                report += f"- {pos['name']}: 继续持有观察\n"
    else:
        report += "目前空仓，建议关注自选股票池，等待买入时机。\n"

    report += f"""

---

## 六、风险提示

⚠️ 本报告仅为模拟交易记录，不构成任何投资建议！
⚠️ 股市有风险，投资需谨慎！

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*金融助手（小钱）为您服务*
"""

    return report

def save_report(report):
    """保存报告"""
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"报告已保存: {REPORT_FILE}")
    return REPORT_FILE

def generate_and_save():
    """生成并保存报告"""
    portfolio = load_portfolio()
    report = generate_report(portfolio)
    report_path = save_report(report)
    return report, report_path

if __name__ == "__main__":
    report, path = generate_and_save()
    print("\n" + "=" * 50)
    print(report)
