@echo off
echo Running Pilot 01 workflow...
echo.

echo Step 1: Running simulation pilot
python -m experiments.run_pilot_01
if errorlevel 1 (
    echo Pilot run failed.
    exit /b 1
)

echo.
echo Step 2: Analysing pilot results
python -m experiments.analyse_pilot_01
if errorlevel 1 (
    echo Pilot analysis failed.
    exit /b 1
)

echo.
echo Step 3: Creating pilot plots
python -m experiments.plot_pilot_01
if errorlevel 1 (
    echo Pilot plotting failed.
    exit /b 1
)

echo.
echo Pilot 01 workflow completed successfully.