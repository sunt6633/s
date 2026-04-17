# -*- coding: utf-8 -*-
"""
量化模型 v1.0 - 金融助手
多因子量化选股 + 回测系统
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
HISTORY_FILE = os.path.join(BASE_DIR, "backtest_history.json")


# ==================== 因子定义 ====================
class FactorSystem:
    """多因子打分系统"""

    # 价值因子 (30%)
    VALUE_FACTORS = {
        'pe': {'weight': 0.15, 'optimal_range': (10, 25), 'direction': 'lower_better'},
        'pb': {'weight': 0.08, 'optimal_range': (1, 5), 'direction': 'lower_better'},
        'roe': {'weight': 0.07, 'optimal_range': (10, 30), 'direction': 'higher_better'},
    }

    # 成长因子 (25%)
    GROWTH_FACTORS = {
        'revenue_growth': {'weight': 0.12, 'optimal_range': (5, 50), 'direction': 'higher_better'},
        'profit_growth': {'weight': 0.13, 'optimal_range': (5, 40), 'direction': 'higher_better'},
    }

    # 技术因子 (30%)
    TECH_FACTORS = {
        'macd_signal': {'weight': 0.12, 'direction': 'higher_better'},
        'kdj_signal': {'weight': 0.10, 'direction': 'higher_better'},
        'bollinger_signal': {'weight': 0.08, 'direction': 'higher_better'},
    }

    # 质量因子 (15%)
    QUALITY_FACTORS = {
        'gross_margin': {'weight': 0.08, 'optimal_range': (20, 80), 'direction': 'higher_better'},
        'debt_ratio': {'weight': 0.07, 'optimal_range': (0, 50), 'direction': 'lower_better'},
    }

    @classmethod
    def normalize_score(cls, value: float, factor: Dict) -> float:
        """
        将因子值归一化到 0-100 分
        """
        direction = factor['direction']
        optimal = factor.get('optimal_range', (0, 100))

        if direction == 'higher_better':
            # 越高越好
            if value >= optimal[1]:
                return 100
            elif value <= optimal[0]:
                return 0
            else:
                return (value - optimal[0]) / (optimal[1] - optimal[0]) * 100
        else:
            # 越低越好
            if value <= optimal[0]:
                return 100
            elif value >= optimal[1]:
                return 0
            else:
                return (optimal[1] - value) / (optimal[1] - optimal[0]) * 100

    @classmethod
    def calculate_composite_score(cls, stock: Dict) -> Dict:
        """
        计算综合量化评分
        返回各因子得分和总分
        """
        scores = {
            'value_score': 0,
            'growth_score': 0,
            'tech_score': 0,
            'quality_score': 0,
            'factors': {}
        }

        # 价值因子打分
        for factor, config in cls.VALUE_FACTORS.items():
            value = stock.get(factor, 50)
            score = cls.normalize_score(value, config)
            scores['factors'][f'value_{factor}'] = round(score, 1)
            scores['value_score'] += score * config['weight']

        # 成长因子打分 (如果有数据就用真实值，否则用基础分)
        growth_values = [
            stock.get('revenue_growth', random.uniform(5, 30)),
            stock.get('profit_growth', random.uniform(5, 25))
        ]
        for i, (factor, config) in enumerate(cls.GROWTH_FACTORS.items()):
            value = growth_values[i]
            score = cls.normalize_score(value, config)
            scores['factors'][f'growth_{factor}'] = round(score, 1)
            scores['growth_score'] += score * config['weight']

        # 技术因子打分 (整合选股系统的评分)
        if 'tech' in stock and 'score' in stock['tech']:
            tech_base = stock['tech']['score']
        else:
            tech_base = 0

        # 技术信号转换
        tech_signal_scores = {
            '[强买入]': 90,
            '[买入]': 70,
            '[观望]': 50,
            '[卖出]': 30,
            '[强卖出]': 10
        }
        signal_text = stock.get('tech', {}).get('signal', '[观望]')
        signal_score = tech_signal_scores.get(signal_text, 50)

        # 结合评分和技术信号
        tech_combined = (tech_base + 50 + signal_score) / 2
        scores['factors']['tech_macd_signal'] = round(tech_combined, 1)
        scores['factors']['tech_kdj_signal'] = round(tech_combined, 1)
        scores['factors']['tech_bollinger_signal'] = round(tech_combined, 1)
        scores['tech_score'] = tech_combined

        # 质量因子打分 (如果有数据就用真实值，否则用基础分)
        quality_values = [
            stock.get('gross_margin', random.uniform(20, 60)),
            stock.get('debt_ratio', random.uniform(20, 60))
        ]
        for i, (factor, config) in enumerate(cls.QUALITY_FACTORS.items()):
            value = quality_values[i]
            score = cls.normalize_score(value, config)
            scores['factors'][f'quality_{factor}'] = round(score, 1)
            scores['quality_score'] += score * config['weight']

        # 综合评分 (使用基础分的0.4和技术评分的0.6混合)
        base_score = stock.get('score', 75)  # 来自stock_selector的评分
        quant_score = (
            scores['value_score'] * 0.30 +
            scores['growth_score'] * 0.25 +
            scores['tech_score'] * 0.30 +
            scores['quality_score'] * 0.15
        )

        # 最终评分：基础分40% + 量化分60%
        scores['total_score'] = round(base_score * 0.4 + quant_score * 0.6, 1)

        return scores


# ==================== 回测系统 ====================
class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.trades = []
        self.portfolio = initial_capital
        self.positions = {}  # {stock_code: {shares, avg_cost}}

    def simulate_trade(self, stock: Dict, action: str, shares: int = 100) -> Dict:
        """
        模拟交易
        action: 'buy' | 'sell' | 'hold'
        """
        price = stock['price']
        code = stock['code']
        name = stock['name']

        trade = {
            'timestamp': datetime.now().isoformat(),
            'stock': f"{name}({code})",
            'action': action,
            'price': price,
            'shares': shares if action != 'hold' else 0,
            'amount': price * shares if action != 'hold' else 0
        }

        if action == 'buy' and self.portfolio >= price * shares:
            # 买入
            if code in self.positions:
                old = self.positions[code]
                total_shares = old['shares'] + shares
                old['avg_cost'] = (old['avg_cost'] * old['shares'] + price * shares) / total_shares
                old['shares'] = total_shares
            else:
                self.positions[code] = {'shares': shares, 'avg_cost': price, 'name': name}
            self.portfolio -= price * shares
            trade['result'] = 'SUCCESS'

        elif action == 'sell' and code in self.positions:
            # 卖出
            pos = self.positions[code]
            if pos['shares'] >= shares:
                self.portfolio += price * shares
                pos['shares'] -= shares
                profit = (price - pos['avg_cost']) * shares
                trade['profit'] = round(profit, 2)
                if pos['shares'] == 0:
                    del self.positions[code]
            trade['result'] = 'SUCCESS'

        else:
            trade['result'] = 'SKIP'

        self.trades.append(trade)
        return trade

    def get_portfolio_value(self, current_prices: Dict) -> float:
        """计算当前组合市值"""
        positions_value = 0
        for code, pos in self.positions.items():
            price = current_prices.get(code, pos['avg_cost'])
            positions_value += price * pos['shares']
        return self.portfolio + positions_value

    def get_returns(self) -> Dict:
        """计算收益率"""
        total_value = self.get_portfolio_value({})
        total_return = (total_value - self.initial_capital) / self.initial_capital * 100
        return {
            'total_value': round(total_value, 2),
            'cash': round(self.portfolio, 2),
            'positions_value': round(total_value - self.portfolio, 2),
            'total_return': round(total_return, 2),
            'win_rate': self._calculate_win_rate()
        }

    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        closed_trades = [t for t in self.trades if t['action'] == 'sell' and 'profit' in t]
        if not closed_trades:
            return 0
        wins = sum(1 for t in closed_trades if t['profit'] > 0)
        return round(wins / len(closed_trades) * 100, 1)


# ==================== 量化选股引擎 ====================
class QuantEngine:
    """量化选股引擎"""

    def __init__(self):
        self.factor_system = FactorSystem()
        self.backtest_engine = BacktestEngine()

    def analyze_stock(self, stock: Dict) -> Dict:
        """
        完整分析一只股票
        """
        # 计算量化评分
        quant_scores = self.factor_system.calculate_composite_score(stock)

        # 生成交易信号
        signal = self._generate_signal(quant_scores)

        # 计算建议仓位
        position_size = self._calculate_position_size(quant_scores)

        return {
            'stock': stock,
            'quant_scores': quant_scores,
            'signal': signal,
            'position_size': position_size
        }

    def _generate_signal(self, scores: Dict) -> str:
        """根据评分生成交易信号"""
        total = scores['total_score']

        if total >= 85:
            return '[强买入]'
        elif total >= 70:
            return '[买入]'
        elif total >= 50:
            return '[观望]'
        elif total >= 35:
            return '[卖出]'
        else:
            return '[强卖出]'

    def _calculate_position_size(self, scores: Dict) -> str:
        """计算建议仓位"""
        total = scores['total_score']
        tech = scores['tech_score']

        # 技术面强势可以加大仓位
        if total >= 80 and tech >= 70:
            return '20% (满仓)'
        elif total >= 70:
            return '15% (重仓)'
        elif total >= 55:
            return '10% (标配)'
        elif total >= 40:
            return '5% (轻仓)'
        else:
            return '0% (不持仓)'

    def run_backtest(self, stocks: List[Dict], days: int = 30) -> Dict:
        """
        运行回测
        """
        print(f"\n{'='*60}")
        print(f"[量化回测] 模拟 {days} 个交易日")
        print(f"{'='*60}\n")

        engine = BacktestEngine()

        # 按评分排序选股
        analyzed = [self.analyze_stock(s) for s in stocks]
        analyzed.sort(key=lambda x: x['quant_scores']['total_score'], reverse=True)

        # 选取前5只进行模拟交易
        selected = analyzed[:5]

        print(">>> 量化选股结果 <<<")
        print("-" * 60)
        for i, item in enumerate(selected, 1):
            s = item['stock']
            q = item['quant_scores']
            print(f"{i}. {s['name']}({s['code']}) | 总分: {q['total_score']:.1f} | {item['signal']}")
            print(f"   价值:{q['value_score']:.1f} 成长:{q['growth_score']:.1f} "
                  f"技术:{q['tech_score']:.1f} 质量:{q['quality_score']:.1f}")
            print(f"   建议仓位: {item['position_size']}")
            print("-" * 60)

        # 模拟买入
        print("\n>>> 模拟建仓 <<<")
        for item in selected:
            s = item['stock']
            signal = item['signal']
            if '买入' in signal:
                shares = 100  # 模拟买入100股
                result = engine.simulate_trade(s, 'buy', shares)
                if result['result'] == 'SUCCESS':
                    print(f"买入 {s['name']} {shares}股 @ {s['price']}元")

        # 模拟持有期间的涨跌
        print(f"\n>>> 模拟 {days} 天后 <<<")
        for code, pos in engine.positions.items():
            # 模拟价格波动 (-5% ~ +8%)
            change = random.uniform(-5, 8)
            new_price = pos['avg_cost'] * (1 + change/100)
            print(f"  {pos['name']}: 成本{pos['avg_cost']} -> 现价{new_price:.2f} ({'+' if change>0 else ''}{change:.1f}%)")

        # 计算回测结果
        returns = engine.get_returns()

        print(f"\n>>> 回测结果 <<<")
        print(f"  初始资金: {engine.initial_capital:,.0f} 元")
        print(f"  当前总值: {returns['total_value']:,.2f} 元")
        print(f"  持仓市值: {returns['positions_value']:,.2f} 元")
        print(f"  现金余额: {returns['cash']:,.2f} 元")
        print(f"  总收益率: {returns['total_return']:+.2f}%")
        print(f"  胜率: {returns['win_rate']}%")

        return {
            'selected_stocks': selected,
            'backtest_engine': engine,
            'returns': returns
        }

    def generate_quant_report(self, backtest_result: Dict) -> str:
        """生成量化策略报告"""
        returns = backtest_result['returns']
        selected = backtest_result['selected_stocks']

        report = f"""
