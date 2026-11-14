@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>&1
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
    if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -c "import cv2, numpy; from PySide6 import QtWidgets" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias na pasta do projeto. A primeira vez precisa de internet.
    ".venv\Scripts\python.exe" -m pip install -r requirements-app.txt
    if errorlevel 1 goto erro
)
start "Vaga" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0aplicativo.py"
exit /b 0
:erro
echo Nao foi possivel preparar o aplicativo.
echo Confira se o Python 3.10 ou mais recente esta instalado e consulte o README.
pause
exit /b 1
