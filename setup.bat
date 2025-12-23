@echo off
REM RPT-to-RDF Converter - Windows Setup Script
REM Creates virtual environment and installs dependencies

setlocal EnableDelayedExpansion

echo ================================
echo   RPT-to-RDF Setup
echo ================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check for Python
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python3"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON=python"
    ) else (
        echo Error: Python not found. Please install Python 3.9+
        exit /b 1
    )
)

for /f "tokens=2" %%i in ('%PYTHON% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [+] Found Python: %PYTHON_VERSION%

REM Create virtual environment
if exist "venv" (
    echo [*] Virtual environment already exists
) else (
    echo [*] Creating virtual environment...
    %PYTHON% -m venv venv
    echo [+] Virtual environment created
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [*] Upgrading pip...
pip install --upgrade pip -q

REM Install dependencies
echo [*] Installing dependencies...
pip install -r requirements.txt -q

echo [+] Dependencies installed

REM Create directories
echo [*] Creating directories...
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

echo.
echo ================================
echo   Setup Complete!
echo ================================
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate.bat
echo.
echo To run the converter:
echo   rpt-to-rdf.bat --help
echo   rpt-to-rdf.bat check-config
echo   rpt-to-rdf.bat convert .\input .\output --mock
echo.
echo To deactivate the virtual environment:
echo   deactivate
echo.

endlocal
