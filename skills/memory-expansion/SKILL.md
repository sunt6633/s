---
name: memory-expansion
description: "Hermes Agent记忆系统扩容方案：从2KB到5KB+Wiki知识库"
version: 1.0
author: 办龙
created: 2026-06-03
tags: [memory, wiki, optimization, config]
---

# Hermes Agent 记忆系统扩容方案

## 问题

Hermes 默认 memory 容量只有 2200 字符（约15条微博），很快就会满。新内容会挤掉旧内容，导致反复教它同样的东西。

## 解决方案

### 第一步：改大 memory_char_limit

**配置文件位置**：`~/.hermes/config.yaml`

**正确写法**（必须嵌套在 memory: 下面）：

```yaml
memory:
  memory_char_limit: 5000
```

**常见错误**：
- ❌ `memory_chars: 5000`（配置项名错误）
- ❌ `memory_char_limit: 5000`（顶级配置，不生效）
- ✅ `memory:\n  memory_char_limit: 5000`（正确嵌套）

**默认值**：2200 字符
**推荐值**：5000 字符（平衡 token 消耗和存储空间）

### 第二步：建 LLM Wiki 知识库

**目录结构**：

```
~/wiki/
├── index.md           # 页面索引
├── SCHEMA.md          # 数据模式定义
├── log.md             # 变更日志
├── reference_graph.json  # 引用关系图
├── concepts/          # 概念性知识
│   ├── hermes-config.md
│   ├── system-environment.md
│   └── nutstore-storage.md
├── entities/          # 具体工具/项目
│   ├── openclaw.md
│   ├── feilong-group.md
│   └── wordpress-blog.md
└── scripts/           # 维护工具
    ├── wiki_lint.py   # 质量检查脚本
    └── reference_graph.py
```

**页面模板**：

```markdown
---
title: 页面标题
created: 2026-06-03
updated: 2026-06-03
type: entity  # 或 concept
tags: [tag1, tag2]
sources: [memory]
confidence: high
---

# 页面标题

## Overview
简要描述

## Key Configuration
- 配置项1: 值1
- 配置项2: 值2

## Related Pages
- [[other-page]] - 关联说明
```

### 第三步：精简 Memory

**原则**：memory 只存一句话索引，详细内容放 Wiki

**示例**：
- 改前：`OpenClaw(小龙)网关：F:\openclaw，端口18789，token=openclaw123456，模型mimo-v2.5-pro。watchdog计划任务已部署。配置文件F:\openclaw\openclaw.json必须包含models和agents段。`
- 改后：`OpenClaw(小龙)配置详见wiki [[openclaw]]。网关F:\openclaw，端口18789，有watchdog守护。`

### 第四步：自动质量检查

**脚本位置**：`~/wiki/scripts/wiki_lint.py`

**检查内容**：
- 孤儿页（无引用）
- 断链（指向不存在的页面）
- Frontmatter 缺失字段
- 超大页面（>200行）
- 未在 index 中

**定时任务**：

```python
# cron job 设置
schedule: "0 9 * * 1"  # 每周一早上9点
script: "wiki_lint.py"
```

**注意**：脚本里的 WIKI_PATH 必须硬编码为实际路径（如 `D:\wiki`），不能用 `~/wiki`。

## 效果

| 指标 | 改前 | 改后 |
|------|------|------|
| memory 使用率 | 85% (1874/2200) | 12% (616/5000) |
| 条目数 | 11条 | 9条 |
| Wiki 页面 | 8个 | 10个 |
| 质量检查 | 无 | 每周自动 |

## 注意事项

1. 改完配置后必须重启 gateway 才生效
2. Wiki 页面之间用 `[[双括号]]` 互相引用
3. 批处理脚本写 Windows 必须用 GBK 编码，UTF-8 会乱码
4. wiki_lint.py 路径问题：`os.path.expanduser("~/wiki")` 在某些环境下会解析错误，建议硬编码
