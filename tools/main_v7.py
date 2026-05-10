"""
金小融量化交易系统 v7.0 主程序
更新时间：2026-04-17
功能：盘前选股 → 盘中监控 → 盘后复盘 → 每周进化
"""

import json
import os
import sys
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from trades import TradeRecorder
from data_source import DataSource
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
STOCK_POOL_FILE = os.path.join(BASE_DIR, "stock_pool.json")

class QuantTrader:
    """金小融量化交易系统 v7.0"""
    
    def __init__(self):
        self.version = "v7.0"
        self.today = date.today().strftime('%Y-%m-%d')
        
    def pre_market(self):
        """盘前任务：选股、更新股票池"""
        print("=" * 60)
        print(f"金小融量化交易系统 {self.version}")
        print(f"盘前分析 - {self.today}")
        print("=" * 60)
        
        # 读取候选股票
        try:
            with open(STOCK_POOL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                candidates = data.get('stocks', [])
        except Exception as e:
            print(f"读取股票池失败: {e}")
            return
        
        # 按得分排序输出TOP10
        sorted_stocks = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)
        
        print("\n核心股票池（≥80分，优先交易）")
        print("-" * 50)
        core = [s for s in sorted_stocks if s.get('score', 0) >= 80]
        if core:
            for i, s in enumerate(core[:5], 1):
                print(f"{i}. {s['name']}（{s['code']}）")
                print(f"   板块：{s['sector']} | 现价：{s['price']} | 涨跌：{s['change_rate']:+.2f}%")
                print(f"   综合得分：{s['score']}分")
                print()
        else:
            print("暂无核心股票池标的")
        
        print("\n观察股票池（60-80分，持续跟踪）")
        print("-" * 50)
        watch = [s for s in sorted_stocks if 60 <= s.get('score', 0) < 80]
        if watch:
            for i, s in enumerate(watch[:10], 1):
                print(f"{i}. {s['name']}（{s['code']}）- {s['score']}分 - {s['sector']}")
        else:
            print("暂无观察股票池标的")
        
        print("\n" + "=" * 60)
        return {'core': core[:5], 'watch': watch[:10]}
    
    def _get_sina_prices(self, codes_dict):
        """从新浪财经获取实时行情"""
        try:
            import requests
            sina_codes = []
            for code in codes_dict.keys():
                if code.startswith('0') or code.startswith('3'):
                    sina_codes.append(f'sz{code}')
                else:
                    sina_codes.append(f'sh{code}')
            
            url = f'https://hq.sinajs.cn/list={",".join(sina_codes)}'
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.sina.com.cn'
            }
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'gbk'
            
            results = {}
            lines = r.text.strip().split('\n')
            code_list = list(codes_dict.keys())
            
            for i, line in enumerate(lines):
                if i < len(code_list) and '=' in line:
                    code = code_list[i]
                    data_str = line.split('=')[1].strip('";\n\r ')
                    parts = data_str.split(',')
                    if len(parts) >= 32:
                        results[code] = float(parts[3])  # 当前价
            
            return results
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def intraday_monitor(self):
        """盘中监控 - tushare Pro数据源"""
        print("=" * 60)
        print(f"盘中监控 - {datetime.now().strftime('%H:%M:%S')}")
        print("数据源: tushare Pro")
        print("=" * 60)
        
        # 使用交易记录器
        recorder = TradeRecorder()
        
        # 使用DataSource获取数据
        ds = DataSource()
        
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                portfolio = json.load(f)
                positions = portfolio.get('positions', [])
        except Exception as e:
            print(f"读取持仓失败: {e}")
            return
        
        if not positions:
            print("当前无持仓")
            return
        
        # 获取实时行情
        codes = [p['code'] for p in positions]
        realtime = ds.get_realtime(codes)
        
        # 获取日线数据计算技术指标
        today_str = date.today().strftime('%Y%m%d')
        start_str = (date.today().replace(day=1)).strftime('%Y%m%d')
        
        # 更新持仓价格
        for pos in positions:
            code = pos['code']
            if realtime and code in realtime:
                info = realtime[code]
                pos['current_price'] = info['price']
                pos['change'] = info['price'] - info['prev_close']
                pos['pct_chg'] = pos['change'] / info['prev_close'] * 100
                pos['current_price_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取日线计算技术指标
        for pos in positions:
            code = pos['code']
            daily_data = ds.get_daily(code, start_str, today_str)
            if daily_data:
                pos['ma5'] = ds.calculate_ma(daily_data, 5)
                pos['ma10'] = ds.calculate_ma(daily_data, 10)
                pos['volatility'] = ds.calculate_volatility(daily_data, 10)
        
        # 保存更新后的数据
        with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        
        # 使用交易记录计算总资产（包含卖出收入）
        total_value, total_profit, profit_rate = recorder.print_summary(positions)
        
        print(f"\n持仓监控")
        print("-" * 50)
        
        for pos in positions:
            cost = pos.get('avg_cost', 0)
            price = pos.get('current_price', 0)
            shares = pos.get('shares', 0)
            pct_chg = pos.get('pct_chg', 0)
            profit_rate_pos = ((price - cost) / cost * 100) if cost > 0 else 0
            market_value = price * shares
            profit = (price - cost) * shares
            ma5 = pos.get('ma5', 0)
            ma10 = pos.get('ma10', 0)
            
            if profit_rate_pos >= 15:
                signal = "[止盈信号]"
            elif profit_rate_pos <= -8:
                signal = "[止损信号]"
            else:
                signal = "[正常持有]"
            
            status = "盈利" if profit >= 0 else "亏损"
            
            print(f"\n{pos['name']}（{pos['code']}）")
            print(f"   成本：{cost:.2f} | 现价：{price:.2f} | 涨跌：{pct_chg:+.2f}%")
            print(f"   持仓：{shares}股 | 市值：{market_value:,.2f}元")
            print(f"   盈亏：{profit:+,.2f}元（{profit_rate_pos:+.2f}%）")
            if ma5:
                print(f"   MA5：{ma5:.2f} | MA10：{ma10:.2f}")
            print(f"   状态：{signal} {status}")
        
        print("\n" + "=" * 60)
    
    def post_market(self):
        """盘后复盘"""
        print("=" * 60)
        print(f"盘后复盘 - {self.today}")
        print("=" * 60)
        
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                portfolio = json.load(f)
        except Exception as e:
            print(f"读取数据失败: {e}")
            return
        
        positions = portfolio.get('positions', [])
        trade_history = portfolio.get('trade_history', [])
        portfolio_info = portfolio.get('portfolio', {})
        
        today_trades = [t for t in trade_history if t.get('date') == self.today]
        
        print(f"\n今日交易记录")
        print("-" * 50)
        if today_trades:
            for t in today_trades:
                action = "买入" if t['action'] in ['buy', 'partial_buy'] else "卖出"
                print(f"{t['name']}（{t['code']}）{action}")
                print(f"  价格：{t['price']} | 数量：{t['shares']}股")
                if t.get('profit'):
                    print(f"  盈亏：{t['profit']:+,.2f}元")
        else:
            print("今日无交易")
        
        print(f"\n持仓绩效")
        print("-" * 50)
        total_profit = portfolio_info.get('total_profit', 0)
        profit_rate = portfolio_info.get('total_profit_rate', 0)
        print(f"总盈亏：{total_profit:+,.2f}元（{profit_rate:+.2f}%）")
        
        sells = [t for t in trade_history if t.get('action') in ['sell', 'partial_sell']]
        if sells:
            wins = [t for t in sells if t.get('profit', 0) > 0]
            win_rate = len(wins) / len(sells) * 100
            print(f"交易次数：{len(sells)} | 盈利次数：{len(wins)} | 胜率：{win_rate:.1f}%")
        
        print("\n" + "=" * 60)
        print("⚠️ 以上仅为模拟交易分析，不构成投资建议")
        print("=" * 60)


def main():
    trader = QuantTrader()
    now = datetime.now()
    hour = now.hour
    
    if hour < 9:
        trader.pre_market()
    elif 9 <= hour < 15:
        trader.intraday_monitor()
    else:
        trader.post_market()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        trader = QuantTrader()
        
        if command == "pre":
            trader.pre_market()
        elif command == "intra":
            trader.intraday_monitor()
        elif command == "post":
            trader.post_market()
        elif command == "all":
            trader.pre_market()
    else:
        main()
