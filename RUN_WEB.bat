@echo off
echo ======================================================================
echo Starting Property Management Chatbot - Web Interface
echo ======================================================================
echo.
echo Opening browser to http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
streamlit run app.py
pause
