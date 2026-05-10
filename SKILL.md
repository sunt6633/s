---
name: moontv-deploy
description: "MoonTV 影视聚合播放器 Windows 本地部署。适用于用户需要在 Windows 上部署 MoonTV（Next.js 开源影视站）的场景，包括从 GitHub 克隆、依赖安装、构建、修复 Windows 兼容问题、启动服务，以及机顶盒（OrionTV）局域网配置。触发词：部署moontv、安装moontv、搭建moontv、MoonTV部署。"
version: "1.0.0"
author: "sunt111"
created: "2026-05-01"
tags: [moontv, nextjs, deployment, windows, 影视, 机顶盒]
---

# MoonTV Windows 本地部署 Skill

> 基于 `Wonderland2024/MoonTV` 项目（Next.js 14 + TypeScript），在 Windows 系统上一键完成从零到可用的完整部署流程。

## 前置条件

| 依赖 | 要求 |
|------|------|
| Node.js | >= 18.x（推荐 LTS 版本） |
| pnpm | 全局安装：`npm i -g pnpm` |
| Git | 用于克隆源码 |
| 操作系统 | Windows 10/11（本 skill 针对 Windows 优化） |

## 部署目录约定

默认部署到 `D:\moontv`，可根据需要修改。

## 完整部署步骤

### 第一步：克隆项目

```bash
git clone https://github.com/Wonderland2024/MoonTV.git D:\moontv\src
cd D:\moontv\src
```

如果 GitHub 访问慢，可用加速镜像：
```bash
# Gitee 镜像（如有）
git clone https://gitee.com/mirrors/MoonTV.git D:\moontv\src

# 或 ghproxy 加速
git clone https://ghproxy.com/https://github.com/Wonderland2024/MoonTV.git D:\moontv\src
```

### 第二步：修复 Windows pnpm 兼容性（关键！）

Windows 下 pnpm 默认使用 symlink 模式，会导致 `EPERM: operation not permitted, symlink` 错误。

**在 `D:\moontv\src\.npmrc` 中写入以下内容**：

```ini
node-linker=hoisted
symlink=false
```

### 第三步：安装依赖并构建

```bash
cd D:\moontv\src
pnpm install
pnpm run build
```

#### ⚠️ 构建时常见问题及修复

**问题 1：`EPERM: operation not permitted, symlink`**
- **原因**：pnpm 默认创建符号链接，Windows 权限不足
- **解决**：确保 `.npmrc` 已配置（见第二步）

**问题 2：TypeScript 类型错误 — `Cannot find type definition file for 'minimatch'`**
- **原因**：`@types/node` v24 与 TypeScript 4.9 不兼容
- **解决**：修改 `tsconfig.json`，在 `compilerOptions` 中添加：
```json
{
  "compilerOptions": {
    "types": ["node", "react", "react-dom"]
  }
}
```

**问题 3：构建白名单报错**
- **原因**：pnpm 对某些原生模块的构建策略
- **解决**：在 `package.json` 中添加：
```json
{
  "pnpm": {
    "onlyBuiltDependencies": ["esbuild", "sharp", "unrs-resolver", "workerd"]
  }
}
```
然后重新执行 `pnpm install && pnpm run build`

### 第四步：复制静态资源到 standalone 目录

Next.js 的 `standalone` 输出模式不会自动复制静态资源，必须手动复制：

```bash
cd D:\moontv\src

# 复制 .next/static 到 standalone 目录
cp -r .next/static .next/standalone/.next/static

# 复制 public 到 standalone 目录
cp -r public .next/standalone/public
```

> **如果不执行此步骤，页面会白屏或无法加载 CSS/JS/图片**

### 第五步：创建启动脚本

创建 `D:\moontv\启动MoonTV.bat`：

```batch
@echo off
chcp 65001 >nul 2>&1
title SunTV - 影视聚合播放器
echo ========================================
echo   SunTV 影视聚合播放器
echo   正在启动服务...
echo ========================================
echo.

cd /d D:\moontv\src

:: 设置环境变量（账号密码）
set USERNAME=admin
set PASSWORD=moontv2026
set SITE_NAME=SunTV
set NEXT_PUBLIC_ENABLE_REGISTER=false

:: 检查是否已有实例在运行
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo [!] SunTV 已经在运行中!
    echo    访问地址: http://localhost:3000
    echo.
    echo 按任意键打开浏览器...
    pause >nul
    start http://localhost:3000
    exit
)

:: 启动前确保静态资源存在
if not exist ".next\standalone\.next\static" (
    echo [*] 复制静态资源...
    xcopy /E /I /Q ".next\static" ".next\standalone\.next\static" >nul 2>&1
)
if not exist ".next\standalone\public\icons" (
    echo [*] 复制 public 资源...
    xcopy /E /I /Q "public" ".next\standalone\public" >nul 2>&1
)

:: 启动服务
start /b node .next\standalone\server.js > nul 2>&1

:: 等待启动
echo [*] 等待服务就绪...
timeout /t 5 /nobreak >nul

:: 验证
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo.
    echo [✓] SunTV 启动成功!
    echo    访问地址: http://localhost:3000
    echo    登录账号: admin
    echo    登录密码: moontv2026
    echo.
    echo 按任意键打开浏览器...
    pause >nul
    start http://localhost:3000
) else (
    echo.
    echo [✗] 启动失败，请检查错误日志
    pause
)
```

创建 `D:\moontv\停止SunTV.bat`：

```batch
@echo off
title 停止 SunTV
echo 正在停止 SunTV 服务...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo SunTV 已停止。
timeout /t 2 >nul
```

