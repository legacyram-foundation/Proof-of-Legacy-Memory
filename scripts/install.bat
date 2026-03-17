@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ████████████████████████████████████████████████████
echo  ██   PoLM — Proof of Legacy Memory   v1.2.0       ██
echo  ██   polm.com.br                                  ██
echo  ██   Windows Installer                            ██
echo  ████████████████████████████████████████████████████
echo.

:: ── Python check ─────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo  Install Python 3.9+ from:  https://www.python.org/downloads/
    echo  IMPORTANT: check "Add Python to PATH" during installation.
    echo.
    start https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [ok] Python %PYVER%

:: ── Virtual environment ──────────────────────────────────────────
if not exist venv (
    echo [..] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 ( echo [ERROR] venv failed & pause & exit /b 1 )
)
echo [ok] Virtual environment ready

:: ── Dependencies ────────────────────────────────────────────────
echo [..] Installing dependencies...
venv\Scripts\pip install --upgrade pip -q
venv\Scripts\pip install flask cryptography requests -q
if errorlevel 1 ( echo [ERROR] pip install failed & pause & exit /b 1 )
echo [ok] Dependencies installed

:: ── Detect RAM ──────────────────────────────────────────────────
echo [..] Detecting RAM type...
set RAM_TYPE=DDR4
for /f "skip=1 tokens=*" %%a in ('wmic memorychip get memorytype 2^>nul') do (
    set T=%%a & set T=!T: =!
    if "!T!"=="21" set RAM_TYPE=DDR2
    if "!T!"=="24" set RAM_TYPE=DDR3
    if "!T!"=="26" set RAM_TYPE=DDR4
    if "!T!"=="34" set RAM_TYPE=DDR5
)
echo [ok] RAM detected: %RAM_TYPE%

:: ── Generate wallet ─────────────────────────────────────────────
echo [..] Setting up wallet...
venv\Scripts\python -c "
import sys, os
sys.path.insert(0, '.')
dd = os.path.join(os.environ.get('APPDATA','~'), 'PoLM')
os.makedirs(dd, exist_ok=True)
wp = os.path.join(dd, 'wallet.json')
from polm_wallet import WalletFile
w = WalletFile(wp)
print(w.default())
" > "%TEMP%\polm_addr.txt" 2>nul
set /p ADDR=<"%TEMP%\polm_addr.txt"
if not defined ADDR set ADDR=POLM_ADDRESS
echo [ok] Address: %ADDR%

:: ── Create launcher scripts ─────────────────────────────────────
echo [..] Creating launchers...

> start_node.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo title PoLM Node
echo echo  PoLM Node v1.2.0 - polm.com.br
echo venv\Scripts\python polm.py node 6060
echo pause
)

> start_miner.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo title PoLM Miner
echo echo  Mining as: %ADDR%
echo venv\Scripts\python polm.py miner http://localhost:6060 %ADDR% %RAM_TYPE%
echo pause
)

> start_wallet.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo title PoLM Wallet
echo echo  Wallet UI: http://localhost:7070
echo timeout /t 2 /nobreak ^>nul
echo start "" http://localhost:7070
echo venv\Scripts\python polm_wallet.py ui http://localhost:6060 7070
echo pause
)

> start_explorer.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo title PoLM Explorer
echo echo  Explorer: http://localhost:5050
echo timeout /t 2 /nobreak ^>nul
echo start "" http://localhost:5050
echo venv\Scripts\python polm_explorer.py http://localhost:6060 5050
echo pause
)

> start_all.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo title PoLM
echo echo  Starting PoLM Network...
echo echo  polm.com.br
echo echo.
echo start "PoLM Node"     cmd /k "cd /d \"%~dp0\" && venv\Scripts\python polm.py node 6060"
echo timeout /t 5 /nobreak ^>nul
echo start "PoLM Miner"    cmd /k "cd /d \"%~dp0\" && venv\Scripts\python polm.py miner http://localhost:6060 %ADDR% %RAM_TYPE%"
echo timeout /t 3 /nobreak ^>nul
echo start "PoLM Wallet"   cmd /k "cd /d \"%~dp0\" && venv\Scripts\python polm_wallet.py ui http://localhost:6060 7070"
echo timeout /t 3 /nobreak ^>nul
echo start "PoLM Explorer" cmd /k "cd /d \"%~dp0\" && venv\Scripts\python polm_explorer.py http://localhost:6060 5050"
echo timeout /t 5 /nobreak ^>nul
echo start "" http://localhost:7070
echo echo.
echo echo  All services started!
echo echo  Wallet:   http://localhost:7070
echo echo  Explorer: http://localhost:5050
echo echo  Node API: http://localhost:6060
echo pause
)

> polm.bat (
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%~dp0"
echo venv\Scripts\python polm.py %%*
)

echo [ok] Launchers created

echo.
echo  ████████████████████████████████████████████████████
echo  ██  Installation complete!                        ██
echo  ████████████████████████████████████████████████████
echo.
echo  Your mining address:
echo  %ADDR%
echo.
echo  ─────────────────────────────────────────────────
echo  start_all.bat      ^> start everything
echo  start_node.bat     ^> full node only
echo  start_miner.bat    ^> miner only
echo  start_wallet.bat   ^> wallet UI
echo  start_explorer.bat ^> blockchain explorer
echo  ─────────────────────────────────────────────────
echo  Wallet:    http://localhost:7070
echo  Explorer:  http://localhost:5050
echo  Node API:  http://localhost:6060
echo  Website:   https://polm.com.br
echo  ─────────────────────────────────────────────────
echo.
pause
