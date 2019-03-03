@echo off
python -V
if errorlevel 1 goto noPython
goto success
:noPython
echo Error: No python 2 installed.
goto end
:success
python "%~dp0files/moveAll.py"
python "%~dp0watch.py" -s
goto eof
:end
set /p a= ::this will be removed