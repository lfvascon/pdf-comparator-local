@echo off
REM Build script for PDF Comparator executable
REM This script builds a standalone .exe file using PyInstaller

echo ========================================
echo PDF Comparator - Build Script
echo ========================================
echo.

REM Check if pyinstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado.
    echo Instalando PyInstaller...
    uv pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar PyInstaller.
        echo Intenta manualmente: uv pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo Compilando ejecutable...
echo Esto puede tardar varios minutos...
echo.

pyinstaller PDFComparator.spec --clean

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo.
    echo Revisa los mensajes de error arriba.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Compilacion completada exitosamente!
echo ========================================
echo.
echo El ejecutable se encuentra en: dist\PDFComparator.exe
echo.
echo Tamanio aproximado del ejecutable: 
dir dist\PDFComparator.exe | find "PDFComparator.exe"
echo.
pause

