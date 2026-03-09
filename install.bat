@echo off
title CD Scanner - Cai dat moi truong
echo ============================================
echo   CD Scanner - Cai Dat Thu Vien
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python. Hay cai Python 3.10+ tu python.org
    pause
    exit /b 1
)

echo [1/3] Tao moi truong ao (venv)...
python -m venv venv
if errorlevel 1 (
    echo [LOI] Khong tao duoc venv.
    pause
    exit /b 1
)

echo [2/3] Kich hoat venv va cai dat thu vien...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [LOI] Cai dat that bai.
    pause
    exit /b 1
)

echo [3/3] Hoan tat!
echo.
echo  - Chay thu: run_dev.bat
echo  - Dong goi EXE: build_exe.bat
echo.
pause
