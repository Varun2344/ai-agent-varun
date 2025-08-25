@echo off
ECHO Starting the AI Competitor Monitor Agent...

REM Change directory to the script's location
cd /d "%~dp0"

ECHO Activating virtual environment and running the monitor...
REM Run the monitor script using the venv python and save the log
".\.venv\Scripts\python.exe" monitor.py --model phi3 > last_run_log.txt 2>&1

ECHO Agent run finished.