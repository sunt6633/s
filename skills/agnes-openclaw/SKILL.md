---
name: agnes-openclaw
description: 为 OpenClaw 配置 Agnes AI 模型（文本/图像/视频）。适用于需要将 Agnes AI 免费模型接入 OpenClaw 的场景。
---

# 为 OpenClaw 配置 Agnes AI

## 背景

Agnes AI 提供免费的大模型 API（文本/图像/视频），兼容 OpenAI 格式。本 skill 记录将 Agnes 接入 OpenClaw 的完整流程。

## 关键信息

- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **API Key 获取**: https://agnes-ai.com/（注册后创建）
- **模型列表**:
  - `agnes-1.5-flash` — 文本，256K 上下文
  - `agnes-2.0-flash` — 文本，256K 上下文（推荐）
  - `agnes-image-2.0-flash` — 文生图
  - `agnes-image-2.1-flash` — 文生图
  - `agnes-video-v2.0` — 文生视频

## 配置步骤

### 1. 停止 OpenClaw 网关

```bash
# 方法1：任务管理器结束 node.exe
# 方法2：命令行
for pid in $(netstat -ano 2>/dev/null | grep ':18789' | grep 'LISTENING' | awk '{print $5}'); do
  taskkill //F //PID $pid 2>/dev/null
done
```

**重要**：必须先停止网关，否则 `openclaw.json` 被 node 进程锁住无法写入。

### 2. 编辑配置文件

文件路径：`E:\openclaw\.openclaw\openclaw.json`

在 `"providers"` 中添加 `agnes` provider：

```json
"agnes": {
  "baseUrl": "https://apihub.agnes-ai.com/v1",
  "apiKey": "sk-YOUR_API_KEY_HERE",
  "api": "openai-completions",
  "timeoutSeconds": 120,
  "models": [
    {
      "id": "agnes-1.5-flash",
      "name": "Agnes-1.5-Flash (免费·文本)",
      "reasoning": false,
      "input": ["text"],
      "contextWindow": 262144,
      "maxTokens": 65536,
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    },
    {
      "id": "agnes-2.0-flash",
      "name": "Agnes-2.0-Flash (免费·文本)",
      "reasoning": false,
      "input": ["text"],
      "contextWindow": 262144,
      "maxTokens": 65536,
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    },
    {
      "id": "agnes-image-2.0-flash",
      "name": "Agnes-Image-2.0-Flash (免费·文生图)",
      "reasoning": false,
      "input": ["text", "image"],
      "contextWindow": 32768,
      "maxTokens": 4096,
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    },
    {
      "id": "agnes-image-2.1-flash",
      "name": "Agnes-Image-2.1-Flash (免费·文生图)",
      "reasoning": false,
      "input": ["text", "image"],
      "contextWindow": 32768,
      "maxTokens": 4096,
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    },
    {
      "id": "agnes-video-v2.0",
      "name": "Agnes-Video-V2.0 (免费·文生视频)",
      "reasoning": false,
      "input": ["text", "image"],
      "contextWindow": 32768,
      "maxTokens": 4096,
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    }
  ]
}
```

### 3. 设置主模型（可选）

在 `openclaw.json` 顶部修改：

```json
"agents": {
  "defaults": {
    "model": {
      "primary": "agnes/agnes-2.0-flash",
      "fallbacks": [
        "siliconflow/deepseek-ai/DeepSeek-V3",
        "xiaomi/mimo-v2.5-pro"
      ]
    }
  }
}
```

### 4. 更新 start-gateway.bat（可选）

文件路径：`E:\openclaw\start-gateway.bat`

添加环境变量（如果要使用环境变量方式）：

```batch
set AGNES_API_KEY=sk-YOUR_API_KEY_HERE
```

**注意**：如果选择硬编码 API Key 到 `openclaw.json`，则不需要修改 bat 文件。

### 5. 重启网关

双击 `E:\openclaw\start-gateway.bat`

## 常见问题

### Q1: 401 错误 - 无效的令牌

**原因**：API Key 无效或过期

**解决方法**：
1. 确认 API Key 正确（去 https://agnes-ai.com/ 重新生成）
2. 测试 API Key 是否有效：
   ```bash
   curl -s -X POST "https://apihub.agnes-ai.com/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{"model":"agnes-2.0-flash","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}'
   ```

### Q2: 文件被进程锁住无法编辑

**原因**：OpenClaw 网关正在运行，node 进程锁住了 `openclaw.json`

**解决方法**：
1. 停止网关（任务管理器结束 node.exe）
2. 或使用 Python 直接写入（绕过文件锁）：
   ```python
   with open('E:/openclaw/.openclaw/openclaw.json', 'w', encoding='utf-8') as f:
       json.dump(config, f, indent=2, ensure_ascii=False)
   ```

### Q3: 图像/视频模型无法调用

**原因**：OpenClaw 的 `api: "openai-completions"` 可能不支持图像/视频生成端点

**解决方法**：
- 文本模型正常可用
- 图像/视频需要测试确认是否支持，可能需要使用专用端点（`/v1/images/generations`、`/v1/videos`）

## 注意事项

1. **Agnes AI 免费但不保证 SLA**，高峰期可能 500/502
2. **免费不等于永远免费**，不要作为生产环境依赖
3. **API Key 不要提交到 Git**，使用环境变量或 `.gitignore`
4. **图像/视频模型**可能需要较长时间处理，建议设置较长超时（`timeoutSeconds: 120`）

## 验证配置

启动网关后，在飞书给 OpenClaw 发消息，确认使用 `agnes/agnes-2.0-flash` 模型回复。

检查日志：`E:\openclaw\gateway-stdout.log`
