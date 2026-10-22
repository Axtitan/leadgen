@echo off
rem Starts LeadFinder and opens it in your browser. Keep this window open while you use it.
cd /d "%~dp0"
start "" http://127.0.0.1:8790
python -X utf8 app.py
pause
