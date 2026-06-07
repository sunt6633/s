---
name: agnes-hermes
description: 为 Hermes Agent 配置 Agnes AI 模型（文本/图像/视频）。适用于需要将 Agnes AI 免费模型接入 Hermes 的场景。
---

# 为 Hermes Agent 配置 Agnes AI

## 背景

Agnes AI 提供免费的大模型 API（文本/图像/视频），兼容 OpenAI 格式。本 skill 记录将 Agnes 接入 Hermes Agent 的完整流程。

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

### 1. 停止 Hermes 网关

```bash
# 方法1：任务管理器结束 hermes.exe
# 方法2：命令行
taskkill //F //IM hermes.exe 2>/dev/null
```

**重要**：必须先停止网关，否则 `config.yaml` 被进程锁住无法写入。

### 2. 使用 hermes config set 命令配置（推荐）

这是 Hermes 官方推荐的方式，使用 `hermes config set` 命令：

```powershell
& "D:\hermes\.venv\Scripts\hermes.exe" config set model.provider custom
& "D:\hermes\.venv\Scripts\hermes.exe" config set model.base_url https://apihub.agnes-ai.com/v1
& "D:\hermes\.venv\Scripts\hermes.exe" config set model.api_key sk-YOUR_API_KEY_HERE
& "D:\hermes\.venv\Scripts\hermes.exe" config set model.default agnes-2.0-flash
```

**关键**：
- `model.provider` 必须设为 `custom`（不是 `agnes`）
- Hermes 会通过 `base_url` 和 `api_key` 直接调用 API
- 模型 ID 区分大小写，建议直接复制平台提供的名称

### 3. 手动编辑配置文件（备用方法）

如果命令配置失败，可以手动编辑：

文件路径：`C:\Users\sunt1\.hermes\config.yaml`

```yaml
model:
  default: agnes-2.0-flash
  provider: custom
  base_url: https://apihub.agnes-ai.com/v1
  api_key: sk-YOUR_API_KEY_HERE
```

**注意**：
- 不要添加 `providers.agnes` 这样的自定义 provider（Hermes 不认识）
- API Key 可以直接硬编码，也可以通过 `env:AGNES_API_KEY` 引用环境变量

### 4. 配置环境变量（可选）

文件路径：`D:\hermes\start-gateway.bat`

```batch
set AGNES_API_KEY=sk-YOUR_API_KEY_HERE
set API_SERVER_PORT=8642
set API_SERVER_KEY=hermes-dashboard-2026
set GATEWAY_ALLOW_ALL_USERS=true
```

### 5. 配置 fallback（可选）

如果需要 fallback 到其他模型（如 SiliconFlow 的 DeepSeek-V3），可以在 `config.yaml` 中添加：

```yaml
model:
  default: agnes-2.0-flash
  fallback: siliconflow/deepseek-ai/DeepSeek-V3
  provider: custom
  base_url: https://apihub.agnes-ai.com/v1
  api_key: sk-YOUR_API_KEY_HERE
providers:
  siliconflow:
    base_url: https://api.siliconflow.cn/v1
    api_key: sk-YOUR_SILICONFLOW_KEY
```

**注意**：Hermes 可能会自动修改 `config.yaml`，建议定期检查配置是否被重置。

### 6. 重启网关

双击 `D:\hermes\start-gateway.bat`

或手动启动：

```bash
cd /d D:\hermes
D:\hermes\.venv\Scripts\hermes.exe gateway run
```

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

### Q2: WARNING gateway.run: API Server: aiohttp not installed

**原因**：aiohttp 包损坏或缺失

**解决方法**：
```powershell
& "D:\hermes\.venv\Scripts\pip.exe" install --force-reinstall -i https://mirrors.aliyun.com/pypi/simple/ aiohttp==3.13.5
```

**注意**：这个 WARNING 是误报，不影响飞书 WebSocket 连接，但会导致仪表盘（端口 8642）无法启动。

### Q3: 提供商认证失败：未知的提供商 'siliconflow'

**原因**：`model.provider` 被设成了 `siliconflow`（Hermes 不认识这个 provider）

**解决方法**：
```powershell
& "D:\hermes\.venv\Scripts\hermes.exe" config set model.provider custom
```

然后重启网关。

### Q4: Hermes 启动后自动改回配置

**原因**：Hermes 可能会根据 `hermes config set` 的历史记录自动重置配置

**解决方法**：
1. 停止 Hermes
2. 手动编辑 `config.yaml`，确保 `provider: custom`
3. 不要使用 `fallback` 引用不认识的 provider
4. 重启后检查配置是否被修改

### Q5: 仪表盘无法访问

**原因**：aiohttp 未安装或端口被占用

**解决方法**：
1. 确认 aiohttp 已安装（见 Q2）
2. 检查端口 8642 是否被占用：
   ```bash
   netstat -ano 2>/dev/null | grep ':8642' | grep LISTENING
   ```
3. 如果占用，修改 `start-gateway.bat` 中的 `API_SERVER_PORT`

## 注意事项

1. **Agnes AI 免费但不保证 SLA**，高峰期可能 500/502
2. **免费不等于永远免费**，不要作为生产环境依赖
3. **API Key 不要提交到 Git**，使用环境变量或 `.gitignore`
4. **Hermes 会修改 config.yaml**，建议定期备份配置
5. **使用 `custom` provider**，不要尝试添加自定义 provider 名称

## 验证配置

启动网关后，检查日志：

```
[Lark] [2026-06-07 17:04:48,736] [INFO] connected to wss://msg-frontier.feishu.cn/...
```

去飞书给 Hermes 发消息，确认使用 `agnes-2.0-flash` 模型回复。

检查仪表盘：http://127.0.0.1:8642

## 完整配置示例

**config.yaml**:
```yaml
model:
  default: agnes-2.0-flash
  provider: custom
  base_url: https://apihub.agnes-ai.com/v1
  api_key: sk-xQR3fyTUroHh1vlcurpGUU6A0Jscf4AfT4KVBnB0sbVotv45
providers:
  siliconflow:
    base_url: https://api.siliconflow.cn/v1
    api_key: sk-opwrojtokckwuaufhthptcdsoxyqwraeojcsayracwzfnzmg
  agnes:
    base_url: https://apihub.agnes-ai.com/v1
    api_key: sk-xQR3fyTUroHh1vlcurpGUU6A0Jscf4AfT4KVBnB0sbVotv45
```

**start-gateway.bat**:
```batch
@echo off
chcp 65001 >nul
set XIAOMI_API_KEY=tp-cb19q3o8ax9zd5kem9ra41md9iioo4nxl6cdzu1uyumcxo3o
set XIAOMI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
set SILICONFLOW_API_KEY=sk-opwrojtokckwuaufhthptcdsoxyqwraeojcsayracwzfnzmg
set AGNES_API_KEY=sk-xQR3fyTUroHh1vlcurpGUU6A0Jscf4AfT4KVBnB0sbVotv45
set FEISHU_APP_ID=cli_aa885f9a3eb91bdb
set FEISHU_APP_SECRET=IROKh7ro0JZ2X7ng2agmLfCVncisRwdA
set FEISHU_CONNECTION_MODE=websocket
set API_SERVER_PORT=8642
set API_SERVER_KEY=hermes-dashboard-2026
set GATEWAY_ALLOW_ALL_USERS=true
...
```
