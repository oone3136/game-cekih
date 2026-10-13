@echo off
title Remi Cekih Pos Ronda - Game Kartu 4 Pemain
chcp 65001 >nul
echo =======================================================
echo 🃏 REMI CEKIH EDISI POS RONDA (NEXT.JS BOARD EDITION)
echo =======================================================
echo.
echo [1] Jalankan Next.js UI Modern (Layout Sesuai Sketsa Meja + Popups) - REKOMENDASI
echo [2] Jalankan Versi Standalone Python Server (Port 8000)
echo.
set /p pilihan="Pilih versi (tekan Enter untuk pilihan [1]): "
if "%pilihan%"=="2" goto python_server
goto nextjs_server

:nextjs_server
echo.
echo Menjalankan Python Backend API (Port 8000)...
start "Python API Server (Port 8000)" /min cmd /c "python server.py 8000"
timeout /t 2 /nobreak >nul
echo Menjalankan Next.js Frontend (Port 3000)...
start http://localhost:3000
cd frontend
npm run dev
goto end

:python_server
echo.
echo Menjalankan Standalone Python Server di http://localhost:8000 ...
start http://localhost:8000
python server.py 8000
goto end

:end
pause