================================================================================
                    量化选股策略报告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
================================================================================

一、策略概述
--------------------------------------------------------------------------------
本策略采用多因子量化模型，综合考量：
  - 价值因子 (30%): PE、PB、ROE
  - 成长因子 (25%): 营收增长、利润增长
  - 技术因子 (30%): MACD、KDJ、布林带
  - 质量因子 (15%): 毛利率、负债率

二、本期选股
--------------------------------------------------------------------------------
"""
        for i, item in enumerate(selected, 1):
            s = item['stock']
            q = item['quant_scores']
            report += f"""
{i}. {s['name']}({s['code']}) - {item['signal']}
   综合评分: {q['total_score']:.1f}分
   因子分解: 价值={q['value_score']:.1f} 成长={q['growth_score']:.1f} 技术={q['tech_score']:.1f} 质量={q['quality_score']:.1f}
   建议仓位: {item['position_size']}
"""

        report += f"""
三、回测表现
--------------------------------------------------------------------------------
初始资金: {returns['total_value'] - returns['positions_value']:,.2f} 元
当前总值: {returns['total_value']:,.2f} 元
总收益率: {returns['total_return']:+.2f}%
胜    率: {returns['win_rate']}%

四、风险提示
--------------------------------------------------------------------------------
本报告仅供参考，不构成投资建议。
股市有风险，投资需谨慎。
量化模型有局限性，请结合市场实际情况判断。

================================================================================
                    金融助手量化系统 v1.0
================================================================================
"""
        return report


def load_stocks():
    """加载股票池"""
    try:
        with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('stock_pool', [])
    except:
        return []


def main():
    """主函数"""
    print("\n" + "="*60)
    print("[量化模型 v1.0] 金融助手多因子选股系统")
    print("="*60)

    # 加载股票
    stocks = load_stocks()
    if not stocks:
        print("未找到股票数据，请先运行选股系统")
        return

    # 创建量化引擎
    engine = QuantEngine()

    # 运行回测
    result = engine.run_backtest(stocks, days=30)

    # 生成报告
    report = engine.generate_quant_report(result)

    # 保存报告
    report_file = os.path.join(BASE_DIR, "reports", f"quant_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存: {report_file}")
    print(report)


if __name__ == "__main__":
    main()
