@echo off
chcp 65001 >nul
title 添加视频素材
cd /d "%~dp0"

echo ================================
echo   猫耳女友桌宠 - 添加视频素材
echo ================================
echo.

:: 检查依赖
py -c "import cv2, rembg, scipy" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    py -m pip install opencv-python Pillow scipy rembg -q
)

echo 支持的状态名称：
echo   idle      - 待机.mp4
echo   work      - 工作中.mp4
echo   exhausted - 力竭了.mp4
echo   greet     - 打招呼.mp4
echo   cute      - 卖萌.mp4
echo   shy       - 害羞.mp4
echo   yawn      - 哈欠.mp4
echo   confused  - 懵圈.mp4
echo   sad       - 委屈屈.mp4
echo   miss      - 想你.mp4
echo   slacking  - 摸鱼.mp4
echo.
echo 请将视频文件放入 videos 目录
echo 文件名需与状态对应的中文名称一致（如 工作中.mp4, 打招呼.mp4）
echo.

set /p state=请输入状态名称:
set "video="
if /I "%state%"=="idle" set "video=videos\待机.mp4"
if /I "%state%"=="work" set "video=videos\工作中.mp4"
if /I "%state%"=="exhausted" set "video=videos\力竭了.mp4"
if /I "%state%"=="greet" set "video=videos\打招呼.mp4"
if /I "%state%"=="cute" set "video=videos\卖萌.mp4"
if /I "%state%"=="shy" set "video=videos\害羞.mp4"
if /I "%state%"=="yawn" set "video=videos\哈欠.mp4"
if /I "%state%"=="confused" set "video=videos\懵圈.mp4"
if /I "%state%"=="sad" set "video=videos\委屈屈.mp4"
if /I "%state%"=="miss" set "video=videos\想你.mp4"
if /I "%state%"=="slacking" set "video=videos\摸鱼.mp4"

if not defined video (
    echo [错误] 不支持的状态名称：%state%
    pause
    exit /b 1
)

if not exist "%video%" (
    echo [错误] 找不到 %video%
    pause
    exit /b 1
)

echo.
echo 正在抽取 %video%...
py extract_all.py %state%
if errorlevel 1 (
    echo [错误] 视频抽帧失败
    pause
    exit /b 1
)

echo 正在处理 %video%...
py rembg_proper.py %state%
if errorlevel 1 (
    echo [错误] rembg 处理失败
    pause
    exit /b 1
)

py fix_edges.py %state%
if errorlevel 1 (
    echo [错误] 边缘修复失败
    pause
    exit /b 1
)

echo.
echo [完成] 已添加 %state% 状态
echo 请重启桌宠生效
pause
