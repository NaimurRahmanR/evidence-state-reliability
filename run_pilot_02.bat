@echo off
echo Running Pilot 02 workflow...
echo.

echo Step 1: Running graded degradation sanity check
python -m experiments.sanity_check_graded_degradation
if errorlevel 1 (
    echo Pilot 02 graded degradation sanity check failed.
    exit /b 1
)

echo.
echo Step 2: Running Pilot 02 severity experiment
python -m experiments.run_pilot_02
if errorlevel 1 (
    echo Pilot 02 run failed.
    exit /b 1
)

echo.
echo Step 3: Analysing Pilot 02 severity results
python -m experiments.analyse_pilot_02
if errorlevel 1 (
    echo Pilot 02 analysis failed.
    exit /b 1
)

echo.
echo Pilot 02 workflow completed successfully.