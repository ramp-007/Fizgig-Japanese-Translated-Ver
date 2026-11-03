@echo off
rem Fizgig Japanese add-on: install (safe to run repeatedly)
chcp 65001 >nul 2>&1
title Fizgig Japanese add-on - install
set "FIZGIG_DIR=%~dp0.."
if not "%~1"=="" set "FIZGIG_DIR=%~1"
if not exist "%FIZGIG_DIR%\venv\Scripts\python.exe" goto :NOVENV
"%FIZGIG_DIR%\venv\Scripts\python.exe" -X utf8 "%~dp0tools\install.py"
if errorlevel 1 goto :FAIL
echo.
echo Done. Start Fizgig as usual. See README.md for how to switch back to English.
pause
exit /b 0

:NOVENV
echo [ERROR] venv not found: "%FIZGIG_DIR%\venv"
echo Put this folder inside the Fizgig folder, or run: install_ja.bat "path\to\Fizgig"
pause
exit /b 1

:FAIL
echo.
echo [FAILED] See the messages above.
pause
exit /b 1
