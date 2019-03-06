@echo off
::This script verifies the other scripts worked fine
python -V 2>nul
if not errorlevel 1 goto pythonOK :: this means errorlevel is less than 1
set /p a=Error: Python is not installed correctly (or not in PATH).
goto :EOF
:pythonOK
python "%~dp0files/moveAll.py" 0>nul
if not errorlevel 1 goto folderOK 
set /p a=Error: 'watch' folder already exists in python site-packages
goto :EOF
:folderOK
call watch -s
if not errorlevel 1 goto scriptsOK 
set /p a=
:: possible error: the python scripts folder is not installed correctly (or not in PATH).
goto :EOF
:scriptsOK
set /p a=installation completed