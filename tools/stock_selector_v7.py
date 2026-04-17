"""
金小融选股模型 v7.0
多因子打分系统：技术面40分 + 资金面30分 + 基本面30分 = 100分
更新时间：2026-04-17
"""

import json
from datetime import datetime

# 评分阈值
CORE_POOL_THRESHOLD = 80  # 核心股票池：≥80分
WATCH_POOL_THRESHOLD = 60  # 观察股票池：60-80分

class StockSelector:
    """选股器 v7.0"""
    
    def __init__(self):
        self.version = "v7.0"
        
    def calculate_technical_score(self, tech_data):
        """计算技术面得分（满分40分）"""
        score = 0
        signals = []
        
        ma = tech_data.get('ma', {})
        
        # 1. 趋势因子（10分）
        trend_score = 0
        if ma.get('ma5_above_ma10') and ma.get('ma10_above_ma20'):
            trend_score += 5
            signals.append("均线多头排列")
        if ma.get('ma20_above_ma60'):
            trend_score += 3
        if ma.get('price_above_ma20'):
            trend_score += 2
        score += min(trend_score, 10)
        
        # 2. 量价因子（10分）
        volume_score = 0
        volume = tech_data.get('volume', {})
        vol_ratio = volume.get('ratio', 1)
        vol_status = volume.get('status', '')
        
        if '放量' in vol_status or vol_ratio > 1.5:
            volume_score += 5
            signals.append("量能放大")
        elif '温和' in vol_status:
            volume_score += 3
        
        change_rate = tech_data.get('trend', 0)
        if 3 <= abs(change_rate) <= 5:
            volume_score += 5
        elif 1 <= abs(change_rate) <= 3:
            volume_score += 3
        
        score += min(volume_score, 10)
        
        # 3. 指标因子（10分）
        indicator_score = 0
        
        macd = tech_data.get('macd', {})
        if macd.get('histogram', 0) > 0 and macd.get('dif', 0) > macd.get('dea', 0):
            indicator_score += 4
            signals.append("MACD金叉")
        
        rsi = tech_data.get('rsi', 50)
        if 30 < rsi < 70:
            if 30 < rsi < 50:
                indicator_score += 3
            elif 50 <= rsi < 70:
                indicator_score += 2
        
        kdj = tech_data.get('kdj', {})
        k = kdj.get('k', 50)
        d = kdj.get('d', 50)
        if k > d and k < 70:
            indicator_score += 3
            signals.append("KDJ金叉")
        
        score += min(indicator_score, 10)
        
        # 4. 异动因子（10分）
        abnormal_score = 0
        
        if vol_ratio > 1.5:
            abnormal_score += 3
        
        turnover = tech_data.get('turnover', 0)
        if 3 <= turnover <= 10:
            abnormal_score += 4
        elif turnover > 0:
            abnormal_score += 2
        
        if 3 <= abs(change_rate) <= 5:
            abnormal_score += 3
        
        score += min(abnormal_score, 10)
        
        return {
            'total': min(score, 40),
            'trend': min(trend_score, 10),
            'volume_price': min(volume_score, 10),
            'indicators': min(indicator_score, 10),
            'abnormal': min(abnormal_score, 10),
            'signals': signals
        }
    
    def calculate_money_score(self, money_data):
        """计算资金面得分（满分30分）"""
        score = 0
        signals = []
        
        main_money = money_data.get('main_flow', 0)
        if main_money > 10000000:
            score += 10
            signals.append("主力净流入")
        elif main_money > 5000000:
            score += 5
        
        north_days = money_data.get('north_continuous_days', 0)
        if north_days >= 3:
            score += 10
            signals.append(f"北向连续{north_days}日净流入")
        elif north_days >= 1:
            score += 5
        
        if money_data.get('dragon_tiger_institution_buy', False):
            score += 10
            signals.append("龙虎榜机构买入")
        
        return {
            'total': min(score, 30),
            'signals': signals
        }
    
    def calculate_fundamental_score(self, fundamental_data):
        """计算基本面得分（满分30分）"""
        score = 0
        signals = []
        
        # 估值
        pe = fundamental_data.get('pe', 0)
        pb = fundamental_data.get('pb', 0)
        roe = fundamental_data.get('roe', 0)
        
        valuation_score = 0
        if 0 < pe < 30:
            valuation_score += 4
        if 0 < pb < 5:
            valuation_score += 3
        if roe > 10:
            valuation_score += 3
        elif roe > 5:
            valuation_score += 1
        
        score += min(valuation_score, 10)
        
        # 成长
        revenue_growth = fundamental_data.get('revenue_growth', 0)
        profit_growth = fundamental_data.get('profit_growth', 0)
        
        growth_score = 0
        if revenue_growth > 15:
            growth_score += 5
            signals.append(f"营收增长{revenue_growth}%")
        elif revenue_growth > 0:
            growth_score += 2
        
        if profit_growth > 20:
            growth_score += 5
            signals.append(f"净利润增长{profit_growth}%")
        elif profit_growth > 0:
            growth_score += 2
        
        score += min(growth_score, 10)
        
        # 风控
        risk_score = 10
        risk_items = []
        
        if fundamental_data.get('商誉暴雷', False):
            risk_score -= 5
            risk_items.append("商誉暴雷")
        if fundamental_data.get('减持', False):
            risk_score -= 3
            risk_items.append("减持")
        if fundamental_data.get('解禁', False):
            risk_score -= 2
            risk_items.append("解禁")
        
        score += max(risk_score, 0)
        
        return {
            'total': score,
            'valuation': min(valuation_score, 10),
            'growth': min(growth_score, 10),
            'risk': max(risk_score, 0),
            'signals': signals,
            'risk_warnings': risk_items
        }
    
    def calculate_composite_score(self, stock_data):
        """计算综合得分"""
        tech_score = self.calculate_technical_score(stock_data.get('tech', {}))
        money_score = self.calculate_money_score(stock_data.get('money', {}))
        fundamental_score = self.calculate_fundamental_score(stock_data.get('fundamental', {}))
        
        total_score = tech_score['total'] + money_score['total'] + fundamental_score['total']
        
        if total_score >= CORE_POOL_THRESHOLD:
            pool = 'core'
        elif total_score >= WATCH_POOL_THRESHOLD:
            pool = 'watch'
        else:
            pool = 'exclude'
        
        return {
            'code': stock_data.get('code', ''),
            'name': stock_data.get('name', ''),
            'sector': stock_data.get('sector', ''),
            'price': stock_data.get('price', 0),
            'change_rate': stock_data.get('change_rate', 0),
            'total_score': round(total_score, 1),
            'technical': tech_score,
            'money': money_score,
            'fundamental': fundamental_score,
            'pool': pool,
            'all_signals': tech_score['signals'] + money_score['signals'] + fundamental_score['signals']
        }
    
    def select_stocks(self, stocks_data):
        """从候选股票中选择核心池和观察池"""
        results = []
        
        for stock in stocks_data:
            result = self.calculate_composite_score(stock)
            results.append(result)
        
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        core_pool = [s for s in results if s['pool'] == 'core'][:5]
        watch_pool = [s for s in results if s['pool'] == 'watch'][:10]
        
        return {
            'version': self.version,
            'select_date': datetime.now().strftime('%Y-%m-%d'),
            'select_time': datetime.now().strftime('%H:%M:%S'),
            'core_pool': core_pool,
            'watch_pool': watch_pool,
            'total_candidates': len(results),
            'core_count': len(core_pool),
            'watch_count': len(watch_pool)
        }