### 第六步：启动验证

双击 `启动MoonTV.bat` 或直接命令行运行：

```bash
cd D:\moontv\src
set USERNAME=admin
set PASSWORD=moontv2026
set SITE_NAME=SunTV
node .next/standalone/server.js
```

访问 `http://localhost:3000`，用 `admin` / `moontv2026` 登录。

---

## 机顶盒（OrionTV）局域网接入

### 原理

```
电脑（SunTV 后端 :3000）
    ↓ 局域网 WiFi/网线
机顶盒（OrionTV App → 配置后端地址）
    ↓ HDMI
电视屏幕
```

### 步骤

1. **下载 OrionTV APK**（Android TV 前端客户端）
   - GitHub: https://github.com/zimplexing/OrionTV/releases
   - 推荐 v1.3.13+ 版本
   - 用 U 盘拷贝到机顶盒安装

2. **配置后端地址**
   - 打开 OrionTV → 设置
   - Backend URL 填入：`http://<电脑IP>:3000`
   - 例如：`http://192.168.28.116:3000`

3. **用相同账号登录**

4. **添加防火墙规则**（如机顶盒无法连接）

以管理员身份运行 CMD：
```cmd
netsh advfirewall firewall add rule name="SunTV 3000" dir=in action=allow protocol=TCP localport=3000
```

### 注意事项

- **电脑必须开机且 SunTV 服务正在运行**，机顶盒才能使用
- 如需 24 小时可用，建议将 SunTV 部署到 NAS（Docker 方式）
- 局域网 IP 可能变动，建议给电脑设置固定 IP

---

## 封装为独立 EXE（可选）

使用 PyInstaller 可将 SunTV 打包为单个 EXE 文件：

```python
# suntv_launcher.py
import os, sys, subprocess, tempfile, shutil, socket, time, threading

PORT = int(os.environ.get('SUNTV_PORT', 3000))
USERNAME = os.environ.get('SUNTV_USERNAME', 'admin')
PASSWORD = os.environ.get('SUNTV_PASSWORD', 'moontv2026')

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getpeername()[0]
    s.close()
    return ip

def is_port_in_use(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', port))
        s.close()
        return False
    except:
        return True

def main():
    print("=== SunTV ===")
    if is_port_in_use(PORT):
        print(f"端口 {PORT} 已占用，可能已在运行")
        time.sleep(2)
        os.startfile(f'http://localhost:{PORT}')
        input("按 Enter 退出...")
        sys.exit(0)

    work_dir = tempfile.mkdtemp(prefix='suntv_')
    node_exe = os.path.join(work_dir, 'node.exe')
    standalone_dir = os.path.join(work_dir, 'standalone')

    # 从 PyInstaller _MEIPASS 解压资源
    src_node = os.path.join(sys._MEIPASS, 'node.exe') if hasattr(sys, '_MEIPASS') else './node.exe'
    src_stand = os.path.join(sys._MEIPASS, 'standalone') if hasattr(sys, '_MEIPASS') else './standalone'

    shutil.copy2(src_node, node_exe)
    shutil.copytree(src_stand, standalone_dir)

    env = os.environ.copy()
    env.update({'USERNAME': USERNAME, 'PASSWORD': PASSWORD,
                'SITE_NAME': 'SunTV', 'PORT': str(PORT),
                'HOSTNAME': '0.0.0.0', 'NODE_ENV': 'production'})

    def open_browser():
        time.sleep(3)
        try: os.startfile(f'http://localhost:{PORT}')
        except: pass
    threading.Thread(target=open_browser, daemon=True).start()

    proc = subprocess.Popen([node_exe, os.path.join(standalone_dir, 'server.js')],
                            cwd=standalone_dir, env=env)
    print(f"服务已启动 PID={proc.pid}")
    print(f"http://localhost:{PORT}  |  http://{get_local_ip()}:{PORT}")
    proc.wait()
try:
    main()
finally:
    shutil.rmtree(work_dir, ignore_errors=True)
```

打包命令：
```bash
pip install pyinstaller
pyinstaller suntv_launcher.py --onefile --name suntv \
  --add-data "node.exe;." \
  --add-data "standalone;standalone"
```

输出文件：`dist/suntv.exe`

---

## 故障排查速查表

| 症状 | 原因 | 解决方法 |
|------|------|----------|
| `EPERM: operation not permitted, symlink` | pnpm symlink 权限 | `.npmrc` 设 `node-linker=hoisted; symlink=false` |
| TypeScript 类型错误 minimatch | @types/node 版本不兼容 | tsconfig 添加 `compilerOptions.types` |
| 页面白屏无内容 | standalone 缺少静态资源 | 复制 `.next/static` 和 `public` 到 standalone 目录 |
| 安全合规配置警告 | 未设置 PASSWORD 环境变量 | 启动脚本中 `set PASSWORD=xxx` |
| 机顶盒无法连接 | 防火墙拦截 | 以管理员添加防火墙入站规则放行 3000 端口 |
| 端口被占用 | 上次没正常关闭 | 先运行停止脚本，或 `taskkill /PID <pid> /F` |

---

## 文件清单（部署完成后）

```
D:\moontv\
├── 启动SunTV.bat          # 双击启动
├── 停止SunTV.bat          # 双击停止
├── src/                   # MoonTV 源码
│   ├── .next/
│   │   └── standalone/    # 构建产物（含 server.js）
│   ├── public/            # 公共资源
│   ├── package.json
│   └── .npmrc             # pnpm Windows 兼容配置
└── README.md              # 本说明文档
```
