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
echo Running Pilot 03 Dry-Run
echo ==========================================
call .\run_pilot_03.bat
if errorlevel 1 (
    echo Pilot 03 dry-run workflow failed.
    exit /b 1
)

echo.
echo ==========================================
echo All pilot workflows completed successfully.
echo ==========================================
echo.
echo Reliability wording:
echo Pilot 01 and Pilot 02 remain simulation-first.
echo Pilot 03 currently reports observed local dry-run results under current Pilot 03 experimental conditions.
echo No real LLM behaviour is claimed unless real LLM runs are explicitly completed.
echo.