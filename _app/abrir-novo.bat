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

rem Interface: compila so quando o codigo mudou. Sem Node.js o motor abre e mostra como compilar.
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Aviso: Node.js nao encontrado. Instale em https://nodejs.org para compilar a interface.
  echo.
) else (
  pushd "%~dp0frontend"
  rem instala dependencias quando o package-lock muda e compila quando o codigo muda
  call node scripts\build-se-preciso.mjs || echo Falha ao preparar a interface.
  popd
)

".venv\Scripts\python.exe" -m estudos %*

echo.
echo O servidor foi encerrado. Pode fechar esta janela.
pause
