@echo off
title Controle Pessoal - Bot Telegram
cd /d "%~dp0"

echo Encerrando instancias anteriores...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo Iniciando sistema...
start "Bot Telegram" python -W ignore main.py

timeout /t 5 /nobreak >nul
echo.
echo Sistema iniciado!
echo API disponivel em: http://localhost:8000
echo Docs da API:        http://localhost:8000/docs
echo.
echo Pressione qualquer tecla para abrir o Swagger UI...
pause >nul
start http://localhost:8000/docs
