---
name: openclaw-debug
description: OpenClaw 本地网关调试与小米 MiMo API 接入完整指南。包含所有踩过的坑、每个报错的真实原因和修法、最终可运行的配置模板、排障检查清单。当用户遇到 OpenClaw 网关不通、模型不响应、闪退、或需要配置 Xiaomi MiMo/第三方 API 时触发。
version: 1.4.0
author: 大成子
tags: [openclaw, mimo, debugging, gateway, config]
agent_created: true
---

# OpenClaw 调试与 MiMo 接入 — 实战踩坑全记录

## 坑汇总（共9个，按发生频率排序）

### 坑 1：闪退 — 端口被旧进程占用（最高频）

**现象**：双击 start-gateway.bat，窗口闪一下就没了，日志里报：
```
Gateway failed to start: another gateway instance is already listening on ws://127.0.0.1:18789 | listen EADDRINUSE
```
或者日志还没写完，进程就退出了（stderr/stdout 都是空）。

**原因**：端口 18789 被一个旧进程（通常是之前调试时启动的）占着，新进程抢不到端口就退出了。

**修法（方案A — 杀掉旧进程）**：
```cmd
taskkill /F /PID <旧进程PID>
```
旧 PID 每次不同，日志里会显示，比如：`pid 33780: ... E:\openclaw\node-v24.15.0-win-x64\node.exe`

**修法（方案B — 启动时强制抢占）**：启动脚本加 `--force` 参数，让网关自动杀掉旧进程：
```bat
E:\openclaw\node-v24.15.0-win-x64\node.exe E:\npm-global\node_modules\openclaw\openclaw.mjs gateway --force
```
`--force` 会在启动前自动 kill 掉端口上已有的进程，无需手动停。

**预防**：每次启动都用 `--force`，不要用 `openclaw gateway stop`（它依赖正确的工作目录才能找到进程），直接强制重启最稳。

**注意**：cmd 窗口自动关闭是**正常现象**，不代表网关死了。网关跑在后台进程里。验证是否活着：
```cmd
curl http://localhost:18789/health -H "Authorization: Bearer openclaw123456"
```
返回 `{"ok":true,"status":"live"}` 就是好的。

---

### 坑 2：Config invalid — api 字段值不合法

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

### 坑 2：Config invalid — api 字段值不合法

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

### 坑 3：Model "mimo-v2.5" without provider

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

### 坑 4：向导把配置覆盖成 Anthropic 接口

**现象**：本来配好的 MiMo，运行了一下向导（wizard configure），结果网关起不来了。

**原因**：向导会把 `baseUrl` 改成 `api.xiaomimimo.com/anthropic`，把 `api` 改成 `anthropic-messages`。但 MiMo 是 OpenAI 兼容接口，不是 Anthropic，直接跪。

**修法**：向导跑完后，手动把 `openclaw.json` 改回：
```json
"baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
"api": "openai-completions"
```

---

### 坑 5：Node 版本不够 — requires Node >=22.16.0

**现象**：网关启动失败，报：
```
openclaw requires Node >=22.16.0.
Detected: node 22.12.0 (exec: C:\Users\sunt1\.workbuddy\binaries\node\versions\22.12.0\node.exe).
```

**原因**：OpenClaw 2026.5.12 起要求 Node >=22.16.0，WorkBuddy 自带的 22.12.0 不够。系统 Node 24 在 `C:\Program Files\nodejs\` 但 bash 环境PATH优先用了 workbuddy 的旧版。

**修法**：启动脚本里用完整路径指定 Node：
```bat
set NODE=E:\openclaw\node-v24.15.0-win-x64\node.exe
set OPENCLAW=E:\npm-global\node_modules\openclaw\dist\entry.js
"%NODE%" "%OPENCLAW%" gateway --port 18789
```

---

### 坑 6：gateway.token 不再是合法配置项

**现象**：网关启动失败，报：
```
Invalid config: gateway: Unrecognized key: "token"
```

**原因**：OpenClaw 2026.5.12 移除了 `gateway.token` 字段。老版本可以配，新版不行。

**修法**：删除 `gateway.token`，新版会在启动时自动生成 runtime token：
```json
"gateway": {
  "mode": "local",
  "port": 18789
}
```

---

### 坑 7：gateway.mode 是必填项

**现象**：网关启动失败，报：
```
Gateway start blocked: existing config is missing gateway.mode.
```

**原因**：新版要求 `gateway.mode` 字段，不填就启动不了。

**修法**：加上 `"mode": "local"`：
```json
"gateway": {
  "mode": "local",
  "port": 18789
}
```

---

## 核心配置文件位置

**默认配置路径**：`C:\Users\{用户名}\.openclaw\openclaw.json`

**推荐：迁移到 E 盘**（通过环境变量 `OPENCLAW_STATE_DIR` 覆盖）：
- 在启动脚本里设置 `set OPENCLAW_STATE_DIR=E:\openclaw\state`
- openclaw 会读 `E:\openclaw\state\openclaw.json`，不再碰 C 盘
- 支持的环境变量：
  - `OPENCLAW_STATE_DIR`：状态目录（含 openclaw.json）
  - `OPENCLAW_CONFIG_PATH`：直接指定配置文件完整路径

注意：向导配置默认写入 C 盘，手动跑向导后记得把配置文件迁回 E 盘。

---

## 最终能跑通的配置模板

### 模板1：NVIDIA NIM（Mistral Large 3 675B）

`C:\Users\sunt1\.openclaw\openclaw.json`：

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "nv": {
        "baseUrl": "https://integrate.api.nvidia.com/v1",
        "apiKey": "你的_NVIDIA_API_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "mistralai/mistral-large-3-675b-instruct-2512",
            "name": "Mistral Large 3 675B (NVIDIA NIM)",
            "reasoning": false,
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
        "primary": "nv/mistralai/mistral-large-3-675b-instruct-2512"
      }
    }
  },
  "gateway": {
    "mode": "local",
    "port": 18789
  }
}
```

