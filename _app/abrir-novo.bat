@echo off
chcp 65001 >nul
title Plataforma de Estudos - Motor novo
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente Python do motor novo...
  py -3.13 -m venv .venv || (
    echo.
    echo Nao encontrei o Python 3.13. Instale em https://www.python.org/downloads/
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install -q -e . || (
    echo Falha ao instalar as dependencias.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m estudos %*

echo.
echo O servidor foi encerrado. Pode fechar esta janela.
pause
