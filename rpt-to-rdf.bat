@echo off
REM RPT-to-RDF Converter - Windows Batch Wrapper
REM Converts Crystal Reports 14 (.rpt) to Oracle Reports 12c (.rdf)
REM
REM Usage:
REM   rpt-to-rdf.bat convert <input> <output> [options]
REM   rpt-to-rdf.bat analyze <input> [options]
REM   rpt-to-rdf.bat check-config
REM   rpt-to-rdf.bat --help

setlocal EnableDelayedExpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check for virtual environment
if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
) else if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
)

REM Try python3 first, then python
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    python3 -m src.main %*
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        python -m src.main %*
    ) else (
        echo Error: Python not found. Please install Python 3.9+
        exit /b 1
    )
)

endlocal
