@echo off
cd /d "%~dp0"
where py >nul 2>&1 || (echo Instale Python 3.11 ou 3.12 com o launcher py. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe py -m venv .venv
if errorlevel 1 goto erro
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto erro
exit /b 0
:erro
echo Erro na instalacao ou execucao. Confira a conexao e a versao do Python.
pause
