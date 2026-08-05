@echo off
cd /d "%~dp0"

echo building docker image: tracker
docker build -t tracker -f dockerfile .

if %ERRORLEVEL% EQU 0 (
    echo build succeeded. run it with:
    echo   docker run --rm -it tracker
) else (
    echo build failed :(
)

pause