**注意**：
- provider 名用 `nv` 而不是 `nvidia`，因为 NVIDIA NIM 的模型 ID 已经含 `mistralai/` 前缀，provider 名 `nvidia` 会导致引用变成 `nvidia/mistralai/...` 容易混淆
- `gateway.token` 已废弃，不需要配
- `gateway.mode: "local"` 是必填项

### 模板2：小米 MiMo（当前生产配置）

`E:\openclaw\state\openclaw.json`（通过 `OPENCLAW_STATE_DIR=E:\openclaw\state` 加载）：

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "xiaomi": {
        "baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
        "apiKey": "tp-cm26v36gu0yxq8c9dm2moiu477fjzlx40mwyfqx43cxb2mqp",
        "api": "openai-completions",
        "models": [
          {
            "id": "mimo-v2.5-pro",
            "name": "Xiaomi MiMo V2.5 Pro",
            "reasoning": true,
            "input": ["text"],
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
            "contextWindow": 131072,
            "maxTokens": 8192
          },
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
        "primary": "xiaomi/mimo-v2.5-pro"
      }
    }
  },
  "gateway": {
    "mode": "local",
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "openclaw123456"
    }
  }
}
```

**关键点**：
- `api` 必须是 `"openai-completions"`，不能是 `"openai"`（常见错误！）
- 模型列表要用对象格式（含 `id`/`name`/`reasoning` 等字段），不能只写字符串数组
- `agents.defaults.model.primary` 必须带 `xiaomi/` 前缀

---

## 排障检查清单（按顺序查）

**1. 端口是否被占用（最高频！）**
- 运行 `netstat -ano | findstr 18789`
- 有结果说明旧进程还在，先杀掉：
  ```cmd
  taskkill /F /PID <PID>
  ```
  或者直接重新双击 `start-gateway.bat`（已含 `--force`，会自动抢占）

**2. cmd 窗口关闭了 ≠ 网关死了**
- 验证：`curl http://localhost:18789/health -H "Authorization: Bearer openclaw123456"`
- 返回 `{"ok":true,"status":"live"}` 就是好的
- Control UI 浏览器访问：http://localhost:18791（填 token `openclaw123456`）

**3. `api` 字段是不是合法枚举** — 只能填7个值，必须 `"openai-completions"`
2. **模型 ID 有没有带 provider 前缀** — 必须是 `xiaomi/mimo-v2.5-pro` 格式
3. **baseUrl 是否正确** — MiMo 用 `https://token-plan-cn.xiaomimimo.com/v1`
4. **gateway.mode 是否设置** — 必须是 `"local"`
5. **OPENCLAW_STATE_DIR 是否设置** — 启动脚本里有没有 `set OPENCLAW_STATE_DIR=E:\openclaw\state`
6. **改完配置重启网关** — 不重启不生效，双击 `restart-gateway.bat`
7. **验证 MiMo API 直连**（Python）：
   ```python
   import urllib.request, json, ssl
   data = json.dumps({"model":"mimo-v2.5-pro","messages":[{"role":"user","content":"hi"}],"max_tokens":10}).encode()
   req = urllib.request.Request("https://token-plan-cn.xiaomimimo.com/v1/chat/completions", data=data,
       headers={"Content-Type":"application/json","Authorization":"Bearer YOUR_KEY"})
   with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
       print(json.loads(r.read()))
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
   - 停止：`"E:\openclaw\node-v24.15.0-win-x64\node.exe" "E:\npm-global\node_modules\openclaw\dist\entry.js" gateway stop`
   - 启动：在 `E:\openclaw` 目录双击 `start-gateway.bat` 或 `restart-gateway.bat`

5. **验证网关健康**：
   ```
   GET http://127.0.0.1:18789/api/health
   Headers: Authorization: Bearer openclaw123
   ```

---

## 相关文件

- Node 24 运行时：`E:\openclaw\node-v24.15.0-win-x64\node.exe`
- npm 全局包目录：`E:\npm-global\node_modules\`
- openclaw 入口：`E:\npm-global\node_modules\openclaw\openclaw.mjs`
- 网关启动脚本：`E:\openclaw\start-gateway.bat`（后台）、`restart-gateway.bat`（重启）、`debug-gateway.bat`（前台调试）
- 配置文件（E盘，推荐）：`E:\openclaw\state\openclaw.json`
- 配置文件（C盘，备用）：`C:\Users\sunt1\.openclaw\openclaw.json`
- 网关日志：`E:\openclaw\gateway-stdout.log`、`E:\openclaw\gateway-stderr.log`
- Canvas 目录：`C:\Users\sunt1\clawd\canvas`

## 启动脚本关键设置

```bat
@echo off
chcp 65001 >nul
set OPENCLAW_STATE_DIR=E:\openclaw\state
echo Starting OpenClaw Gateway...

