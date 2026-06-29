@echo off
setlocal

echo ==========================================
echo Pilot 03 Dry-Run Reproducibility Workflow
echo ==========================================
echo.
echo This workflow does NOT call any real LLM.
echo It runs the local Pilot 03 dry-run scaffold only.
echo.

echo [1/4] Checking Pilot 03 Python files compile...
python -m py_compile src/pilot_03_tasks.py
if errorlevel 1 goto :error

python -m py_compile src/pilot_03_prompts.py
if errorlevel 1 goto :error

python -m py_compile src/pilot_03_dry_run.py
if errorlevel 1 goto :error

python -m py_compile src/pilot_03_llm_client.py
if errorlevel 1 goto :error

python -m py_compile src/pilot_03_logging.py
if errorlevel 1 goto :error

python -m py_compile src/pilot_03_parser.py
if errorlevel 1 goto :error

python -m py_compile experiments/pilot_03_dry_run_runner.py
if errorlevel 1 goto :error

python -m py_compile experiments/pilot_03_dry_run_analysis.py
if errorlevel 1 goto :error

python -m py_compile experiments/pilot_03_dry_run_plots.py
if errorlevel 1 goto :error

echo.
echo [2/4] Running Pilot 03 dry-run analysis...
python -m experiments.pilot_03_dry_run_analysis
if errorlevel 1 goto :error

echo.
echo [3/4] Generating Pilot 03 dry-run plots...
python -m experiments.pilot_03_dry_run_plots
if errorlevel 1 goto :error

echo.
echo [4/4] Pilot 03 dry-run workflow completed successfully.
echo.
echo Outputs should be in:
echo results\pilot_03_dry_run_analysis\pilot_03_dry_run_analysis_latest
echo.
echo Safe wording:
echo observed local dry-run result under current Pilot 03 experimental conditions
echo.
goto :end

:error
echo.
echo Pilot 03 dry-run workflow failed.
echo Please paste the full terminal output so we can debug step by step.
exit /b 1

:end
endlocal