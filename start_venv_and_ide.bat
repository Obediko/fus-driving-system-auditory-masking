@echo off
setlocal

REM Define environment variables
set "DEFAULT_MODE=default"
set "MODE=%~3"
if "%MODE%"=="" set "MODE=%DEFAULT_MODE%"

if "%MODE%" == "DCCN" (
	set "DEFAULT_VENV_PATH=D:\Users\%USERNAME%\venv310"
) else (
	set "DEFAULT_VENV_PATH=%USERPROFILE%\Envs\FUS_DS_PACKAGE"
)

set "DEFAULT_IDE=spyder"

set "VENV_PATH=%~1"
if "%VENV_PATH%"=="" set "VENV_PATH=%DEFAULT_VENV_PATH%"

set "IDE=%~2"
if "%IDE%"=="" set "IDE=%DEFAULT_IDE%"

REM Activate the virtual environment and launch the IDE
call "%VENV_PATH%\Scripts\activate"
start "" "%IDE%"

endlocal