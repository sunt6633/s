# -*- coding: utf-8 -*-
"""
智能学习引擎 - 金融助手
从交易历史中学习，不断优化选股和交易策略
"""

import json
import os
from datetime import datetime
from collections import defaultdict

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")
LEARNING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_data.json")

class LearningEngine:
    def __init__(self):
        self.load_data()
        
    def load_data(self):
        """加载学习数据"""
        if os.path.exists(LEARNING_FILE):
            with open(LEARNING_FILE, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "trade_history": [],        # 所有交易记录
                "stock_performance": {},    # 个股表现
                "strategy_results": {},      # 策略效果
                "learned_rules": [],         # 学到的规则
                "parameters": {
                    "buy_score_threshold": 75,      # 买入评分阈值（会动态调整）
                    "sell_score_threshold": 70,     # 卖出评分阈值
                    "max_loss_tolerance": 0.08,     # 最大亏损容忍
                    "min_profit_take": 0.15,        # 最小盈利目标
                },
                "insights": []               # 洞察记录
            }
    
    def save_data(self):
        """保存学习数据"""
        with open(LEARNING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def record_trade(self, trade_info):
        """
        记录一笔交易供学习
        trade_info: {
            'code', 'name', 'action', 'price', 'reason',
            'market_condition': {},  # 当时大盘情况
            'stock_data': {},         # 当时个股数据
            'decision_factors': []    # 决策因素列表
        }
        """
        trade_record = {
            **trade_info,
            'recorded_at': datetime.now().isoformat()
        }
        self.data['trade_history'].append(trade_record)
        
        # 追踪个股表现
        if trade_info['action'] == 'buy':
            code = trade_info['code']
            if code not in self.data['stock_performance']:
                self.data['stock_performance'][code] = {
                    'name': trade_info['name'],
                    'buy_records': [],
                    'sell_records': [],
                    'total_profit': 0,
                    'trade_count': 0
                }
            self.data['stock_performance'][code]['buy_records'].append({
                'price': trade_info['price'],
                'date': trade_info.get('date', datetime.now().strftime('%Y-%m-%d')),
                'score': trade_info.get('stock_data', {}).get('score', 0)
            })
        
        self.save_data()
    
    def record_sell_result(self, code, buy_price, sell_price, reason):
        """记录卖出结果，分析成功/失败"""
        if code not in self.data['stock_performance']:
            return
            
        perf = self.data['stock_performance'][code]
        profit_rate = (sell_price - buy_price) / buy_price
        
        sell_record = {
            'price': sell_price,
            'profit_rate': profit_rate,
            'reason': reason,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        perf['sell_records'].append(sell_record)
        perf['total_profit'] += profit_rate * 100
        perf['trade_count'] += 1
        
        # 分析这笔交易
        self._analyze_trade(code, buy_price, sell_price, reason)
        self.save_data()
    
    def _analyze_trade(self, code, buy_price, sell_price, reason):
        """分析单笔交易，提取经验"""
        profit_rate = (sell_price - buy_price) / buy_price
        insight = {
            'code': code,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_rate': round(profit_rate * 100, 2),
            'reason': reason,
            'analyzed_at': datetime.now().isoformat(),
            'lessons': []
        }
        
        # 分析止损交易
        if profit_rate < -0.05:
            insight['lessons'].append({
                'type': 'loss_analysis',
                'lesson': f'亏损{abs(profit_rate)*100:.1f}%，原因：{reason}'
            })
            # 检查是否是追高
            for record in self.data['stock_performance'][code]['buy_records'][-1:]:
                if record.get('price') > buy_price * 0.98:
                    insight['lessons'].append({
                        'type': 'pattern',
                        'lesson': '可能是追高买入，需注意买入时机'
                    })
        
        # 分析盈利交易
        elif profit_rate > 0.10:
            insight['lessons'].append({
                'type': 'success_pattern',
                'lesson': f'盈利{profit_rate*100:.1f}%，成功因素：{reason}'
            })
            # 检查是否是低吸
            if profit_rate > 0.15:
                insight['lessons'].append({
                    'type': 'pattern',
                    'lesson': '大幅盈利，可能是低位买入或持有时间足够'
                })
        
        # 生成新洞察
        if insight['lessons']:
            self.data['insights'].append(insight)
            
            # 如果有重要教训，更新参数
            self._update_parameters(insight)
    
    def _update_parameters(self, insight):
        """根据分析结果调整参数"""
        params = self.data['parameters']
        
        for lesson in insight['lessons']:
            if lesson['type'] == 'loss_analysis':
                # 亏损交易：调高买入标准
                params['buy_score_threshold'] = min(params['buy_score_threshold'] + 1, 85)
                
            elif lesson['type'] == 'success_pattern':
                # 成功交易：保持或微调
                pass
    
    def get_buy_signals(self, stock_pool, market_data):
        """
        根据学习到的知识，筛选买入信号
        返回: [{stock, score, confidence, factors}]
        """
        params = self.data['parameters']
        signals = []
        
        for stock in stock_pool:
            factors = []
            buy_score = 0
            
            # 1. 基础评分（权重60%）
            base_score = stock.get('score', 70)
            if base_score >= params['buy_score_threshold']:
                buy_score += base_score * 0.6
                factors.append(f"评分{base_score}，超过阈值{params['buy_score_threshold']}")
            
            # 2. 价格回调机会（权重20%）
            change_rate = stock.get('change_rate', 0)
            if -3 <= change_rate <= 0:  # 小幅回调或微跌
                buy_score += 20
                factors.append(f"价格回调{change_rate:.1f}%，提供入场机会")
            elif change_rate < -3:  # 跌幅过大，谨慎
                buy_score += 10
                factors.append(f"跌幅较大({change_rate:.1f}%)，需观察是否企稳")
            
            # 3. 学习到的经验（权重20%）
            code = stock.get('code', '')
            if code in self.data['stock_performance']:
                perf = self.data['stock_performance'][code]
                if perf['total_profit'] > 0:  # 历史盈利
                    buy_score += 15
                    factors.append(f"历史表现优秀，累计盈利{perf['total_profit']:.1f}%")
                elif perf['trade_count'] >= 2:
                    buy_score += 5
                    factors.append(f"有过交易经验")
            
            # 4. 行业配置
            sector = stock.get('sector', '')
            sector_count = sum(1 for s in stock_pool if s.get('sector') == sector and any(p.get('sector') == sector for p in self.data.get('positions', [])))
            if sector_count < 2:  # 行业集中度控制
                buy_score += 5
                factors.append("行业配置合理")
            
            # 计算置信度
            confidence = min(buy_score / 100, 1.0)
            
            if buy_score >= 70:
                signals.append({
                    'stock': stock,
                    'score': round(buy_score, 1),
                    'confidence': round(confidence, 2),
                    'factors': factors
                })
        
        # 按分数排序
        signals.sort(key=lambda x: x['score'], reverse=True)
        return signals[:5]  # 最多推荐5只
    
    def get_sell_signals(self, position, current_price, market_data):
        """
        根据学习到的知识，判断是否应该卖出
        返回: {action: 'sell'/'hold', reason: str, urgency: 'high'/'medium'/'low'}
        """
        params = self.data['parameters']
        profit_rate = (current_price - position['avg_cost']) / position['avg_cost']
        
        # 1. 止损检查（最高优先级）
        if profit_rate <= -params['max_loss_tolerance']:
            return {
                'action': 'sell',
                'reason': f'触发止损线，亏损{abs(profit_rate)*100:.1f}%',
                'urgency': 'high'
            }
        
        # 2. 止盈检查
        if profit_rate >= params['min_profit_take']:
            return {
                'action': 'sell',
                'reason': f'达到止盈目标，盈利{profit_rate*100:.1f}%，建议锁定收益',
                'urgency': 'medium'
            }
        
        # 3. 大幅盈利保护（回撤止盈）
        if profit_rate > 0.10:
            peak_profit = position.get('peak_profit', profit_rate)
            if profit_rate < peak_profit - 0.05:
                return {
                    'action': 'sell',
                    'reason': f'盈利回撤，从{peak_profit*100:.1f}%降至{profit_rate*100:.1f}%，保护利润',
                    'urgency': 'low'
                }
        
        # 4. 评分下降警告
        code = position.get('code', '')
        if code in self.data['stock_performance']:
            perf = self.data['stock_performance'][code]
            recent_sells = perf.get('sell_records', [])
            if recent_sells and len(recent_sells) >= 2:
                avg_profit = sum(s['profit_rate'] for s in recent_sells[-3:]) / min(3, len(recent_sells))
                if profit_rate > avg_profit + 0.05:
                    return {
                        'action': 'sell',
                        'reason': f'当前盈利高于历史平均({avg_profit*100:.1f}%)，建议落袋为安',
                        'urgency': 'low'
                    }
        
        return {
            'action': 'hold',
            'reason': '暂无明确卖出信号',
            'urgency': 'none'
        }
    
    def get_market_insight(self):
        """生成市场洞察"""
        insights = []
        
        # 分析最近10笔交易
        recent_trades = self.data['trade_history'][-10:]
        if len(recent_trades) >= 5:
            buys = [t for t in recent_trades if t.get('action') == 'buy']
            sells = [t for t in recent_trades if t.get('action') == 'sell']
            
            if sells:
                avg_profit = sum(t.get('profit_rate', 0) for t in sells) / len(sells)
                insights.append(f"近期卖出平均收益率: {avg_profit*100:.1f}%")
                
                if avg_profit > 0:
                    insights.append("当前策略总体有效，继续执行")
                else:
                    insights.append("近期亏损较多，考虑提高买入标准")
        
        # 评分阈值
        threshold = self.data['parameters']['buy_score_threshold']
        insights.append(f"当前买入评分阈值: {threshold}（系统自动调整中）")
        
        return insights
    
    def auto_learn(self):
        """自动学习：根据持仓表现调整策略"""
        if not os.path.exists(PORTFOLIO_FILE):
            return
            
        with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
        
        # 检查持仓是否需要卖出
        actions = []
        for pos in portfolio.get('positions', []):
            # 更新峰值盈利
            current_profit = pos.get('profit_rate', 0)
            peak_profit = pos.get('peak_profit', current_profit)
            if current_profit > peak_profit:
                pos['peak_profit'] = current_profit
        
        # 保存更新
        with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        
        return actions

# 全局实例
engine = LearningEngine()

if __name__ == "__main__":
    # 测试学习引擎
    le = LearningEngine()
    print("学习引擎初始化完成")
    print(f"历史交易: {len(le.data['trade_history'])} 笔")
    print(f"追踪个股: {len(le.data['stock_performance'])} 只")
    print(f"当前参数: {le.data['parameters']}")
