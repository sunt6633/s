@echo off
chcp 65001 >nul 2>&1
title SunTV 自动更新
echo ========================================
echo   SunTV 自动更新工具
echo ========================================
echo.

:: 配置区（按需修改）
set MOONTV_DIR=D:\moontv
set GITHUB_REPO=Wonderland2024/MoonTV

:: 检查 MoonTV 是否在运行
curl -s -o nul http://localhost:3000/login 2>nul
if %errorlevel%==0 (
    echo [!] 检测到 SunTV 正在运行，正在停止...
    call "%MOONTV_DIR%\停止MoonTV.bat"
    timeout /t 3 /nobreak >nul
)

echo [*] 开始更新 MoonTV...
echo.

cd /d "%MOONTV_DIR%"

:: 备份当前配置文件
if exist "src\.npmrc" (
    echo [*] 备份配置文件...
    copy "src\.npmrc" ".npmrc.bak" >nul 2>&1
)
if exist "src\tsconfig.json" (
    copy "src\tsconfig.json" "tsconfig.json.bak" >nul 2>&1
)
if exist "src\package.json.new" (
    copy "src\package.json.new" "package.json.new.bak" >nul 2>&1
)

:: 备份 standalone 构建产物
if exist "src\.next\standalone" (
    echo [*] 备份旧版构建产物...
    if exist "backup\standalone" rd /s /q "backup\standalone" >nul 2>&1
    mkdir backup 2>nul
    xcopy /E /I /Q "src\.next\standalone" "backup\standalone" >nul 2>&1
)

:: 拉取最新代码（使用 GitHub 镜像加速）
echo.
echo [*] 正在从 GitHub 拉取最新代码...
echo.

:: 尝试多种镜像源
set UPDATE_SUCCESS=0

:: 方法1：直接 git pull（如果 src 是独立仓库）
if exist "src\.git" (
    cd src
    git pull origin master 2>nul
    if !errorlevel!==0 set UPDATE_SUCCESS=1
    cd ..
)

:: 方法2：重新 clone 到临时目录再覆盖
if !UPDATE_SUCCESS!==0 (
    echo [*] 使用完整克隆方式更新...

    :: 清理旧临时目录
    if exist "src_new" rd /s /q "src_new" >nul 2>&1

    :: 尝试 GitHub 直连
    git clone --depth 1 https://github.com/%GITHUB_REPO%.git src_new 2>nul
    if errorlevel 1 (
        echo [*] GitHub 直连失败，尝试加速镜像...
        :: 尝试 ghproxy 加速
        git clone --depth 1 https://ghproxy.com/https://github.com/%GITHUB_REPO%.git src_new 2>nul
        if errorlevel 1 (
            :: 尝试 gitclone 镜像
            git clone --depth 1 https://gitclone.com/github.com/%GITHUB_REPO%.git src_new 2>nul
        )
    )

    if exist "src_new\node_modules" (
        set UPDATE_SUCCESS=2
    )
)

if !UPDATE_SUCCESS!==0 (
    echo.
    echo [✗] 更新失败！请检查网络连接或手动下载：
    echo     https://github.com/%GITHUB_REPO%/releases
    goto :rollback
)

:: 如果用了方法2（新克隆），替换源码目录
if !UPDATE_SUCCESS!==2 (
    echo.
    echo [*] 替换源码目录...
    if exist "src_backup" rd /s /q "src_backup" >nul 2>&1
    move src src_backup >nul 2>&1
    move src_new src >nul 2>&1
)

:: 恢复配置文件
echo [*] 恢复配置文件...
if exist ".npmrc.bak" (
    copy ".npmrc.bak" "src\.npmrc" >nul 2>&1
    del ".npmrc.bak" >nul 2>&1
) else (
    :: 写入 Windows 兼容配置
    echo node-linker=hoisted> "src\.npmrc"
    echo symlink=false>> "src\.npmrc"
)

:: 安装依赖 & 构建
echo.
echo ========================================
echo   安装依赖并构建中...（可能需要几分钟）
echo ========================================
echo.

cd src

:: pnpm install
call pnpm install 2>&1 | findstr /V "warn deprecated"
if errorlevel 1 (
    echo [✗] 依赖安装失败
    goto :rollback
)

:: 构建
call pnpm run build 2>&1 | findstr /V "warn deprecated"
if errorlevel 1 (
    echo [✗] 构建失败
    goto :rollback
)

cd ..

:: 复制静态资源到 standalone
echo [*] 准备运行环境...
xcopy /E /I /Q "src\.next\static" "src\.next\standalone\.next\static" >nul 2>&1
xcopy /E /I /Q "src\public" "src\.next\standalone\public" >nul 2>&1

:: 清理备份
echo [*] 更新完成！清理备份...
if exist "src_backup" rd /s /q "src_backup" >nul 2>&1
if exist "backup" rd /s /q "backup" >nul 2>&1
del *.bak 2>nul

:: 显示版本信息
echo.
echo ========================================
echo   ✅ SunTV 更新成功！
echo ========================================
for %%f in (src\VERSION.txt) do type "%%f" 2>nul
echo.

:: 启动服务
echo [*] 是否立即启动 SunTV？
choice /C YN /M "启动(Y/N)"
if errorlevel 2 goto :end
if errorlevel 1 (
    start "" "%MOONTV_DIR%\启动MoonTV.bat"
    echo 已启动！
)
goto :end

:rollback
echo.
echo [!] 正在回滚到之前版本...
if exist "src_backup" (
    if exist "src" rd /s /q "src" >nul 2>&1
    move src_backup src >nul 2>&1
    echo 已回滚。
) else if exist "backup\standalone" (
    xcopy /E /I /Q "backup\standalone" "src\.next\standalone" >nul 2>&1
    echo 已恢复构建产物。
) else (
    echo [!] 无备份可回滚，请手动处理。
)

:end
pause
