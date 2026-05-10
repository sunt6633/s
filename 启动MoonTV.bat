@echo off
chcp 65001 >nul 2>&1
title SunTV 启动器
echo ===================
echo   SunTV 影视聚合播放器
echo   正在启动服务...
echo ===================
echo.

cd /d D:\moontv\src

:: 设置环境变量
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

:: 确保静态资源存在
if not exist ".next\standalone\.next\static" (
    echo [*] 复制静态资源...
    xcopy /E /I /Q ".next\static" ".next\standalone\.next\static" >nul 2>&1
)
if not exist ".next\standalone\public\icons" (
    echo [*] 复制 public 资源...
    xcopy /E /I /Q "public" ".next\standalone\public" >nul 2>&1
)

:: 启动服务（通过 VBS 隐藏窗口运行，关闭此窗口不影响服务）
echo [*] 正在启动服务（后台模式）...
wscript "..\run_suntv.vbs" >nul 2>&1

:: 等待启动
echo [*] 等待服务就绪...
timeout /t 5 /nobreak >nul

:: 验证启动结果
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo.
    echo [√] SunTV 启动成功!
    echo    访问地址: http://localhost:3000
    echo    登录账号: admin
    echo    登录密码: moontv2026
    echo.
    echo [√] 此窗口可安全关闭，服务在后台运行中
    echo.
    echo 按任意键打开浏览器...
    pause >nul
    start http://localhost:3000
) else (
    echo.
    echo [X] 启动失败，请检查错误日志
    pause
)
