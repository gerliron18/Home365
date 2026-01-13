@echo off
REM Database Inspection Tool - Quick Launcher
REM ==========================================

cd /d "%~dp0"

echo ======================================================================
echo Database Inspection Tool
echo ======================================================================
echo.

py scripts\inspect_database.py

pause
