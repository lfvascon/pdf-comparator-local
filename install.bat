@echo off
REM Installation script for Windows using uv
echo ========================================
echo PDF Comparator - Installation (uv)
echo ========================================
echo.

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo [1/5] uv no esta instalado. Instalando uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo ERROR: No se pudo instalar uv
        echo Por favor instala uv manualmente desde https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
    echo uv instalado correctamente.
    echo Por favor reinicia la terminal y ejecuta este script nuevamente.
    pause
    exit /b 0
) else (
    echo [1/5] uv detectado
    uv --version
)

echo.
echo [2/5] Creando entorno virtual con uv...
uv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo.
echo [3/5] Instalando dependencias con uv...
uv pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [4/5] Sincronizando entorno...
uv pip sync requirements.txt
if errorlevel 1 (
    echo Advertencia: No se pudo sincronizar (esto es normal si no hay uv.lock)
)

echo.
echo [5/5] Verificando instalacion...
.venv\Scripts\python.exe -c "import fitz; import cv2; import PIL; print('✓ Todas las dependencias instaladas correctamente')"
if errorlevel 1 (
    echo ERROR: Algunas dependencias no se instalaron correctamente
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalacion completada exitosamente!
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   1. Activa el entorno virtual: .venv\Scripts\activate
echo   2. Ejecuta: python menu_principal.py
echo.
echo O usa el script run.bat
echo.
pause

