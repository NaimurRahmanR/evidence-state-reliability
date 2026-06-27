@echo off
echo Running all Evidence-State Reliability pilot workflows...
echo.

echo ==========================================
echo Running Pilot 01
echo ==========================================
call .\run_pilot_01.bat
if errorlevel 1 (
    echo Pilot 01 workflow failed.
    exit /b 1
)

echo.
echo ==========================================
echo Running Pilot 02
echo ==========================================
call .\run_pilot_02.bat
if errorlevel 1 (
    echo Pilot 02 workflow failed.
    exit /b 1
)

echo.
echo ==========================================
echo All pilot workflows completed successfully.
echo ==========================================