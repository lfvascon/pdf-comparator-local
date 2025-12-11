#!/bin/bash
# Build script for PDF Comparator executable
# This script builds a standalone executable using PyInstaller

set -e

echo "========================================"
echo "PDF Comparator - Build Script"
echo "========================================"
echo ""

# Check if pyinstaller is installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller no está instalado."
    echo "Instalando PyInstaller..."
    uv pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[ERROR] No se pudo instalar PyInstaller."
        echo "Intenta manualmente: uv pip install pyinstaller"
        exit 1
    fi
fi

echo ""
echo "Limpiando builds anteriores..."
rm -rf build dist __pycache__

echo ""
echo "Compilando ejecutable..."
echo "Esto puede tardar varios minutos..."
echo ""

pyinstaller PDFComparator.spec --clean

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] La compilación falló."
    echo "Revisa los mensajes de error arriba."
    exit 1
fi

echo ""
echo "========================================"
echo "Compilación completada exitosamente!"
echo "========================================"
echo ""
echo "El ejecutable se encuentra en: dist/PDFComparator"
echo ""
echo "Tamaño aproximado del ejecutable:"
ls -lh dist/PDFComparator
echo ""

