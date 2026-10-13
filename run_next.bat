@echo off
title Remi Cekih Next.js - Board Pos Ronda
chcp 65001 >nul
echo =======================================================
echo 🃏 MENJALANKAN GAME REMI CEKIH EDISI POS RONDA (NEXT.JS)
echo 1. Menjalankan Python API Server di background (Port 8000)...
echo 2. Menjalankan Next.js Frontend (Port 3000)...
echo =======================================================

start "Python API Server (Port 8000)" /min cmd /c "python server.py 8000"

timeout /t 2 /nobreak >nul

start http://localhost:3000

cd frontend
npm run dev
pause
