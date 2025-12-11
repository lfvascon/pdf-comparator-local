#!/bin/bash
# Installation script for Linux/macOS using uv

echo "========================================"
echo "PDF Comparator - Installation (uv)"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "[1/5] uv no está instalado. Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo instalar uv"
        echo "Por favor instala uv manualmente desde https://github.com/astral-sh/uv"
        exit 1
    fi
    echo "uv instalado correctamente."
    echo "Por favor reinicia la terminal y ejecuta este script nuevamente."
    echo "O ejecuta: source $HOME/.cargo/env"
    exit 0
else
    echo "[1/5] uv detectado"
    uv --version
fi

echo ""
echo "[2/5] Creando entorno virtual con uv..."
uv venv
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual"
    exit 1
fi

echo ""
echo "[3/5] Instalando dependencias con uv..."
uv pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias"
    exit 1
fi

echo ""
echo "[4/5] Sincronizando entorno..."
uv pip sync requirements.txt 2>/dev/null || echo "Info: No hay uv.lock (esto es normal)"

echo ""
echo "[5/5] Verificando instalación..."
.venv/bin/python3 -c "import fitz; import cv2; import PIL; print('✓ Todas las dependencias instaladas correctamente')"
if [ $? -ne 0 ]; then
    echo "ERROR: Algunas dependencias no se instalaron correctamente"
    exit 1
fi

echo ""
echo "========================================"
echo "Instalación completada exitosamente!"
echo "========================================"
echo ""
echo "Para ejecutar la aplicación:"
echo "  1. Activa el entorno virtual: source .venv/bin/activate"
echo "  2. Ejecuta: python menu_principal.py"
echo ""
echo "O usa el script run.sh"
echo ""

