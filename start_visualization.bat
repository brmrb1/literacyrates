@echo off
echo Starting Abstract Geometric Art Visualization...
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first to create the environment.
    pause
    exit /b 1
)

REM Check if geometric data exists
if not exist "geometric_data.json" (
    echo Processing literacy data...
    ".venv\Scripts\python.exe" geometric_processor.py
    if errorlevel 1 (
        echo Error: Failed to process data!
        pause
        exit /b 1
    )
)

echo Launching Geometric Art Visualization...
echo.
echo Controls:
echo   ESC - Exit
echo   SPACE - Pause/Resume
echo   S - Save Screenshot
echo   H - Toggle Info Panel
echo   Click - Select Entity
echo   Mouse - Attract Entities
echo.

REM Launch the visualization
".venv\Scripts\python.exe" geometric_art.py

echo.
echo Visualization closed.
pause