E:\openclaw\node-v24.15.0-win-x64\node.exe E:\npm-global\node_modules\openclaw\openclaw.mjs gateway --force
pause
```

**关键点**：
- `--force`：自动杀掉端口上已有的旧进程，无需手动停
- `chcp 65001`：防止中文乱码
- `OPENCLAW_STATE_DIR`：读 E 盘配置，不设则默认读 C 盘
- `pause`：方便看退出原因（可去掉改为后台运行）

---

## 端口说明

| 端口 | 用途 |
|------|------|
| 18789 | 主 Gateway API（HTTP/WebSocket） |
| 18791 | Control UI（浏览器控制面板） |

两个端口互相独立，都需要认证 token `openclaw123456`。

---

## 相关文件

- Node 24 运行时：`E:\openclaw\node-v24.15.0-win-x64\node.exe`
- npm 全局包目录：`E:\npm-global\node_modules\`
- openclaw 入口：`E:\npm-global\node_modules\openclaw\openclaw.mjs`
- **启动脚本（核心）**：`E:\openclaw\start-gateway.bat` — 含 `--force` 和 `OPENCLAW_STATE_DIR`
- 重启脚本：`E:\openclaw\restart-gateway.bat`
- 前台调试脚本：`E:\openclaw\debug-gateway.bat`（保留日志输出）
- 配置文件（E盘）：`E:\openclaw\state\openclaw.json`
- 配置文件（C盘）：`C:\Users\sunt1\.openclaw\openclaw.json`（需同步维护）
- 网关日志：`E:\openclaw\gateway-stdout.log`、`E:\openclaw\gateway-stderr.log`
- 运行时日志（系统）：`C:\Users\sunt1\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log`

---

## 全E盘安装方案（无C盘依赖）

如果要求所有依赖不在C盘：

1. 下载 Node.js 到 `E:\openclaw\node-v24.15.0-win-x64\`（zip版）
2. 设置 npm 全局前缀：`npm config set prefix "E:\npm-global"`
3. 安装 openclaw：`npm install -g openclaw@latest`（装到 `E:\npm-global\`）
4. 启动脚本用完整路径（见上方启动脚本）
5. **必须同时维护两个配置文件**：
   - `E:\openclaw\state\openclaw.json`（主配置，OPENCLAW_STATE_DIR指向）
   - `C:\Users\sunt1\.openclaw\openclaw.json`（openclaw默认读这个，防止向导覆盖）

---

## 更新日志

**v1.4.0** (2026-05-17 下午)
- 新增坑1（最高频）：闪退根因是端口被旧进程占用，解决方案是启动加 `--force` 参数
- 坑号重新整理：移除低频坑（PI_KEY、路径空格），保留7个高价值坑
- 新增"端口说明"：18789是主API，18791是Control UI
- 排障清单重写：端口检查作为第一步，cmd窗口关闭≠网关死
- 启动脚本更新：加入 `--force`、`chcp 65001`、`pause`
- 启动脚本注释：说明每个参数的作用
- 相关文件：新增启动脚本路径说明

**v1.3.0** (2026-05-17)
- 发现并记录坑9：`api` 填 `"openai"` 无效，必须 `"openai-completions"`
- 新增 E 盘配置迁移方案（OPENCLAW_STATE_DIR 环境变量）
- 更新 MiMo 配置模板（含 mimo-v2.5-pro，模型用对象格式而非字符串数组）
- 更新启动脚本（start/restart/debug 均含 OPENCLAW_STATE_DIR）
- 更新相关文件路径（openclaw 入口改为 openclaw.mjs）

**v1.2.0** (2026-05-16)
- 新增坑6-8：Node版本不够、gateway.token废弃、gateway.mode必填
- 新增 NVIDIA NIM 配置模板（Mistral Large 3 675B）
- 新增全E盘安装方案

**v1.1.0** (2026-05-10)
- 新增 bat 文件常见错误及修法
- 完善排障检查清单

**v1.0.0** (2026-05-03)
- 初始版本
