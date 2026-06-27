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
echo Step 2: Analysing pilot condition-level results
python -m experiments.analyse_pilot_01
if errorlevel 1 (
    echo Pilot condition-level analysis failed.
    exit /b 1
)

echo.
echo Step 3: Analysing reliability-failure relationships
python -m experiments.analyse_reliability_failure_relationship
if errorlevel 1 (
    echo Pilot reliability-failure relationship analysis failed.
    exit /b 1
)

echo.
echo Step 4: Running relationship sensitivity analysis
python -m experiments.analyse_relationship_sensitivity
if errorlevel 1 (
    echo Pilot relationship sensitivity analysis failed.
    exit /b 1
)

echo.
echo Step 5: Creating pilot plots
python -m experiments.plot_pilot_01
if errorlevel 1 (
    echo Pilot plotting failed.
    exit /b 1
)

echo.
echo Pilot 01 workflow completed successfully.