if __name__ == "__main__":
    selector = StockSelector()
    
    test_stocks = [
        {
            'code': '600036',
            'name': '招商银行',
            'sector': '银行',
            'price': 39.22,
            'change_rate': -2.79,
            'tech': {
                'ma': {
                    'ma5': 35.39, 'ma10': 38.44, 'ma20': 38.46, 'ma60': 38.17,
                    'ma5_above_ma10': False, 'ma10_above_ma20': False, 'ma20_above_ma60': True,
                    'price_above_ma20': True
                },
                'macd': {'dif': -0.751, 'dea': -0.108, 'histogram': -1.286},
                'kdj': {'k': 45.1, 'd': 48.4, 'j': 38.6},
                'rsi': 44.7,
                'volume': {'ratio': 1.55, 'status': '量能放大'},
                'turnover': 4.96,
                'trend': -8.0
            },
            'fundamental': {
                'pe': 8.5, 'pb': 1.2, 'roe': 16.5,
                'revenue_growth': 8, 'profit_growth': 6
            },
            'money': {}
        }
    ]
    
    result = selector.select_stocks(test_stocks)
    print(f"版本：{result['version']}")
    print(f"核心池：{result['core_count']}只")
    print(f"观察池：{result['watch_count']}只")
    for s in result['core_pool']:
        print(f"  {s['name']}（{s['code']}）- {s['total_score']}分")
    for s in result['watch_pool']:
        print(f"  {s['name']}（{s['code']}）- {s['total_score']}分")
