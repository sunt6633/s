@echo off
chcp 65001 >nul 2>&1
title 停止 MoonTV
echo ========================================
echo   停止 MoonTV 服务
echo ========================================
echo.

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo [*] 找到进程 PID: %%a
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel!==0 (
        echo [✓] 已成功终止进程
    ) else (
        echo [✗] 终止失败，可能需要手动关闭
    )
)

timeout /t 2 /nobreak >nul
curl -s -o nul http://localhost:3000/login 2>nul
if not %errorlevel%==0 (
    echo.
    echo [✓] MoonTV 已停止运行
) else (
    echo.
    echo [!] 服务仍在运行，请检查是否有其他程序占用3000端口
)
pause
