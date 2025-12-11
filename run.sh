#!/bin/bash
# Quick run script for Linux/macOS using uv

if [ ! -d ".venv" ]; then
    echo "ERROR: Entorno virtual no encontrado"
    echo "Por favor ejecuta install.sh primero"
    exit 1
fi

source .venv/bin/activate
python menu_principal.py

