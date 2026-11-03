@echo off
rem Fizgig Japanese add-on: uninstall
chcp 65001 >nul 2>&1
title Fizgig Japanese add-on - uninstall
set "FIZGIG_DIR=%~dp0.."
if not "%~1"=="" set "FIZGIG_DIR=%~1"
if not exist "%FIZGIG_DIR%\venv\Scripts\python.exe" goto :NOVENV
"%FIZGIG_DIR%\venv\Scripts\python.exe" -X utf8 "%~dp0tools\install.py" --remove
if errorlevel 1 goto :FAIL
echo.
echo Removed. Fizgig now starts in English.
pause
exit /b 0

:NOVENV
echo [ERROR] venv not found: "%FIZGIG_DIR%\venv"
echo Put this folder inside the Fizgig folder, or run: uninstall_ja.bat "path\to\Fizgig"
pause
exit /b 1

:FAIL
echo.
echo [FAILED] See the messages above.
pause
exit /b 1
