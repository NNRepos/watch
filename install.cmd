@echo off
python -V
if errorlevel 1 goto noPython
pip -V
if errorlevel 1 goto noPip
goto success
:noPython
echo Error: No python 2 installed.
goto end
:noPip
echo Error: No pip installed.
goto end
:success
pip install -r "%~dp0requirements.txt"
python "%~dp0watch.py" -s
goto eof
:end
set /p a=