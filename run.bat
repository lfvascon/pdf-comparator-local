@echo off
REM Quick run script for Windows using uv
if not exist .venv (
    echo ERROR: Entorno virtual no encontrado
    echo Por favor ejecuta install.bat primero
    pause
    exit /b 1
)

.venv\Scripts\activate.bat
python menu_principal.py

