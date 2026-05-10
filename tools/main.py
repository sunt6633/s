# -*- coding: utf-8 -*-
"""
金融助手 - 股票模拟交易主程序 v6.0
整合选股、交易、报告、学习、实时监控功能
支持多种运行模式

v6.0 重大升级 (2026-04-16 孙先生指示):
【选股系统 v6.0】
- 技术面权重从15%提升到25%
- 新增北向资金因子
- 新增板块轮动因子
- 新增量价背离检测
- 新增MACD背离检测

【风控系统 v9.0】
- 动态止损（根据波动率自适应）
- 个股最大回撤15%强制清仓
- 账户总回撤10%一键清仓
- 亏损连续3天暂停交易
- 大盘暴跌3%自动熔断

【量化引擎 v2.0】
- 接入akshare免费数据源
- 布林带买卖点量化
- MACD底背离检测
- 回测框架
"""

import sys
import os
from datetime import datetime, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# v6.0 选股系统
from stock_selector_v6 import update_stock_pool_v6

# v9.0 风控交易引擎
try:
    from trading_engine_v9 import run_daily_trading_v9 as run_daily_trading, is_trading_time, load_portfolio
except:
    from trading_engine import run_daily_trading, is_trading_time, load_portfolio

from daily_report import generate_and_save
from market_monitor import MarketMonitor

def check_trading_time_required():
    """
    检查是否必须在交易时间内执行
    如果不是交易模式(check)，则必须检查交易时间
    """
    return True  # 强制检查

def run_full_simulation(mode="full"):
    """
    运行模拟交易流程
    
    Args:
        mode: 运行模式
            - "full": 完整模式（选股+交易+报告）
            - "morning": 开盘模式（选股+建仓，不生成报告）
            - "afternoon": 盘后复检模式（检查持仓，生成报告）
            - "monitor": 盘中持续监控模式（不退出）
            - "check": 单次检查（交易时间内盘中检查，非交易时间盘前/盘后状态检查）
    """
    print("=" * 60)
    print("  金融助手 - 智能股票交易系统")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  运行模式: {mode}")
    print("=" * 60)

    if mode == "full":
        # 完整模式（用于测试或手动运行）
        print("\n[步骤1/3] 筛选自选股票池...")
        stocks = update_stock_pool_v6("综合评分")
        
        print("\n[步骤2/3] 执行模拟交易...")
        portfolio, trades = run_daily_trading()
        
        print("\n[步骤3/3] 生成每日报告...")
        report, report_path = generate_and_save()
        
    elif mode == "morning":
        # 开盘模式：选股 + 建仓
        print("\n[开盘模式] 9:30 开盘选股 + 建仓")
        print("\n[步骤1/2] 筛选自选股票池...")
        stocks = update_stock_pool_v6("综合评分")
        
        print("\n[步骤2/2] 执行买入交易...")
        portfolio, trades = run_daily_trading()
        
        print(f"\n开盘交易完成！执行 {len(trades)} 笔买入")
        
    elif mode == "afternoon":
        # 收盘复检模式：检查持仓 + 止损止盈 + 生成报告
        print("\n[收盘复检模式] 14:30 持仓检查 + 止损止盈")
        
        print("\n[步骤1/2] 执行持仓复检（止损/止盈）...")
        portfolio, trades = run_daily_trading()
        
        print("\n[步骤2/2] 生成每日报告...")
        report, report_path = generate_and_save()
        
        print(f"\n收盘复检完成！执行 {len(trades)} 笔交易")
    
    elif mode == "monitor":
        # 盘中持续监控模式
        print("\n[盘中监控模式] 启动智能监控系统...")
        print("  - 交易时段持续监控（9:30-11:30, 13:00-15:00）")
        print("  - 自动判断买卖时机并执行")
        print("  - 可随时 Ctrl+C 停止")
        print()
        
        monitor = MarketMonitor()
        try:
            monitor.run_continuous()
        except KeyboardInterrupt:
            print("\n收到停止信号，正在退出...")
            monitor.stop()
    
    elif mode == "check":
        # 单次检查模式（用于定时任务）
        can_trade, time_reason = is_trading_time()
        
        # 根据时间显示不同状态
        now = datetime.now()
        is_auction = (now.hour == 9 and now.minute >= 15 and now.minute < 25)
        is_pre_market = (now.hour == 9 and now.minute < 15)
        is_market = can_trade
        is_after_hours = (now.hour >= 15)
        
        if is_auction:
            mode_desc = "集合竞价阶段"
        elif is_pre_market:
            mode_desc = "盘前准备阶段"
        elif is_market:
            mode_desc = "盘中检查"
        elif is_after_hours:
            mode_desc = "盘后总结"
        else:
            mode_desc = "状态检查"
        
        print(f"\n[{mode_desc}] 执行检查...")
        
        # 执行交易检查
        portfolio, trades = run_daily_trading()
        
        # 开盘后可以检查持仓状态，但交易必须严格遵守时间
        if not can_trade:
            print(f"\n[警告] 当前非交易时间：{time_reason}")
            print("   - 可以查看持仓状态，但不能执行买卖操作")
            print("   - 系统将在开盘后自动执行交易\n")
        
        if trades:
            print(f"\n[交易完成] 执行了 {len(trades)} 笔交易:")
            for trade in trades:
                print(f"  - {trade['action'].upper()}: {trade['name']} @ {trade['price']}元")
            # 生成简要报告
            portfolio = load_portfolio()
            p = portfolio['portfolio']
            print(f"\n[当前状态]")
            print(f"   总资产: {p['total_value']:.2f}元")
            print(f"   持仓: {len(portfolio['positions'])}只")
            print(f"   现金: {p['current_capital']:.2f}元")
        else:
            print("\n本次检查无交易，系统状态良好")
    
    else:
        print(f"\n[错误] 未知模式: {mode}")
        print("可用模式: full, morning, afternoon, monitor, check")
        return

    print("\n" + "=" * 60)
    print("  任务完成!")
    print("=" * 60)

def show_help():
    """显示帮助信息"""
    print("""
金融助手 - 智能股票交易系统
========================

用法: python main.py [模式]

模式选项:
  full     - 完整模式（选股+交易+报告），用于测试
  morning  - 盘前模式，选股+建仓（9:30前）
  afternoon- 盘后模式，持仓复检+报告（15:00后）
  monitor  - 盘中持续监控（不退出），交易时段自动运行
  check    - 单次检查（根据时间自动判断：盘前/盘中/盘后）

示例:
  python main.py full        # 完整运行
  python main.py morning     # 开盘建仓
  python main.py afternoon   # 收盘复检
  python main.py monitor     # 盘中持续监控
  python main.py check       # 单次检查

定时任务建议:
  - 盘中监控: 设置一个每小时运行 check 模式的任务
  - 或直接运行 monitor 模式（需要保持进程）
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_help()
        else:
            run_full_simulation(sys.argv[1])
    else:
        # 默认完整模式
        run_full_simulation("full")
