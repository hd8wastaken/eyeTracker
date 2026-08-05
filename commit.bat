@echo off
cd /d "%~dp0"

set /p msg="commit message: "

if "%msg%"=="" (
    echo commit message cannot be empty
    pause
    exit /b 1
)

git add .
git commit -m "%msg%"

if %ERRORLEVEL% NEQ 0 (
    echo commit failed, nothing pushed
    pause
    exit /b 1
)

git push

if %ERRORLEVEL% NEQ 0 (
    echo push failed
    pause
    exit /b 1
)

echo done
pause