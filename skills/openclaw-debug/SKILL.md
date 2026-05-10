---
name: openclaw-debug
description: OpenClaw 本地网关调试与小米 MiMo API 接入完整指南。包含今天踩过的 5 个坑、每个报错的真实原因和修法、最终可运行的配置模板、排障检查清单。当用户遇到 OpenClaw 网关不通、模型不响应、Config invalid 报错、或需要配置 Xiaomi MiMo/第三方 API 时触发。
version: 1.1.0
author: 大成子
tags: [openclaw, mimo, debugging, gateway, config]
agent_created: true
---

# OpenClaw 调试与 MiMo 接入 — 实战踩坑全记录

## 今天踩过的 5 个坑

### 坑 1：PI_KEY 不是内部或外部命令

**现象**：双击 start-chat.bat，黑窗口闪一下，报 `PI_KEY 不是内部或外部命令`。

**原因**：bat 文件里直接写了 `PI_KEY xxxxx`，少了 `set`。Windows 批处理里设置环境变量必须用 `set PI_KEY=xxx`，不能直接写变量名。

**修法**：
```bat
@echo off
set PI_KEY=your_key_here
```
而不是：
```bat
@echo off
PI_KEY=your_key_here   ← 错
```

---

### 坑 2：'com' 不是内部或外部命令

**现象**：bat 里写了某行，报 `com 不是内部或外部命令`。

**原因**：通常是 `.bat` 文件里路径或命令被空格截断，或者 `%VAR%` 展开后出了奇怪的东西。比如路径里有空格但没加引号。

**修法**：路径永远加引号：
```bat
cd "E:\openclaw"
node "dist\entry.js" gateway --port 18789
```
而不是：
```bat
cd E:\openclaw   ← 路径有空格会炸
```

---

### 坑 3：Config invalid — api 字段值不合法

**现象**：网关起不来，报：
```
Invalid config at C:\Users\sunt1\.openclaw\openclaw.json:
- models.providers.xiaomi.api: Invalid input
```

**原因**：`api` 字段只能填枚举值，填错一个字母都不行。

**合法枚举值**（从源码 `zod-schema.core.js` 挖出来的）：
- `openai-completions` ← 小米 MiMo 用这个
- `openai-responses`
- `anthropic-messages`
- `google-generative-ai`
- `github-copilot`
- `bedrock-converse-stream`
- `ollama`

填了 `openai-chat`、`openai-compat` 这种不存在的值必炸。

**修法**：确认 `openclaw.json` 里是：
```json
"api": "openai-completions"
```

---

### 坑 4：Model "mimo-v2.5" without provider

**现象**：网关能起，但对话没反应，日志里看到：
```
Model "mimo-v2.5" specified without provider.
Falling back to "anthropic/mimo-v2.5"
```

**原因**：模型 ID 必须带 provider 前缀，格式 `{provider}/{model}`。

**修法**：
```json
"primary": "xiaomi/mimo-v2.5"
```
而不是：
```json
"primary": "mimo-v2.5"   ← 少了前缀
```

---

### 坑 5：向导把配置覆盖成 Anthropic 接口

**现象**：本来配好的 MiMo，运行了一下向导（wizard configure），结果网关起不来了。

**原因**：向导会把 `baseUrl` 改成 `api.xiaomimimo.com/anthropic`，把 `api` 改成 `anthropic-messages`。但 MiMo 是 OpenAI 兼容接口，不是 Anthropic，直接跪。

**修法**：向导跑完后，手动把 `openclaw.json` 改回：
```json
"baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
"api": "openai-completions"
```

---

## 核心配置文件位置

**唯一生效的配置**：`C:\Users\{用户名}\.openclaw\openclaw.json`

注意：不要被 `E:\openclaw\openclaw.json` 或项目本地目录迷惑，向导配置一定写入用户主目录的 `.openclaw`。

---

## 最终能跑的通的配置模板

`C:\Users\sunt1\.openclaw\openclaw.json`：

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "xiaomi": {
        "baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
        "apiKey": "你的_API_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "mimo-v2.5",
            "name": "Xiaomi MiMo V2.5",
            "reasoning": true,
            "input": ["text"],
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
            "contextWindow": 131072,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "xiaomi/mimo-v2.5"
      }
    }
  },
  "gateway": {
    "port": 18789,
    "token": "openclaw123"
  }
}
```

---

## 排障检查清单

网关起不来，按顺序查：

1. **配置文件路径对不对** — 唯一生效的是 `C:\Users\{用户}\.openclaw\openclaw.json`，别被项目目录下的同名文件迷惑
2. **`api` 字段是不是合法枚举** — 只能填上面列的 7 个值
3. **模型 ID 有没有带 provider 前缀** — 必须是 `xiaomi/mimo-v2.5`
4. **baseUrl 是不是 OpenAI 兼容的** — MiMo 用 `https://token-plan-cn.xiaomimimo.com/v1`
5. **改完配置重启网关** — 不重启不生效
6. **验证网关健康**：
   ```bash
   curl http://127.0.0.1:18789/api/health -H "Authorization: Bearer openclaw123"
   ```

---

## 调试步骤

1. **查看网关启动日志**，关注这几行：
   - `[gateway] agent model: xiaomi/mimo-v2.5` ← 正常（带 provider 前缀）
   - `[gateway] agent model: anthropic/mimo-v2.5` ← 有问题（fallback）
   - `Config invalid` ← 配置校验失败，看具体报错

2. **验证 API 直连**：用 curl/PowerShell 直接 POST 到 `baseUrl/chat/completions`，确认 API 本身是否可用

3. **检查配置文件**：`C:\Users\{user}\.openclaw\openclaw.json`，特别是：
   - `models.providers.{name}.api` 是否是合法枚举
   - `models.providers.{name}.baseUrl` 是否指向正确端点
   - `agents.defaults.model.primary` 是否带 provider 前缀

4. **重启网关**：修改配置后必须重启才能生效
   - 启动脚本：`node node_modules/openclaw-cn/dist/entry.js gateway --port 18789`
   - 或在 `E:\openclaw` 目录双击 `restart-gateway.bat`

5. **验证网关健康**：
   ```
   GET http://127.0.0.1:18789/api/health
   Headers: Authorization: Bearer openclaw123
   ```

---

## 相关文件

- 网关启动脚本：`E:\openclaw\start-gateway.bat`、`restart-gateway.bat`
- 网关日志：`\tmp\clawdbot\clawdbot-{date}.log`
- Canvas 目录：`C:\Users\sunt1\clawd\canvas`

---

## 更新日志

**v1.1.0** (2026-05-10)
- 新增今天踩过的 5 个坑完整记录
- 新增 bat 文件常见错误及修法
- 完善排障检查清单
- 补充网关健康验证方法

**v1.0.0** (2026-05-03)
- 初始版本
- 支持 OpenClaw 调试
- MiMo API 接入指南
