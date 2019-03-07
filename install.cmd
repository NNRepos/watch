@echo off
::This script verifies the other scripts worked fine
python -V 2>nul
if not errorlevel 1 goto pythonOK :: this means errorlevel is less than 1
set /p a=Error: Python is not installed correctly (or not in PATH).
goto :EOF

:pythonOK
python "%~dp0files\moveAll.py" 0>nul
if not errorlevel 1 goto folderOK 
pause
goto :EOF

:folderOK
set /p path_to_scripts=<"%~dp0files\folder.txt"
del "%~dp0files\folder.txt"
echo/%path%|find "%path_to_scripts%" >nul
if not errorlevel 1 goto scriptsOK
echo Adding python/scripts to path...
setx path "%path_to_scripts%;%path%" 1>nul 2>nul
if not errorlevel 1 goto setxOK
set /p a=Error: 'setx' was not successful. Try starting this file in administrator mode.
goto :EOF

:setxOK
set /p a= Added successfully. Please close this window and reinstall.
goto :EOF

:scriptsOK
call watch -sc
if not errorlevel 1 goto watchOK
set /p a=Error: Something went wrong ;/
goto :EOF

:watchOK
set /p a=installation completed