@echo off
chcp 65001 >nul
title Plataforma de Estudos - Desktop
cd /d "%~dp0Calculo 2\_app"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 servidor.py %*
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python servidor.py %*
  ) else (
    echo.
    echo Nao encontrei o Python nesta maquina.
    echo Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
    echo.
  )
)

echo.
echo O servidor foi encerrado. Pode fechar esta janela.
pause
