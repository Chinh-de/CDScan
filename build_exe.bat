@echo off
title CD Scanner - Dong goi EXE
echo ============================================
echo   CD Scanner - Dong Goi Thanh File EXE
echo ============================================
echo.

call venv\Scripts\activate
if errorlevel 1 (
    echo [LOI] Chua chay install.bat. Hay chay install.bat truoc.
    pause
    exit /b 1
)

echo Dang dong goi... (co the mat 1-3 phut)
echo.

REM Build with PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --noconsole ^
    --icon "static/cat_icon.ico" ^
    --name CDscaner ^
    --add-data "static;static" ^
    --add-data "UVDoc_grid.onnx;." ^
    --add-data "UVDoc_grid.onnx.data;." ^
    --add-data "credentials.json;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all onnxruntime ^
    --collect-all reportlab ^
    --collect-all tkinterdnd2 ^
    main_app.py

if errorlevel 1 (
    echo.
    echo [LOI] Dong goi that bai. Xem log o tren.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  THANH CONG!
echo  File EXE: dist\CDscaner.exe
echo  Chia se file nay cho nguoi dung, khong can
echo  cai Python hay thu vien gi them.
echo ============================================
echo.
pause
