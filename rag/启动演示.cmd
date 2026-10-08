@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please install the virtual environment first. See README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app_qa.py --server.address 127.0.0.1
pause
