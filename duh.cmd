@echo off
REM Find Python executable - try multiple common locations
set PYTHON_EXE=
for %%p in (
    "%LOCALAPPDATA%\Python\bin\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "python.exe"
) do (
    if exist "%%p" (
        set PYTHON_EXE=%%p
        goto :found_python
    )
)
:found_python
if "%PYTHON_EXE%"=="" (
    echo Error: Python not found. Please install Python and ensure it's in PATH.
    pause
    exit /b 1
)
"%PYTHON_EXE%" "%~dp0duh.py" %*
