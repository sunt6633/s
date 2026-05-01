@echo off
chcp 65001 >nul 2>&1
title MoonTV - 影视聚合播放器
echo ========================================
echo   MoonTV 影视聚合播放器
echo   正在启动服务...
echo ========================================
echo.

cd /d D:\moontv\src

:: 设置环境变量（账号密码）
set USERNAME=admin
set PASSWORD=moontv2026
set SITE_NAME=MoonTV
set NEXT_PUBLIC_ENABLE_REGISTER=false

:: 检查是否已有实例在运行
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo [!] MoonTV 已经在运行中!
    echo    访问地址: http://localhost:3000
    echo.
    echo 按任意键打开浏览器...
    pause >nul
    start http://localhost:3000
    exit
)

:: 启动服务（后台运行）
echo [*] 正在启动 Node.js 服务...
:: 确保静态资源存在（standalone 构建不会自动复制这些目录）
if not exist ".next\standalone\.next\static" (
    echo [*] 复制静态资源...
    xcopy /E /I /Q ".next\static" ".next\standalone\.next\static" >nul 2>&1
)
if not exist ".next\standalone\public\icons" (
    echo [*] 复制 public 资源...
    xcopy /E /I /Q "public" ".next\standalone\public" >nul 2>&1
)

:: 启动服务（后台运行）
start /b node .next\standalone\server.js > nul 2>&1

:: 等待启动
echo [*] 等待服务就绪...
timeout /t 5 /nobreak >nul

:: 验证启动结果
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo.
    echo [✓] MoonTV 启动成功!
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
