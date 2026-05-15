---
name: blog-publish
description: >
  全自动 WordPress 博客文章发布 Skill。将 AI 生成的高质量技术文章直接发布到博客，
  无需任何人工干预。完全自动化：生成内容 → 调用 WordPress REST API → 发布。
  当用户说"发博客"、"发布文章"、"发一篇技术文章"、"博客自动发布"、"更新博客"时触发。
version: 1.0.0
author: WorkBuddy
tags: [wordpress, automation, blog, publishing, AI writing]
agent_created: true
---

# Blog Publish Skill — 博客自动发布

## 概述

此 Skill 将博客发文流程完全自动化：AI 生成高质量技术文章 → WordPress REST API 发布。
无需任何人工确认，适合每日定时任务。

---

## 配置信息

| 参数 | 值 | 说明 |
|------|-----|------|
| `BLOG_URL` | `http://43.226.44.9` | WordPress 博客地址 |
| `USERNAME` | `sunt` | WordPress 用户名 |
| `APP_PASSWORD` | `bp5RZDmsomAPFlmqk0xenYko` | Application Password（在 WordPress 后台 → 用户 → 安全 → 应用密码生成） |
| `API_ENDPOINT` | `{BLOG_URL}/wp-json/wp/v2/posts` | WordPress REST API 发布端点 |

---

## 发布流程

### 第一步：确认主题

每次发布从以下主题池中按顺序轮换：

1. OpenClaw 技术详解
2. Hermes Agent 实战指南
3. Claude 应用技巧
4. AI Agent 开发实践
5. 技术架构与设计模式

**轮换规则**：按列表顺序循环，每个主题发布完后才轮下一个。

### 第二步：生成文章

要求：
1. **技术含量高**：深入讲解技术细节，提供实用价值
2. **配图丰富**：使用 Markdown 或 HTML 嵌入相关技术图表、代码示例
3. **无 AI 味**：自然流畅的中文表达，避免机械化的 AI 特征
4. **内容详实**：每篇文章 1500–2500 字，结构清晰

**标题格式偏好**：
- "深入解析 XXX：从原理到实践"
- "XXX 技术全景：2026 年最新实战指南"
- "揭秘 XXX：技术大佬不会告诉你的真相"

### 第三步：调用 WordPress API 发布

使用 curl 请求：

```bash
curl -X POST "http://43.226.44.9/wp-json/wp/v2/posts" \
  --user "sunt:bp5RZDmsomAPFlmqk0xenYko" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "title": "文章标题",
    "content": "文章内容（HTML格式）",
    "status": "publish",
    "excerpt": "文章摘要，100字以内"
  }'
```

**注意**：
- `status` 直接设为 `publish`（立即发布），无需草稿
- 内容必须为 HTML 格式
- 响应中的 `id` 字段即为文章 ID

### 第四步：验证结果

- `201 Created`：发布成功
- `401 Unauthorized`：认证失败，检查用户名和应用密码
- `403 Forbidden`：权限不足
- 其他 4xx/5xx：检查网络或博客配置

---

## 文章模板

核心结构：
1. **引言**（200–300 字）：背景 + 为什么这个技术值得关注
2. **技术背景**（300–500 字）：发展历史 / 现状 / 生态
3. **核心原理**（500–800 字）：深入讲解技术细节，配合代码示例
4. **实战案例**（400–600 字）：真实使用场景，步骤化操作指南
5. **最佳实践**（300–500 字）：避坑指南、性能优化、安全注意事项
6. **总结与展望**（200–300 字）：趋势判断、下一步行动建议

---

## 自动化配置

创建每日定时任务（使用 `automation_update` 工具）：
- 名称：`每日自动发布技术文章`
- 时间：每天上午 9 点
- prompt：使用 blog-publish skill，生成并发布一篇技术文章到 WordPress 博客

---

## 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| `401 Unauthorized` | 应用密码错误 | 确认密码无空格，重新在 WordPress 后台生成 |
| `403 Forbidden` | 用户权限不足 | 确认用户角色为"编辑"或"管理员" |
| `400 Bad Request` | JSON 格式错误 | 检查引号转义，确保中文字符正确编码 |
| 网络超时 | 博客地址不可达 | 检查 http://43.226.44.9 是否可访问 |

---

## 注意事项

- 文章直接发布到真实博客，无法撤回
- 确保内容质量和技术准确性
- 保持原创性，避免抄袭
