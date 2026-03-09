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
    --name CDscaner ^
    --add-data "scanner_core.py;." ^
    --add-data "pdf_exporter.py;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinterdnd2" ^
    --hidden-import "reportlab" ^
    --hidden-import "cv2" ^
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
