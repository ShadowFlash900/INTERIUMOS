@echo off
title Interium Launcher

cls

:menu
echo.
echo  #############################################
echo  #                                           #
echo  #            INTERIUM GRUB v1.1             #
echo  #                                           #
echo  #############################################
echo.
echo  [1] Normal launch
echo  [2] Debug mode launch
echo  [3] Exit
echo.

set /p choice="  Select mode (1-3): "

if "%choice%"=="1" goto normal
if "%choice%"=="2" goto debug
if "%choice%"=="3" exit /b
echo.
echo  [ERROR] Invalid choice! Please enter 1, 2 or 3
timeout /t 2 >nul
goto menu

:normal
cls
echo.
echo  #############################################
echo  #            MODE: NORMAL LAUNCH           #
echo  #############################################
echo.
goto launch

:debug
cls
echo.
echo  #############################################
echo  #            MODE: DEBUG LAUNCH             #
echo  #############################################
echo.
set DEBUG_MODE=1

:launch
if not exist "interium.py" (
    echo  [ERROR] interium.py file not found!
    echo  Please make sure it's in the same directory
    echo  as this bat file.
    echo.
    pause
    exit /b 1
)

if defined DEBUG_MODE (
    echo  [DEBUG] Launching with debug information...
    python -X dev interium.py
) else (
    echo  [INFO] Standard launch...
    python interium.py
)

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Launch failed with error code: %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo  [INFO] Interium has finished successfully
pause
quit
start launcher.bat