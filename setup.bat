@echo off
echo Setting up Abstract Geometric Art Environment...
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment!
        echo Please ensure Python is installed and available in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install packages
echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install pandas numpy pygame

if errorlevel 1 (
    echo Error: Failed to install packages!
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo You can now run start_visualization.bat to launch the art.
echo.
pause