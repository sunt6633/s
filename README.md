# 🦐 小腾工具库 (sunt)

> 孙先生的专属AI助手小腾的工具箱，目标是让小腾更强、更能赚钱！

## 📁 目录结构

```
sunt/
├── skills/          # Skills技能包
│   ├── glmv-stock-analyst/   # 股票分析报告生成 ⭐
│   └── glmocr/               # OCR文字识别
├── tools/           # 金融交易工具
│   ├── stock_selector_v*.py  # 选股系统
│   ├── trading_engine*.py     # 交易引擎
│   └── data_source.py        # 数据源
├── scripts/         # 常用脚本
│   ├── update_pool.py        # 更新股票池行情
│   └── verify_data.py        # 验证数据
├── configs/         # 配置文件
│   └── user_profile.json     # 用户画像
├── templates/       # 模板
└── workflows/       # 工作流程
```

## 🚀 快速使用

### 1. 股票分析（glmv-stock-analyst）
```bash
python scripts/run_stock_analysis.py 601318.SH  # 分析中国平安
python scripts/run_stock_analysis.py 000063.SZ  # 分析中兴通讯
```

### 2. 更新股票池行情
```bash
cd D:/for workbuddy/finance_bot
python update_pool.py
```

### 3. 验证交易数据
```bash
cd D:/for workbuddy/finance_bot
python verify_data.py
```

## 📊 赚钱能力

| 能力 | 状态 | 说明 |
|------|------|------|
| 股票分析 | ✅ 已掌握 | 多源数据分析、K线图、资金流向 |
| 量化选股 | ✅ 已掌握 | v6.0选股系统，评分因子超过10个 |
| 模拟交易 | ✅ 运行中 | 10万本金，当前盈利16%+ |
| 实时行情 | ✅ 已集成 | tushare Pro + akshare双数据源 |
| OCR识别 | ✅ 已掌握 | 表格、手写、公式识别 |

## 🔧 开发指南

### 添加新工具
1. 在对应目录创建文件
2. 更新本README
3. git add → commit → push

### 同步到其他机器
```bash
git clone https://gitee.com/sunt111/sunt.git
```

## 📈 进化记录

| 日期 | 进化内容 |
|------|----------|
| 2026-04-17 | 创建工具库，整合股票分析skill和金融工具 |

## ⚠️ 注意事项

- 所有工具仅供模拟交易练习
- 实盘操作需谨慎，后果自负
- 禁止往C盘存放任何文件

---
*🦐 小腾出品 | 专为孙先生赚钱而生*
