# 📄 Comparador de PDFs

Aplicación de escritorio para comparar documentos PDF y detectar diferencias visualmente, destacando cambios con colores (verde para nuevo contenido, magenta para contenido eliminado).

## ✨ Características

- 🔍 **Comparación de carpetas**: Procesa lotes de PDFs emparejando archivos automáticamente
- 📄 **Comparación individual**: Compara dos archivos PDF directamente
- 🎯 **Detección inteligente**: Empareja archivos por similitud de nombres
- 🖼️ **Alineación automática**: Alinea páginas con diferentes orientaciones o escalas
- ⚙️ **Configuración personalizable**: Ajusta calidad, sensibilidad y otros parámetros
- 💾 **Sin dependencias externas**: Usa PyMuPDF (librería Python pura) en lugar de Poppler

## 📋 Requisitos

- **Python 3.10 o superior**
- **uv** (se instala automáticamente si no está presente)
- **Sistema Operativo**: Windows, Linux o macOS

## 🚀 Instalación Rápida

### Windows

```bash
# 1. Clonar el repositorio
git clone https://github.com/lfvascon/pdf-comparator-local.git
cd pdf-comparator-local

# 2. Ejecutar script de instalación (instala uv automáticamente si es necesario)
install.bat

# 3. Ejecutar la aplicación
run.bat
```

### Linux/macOS

```bash
# 1. Clonar el repositorio
git clone https://github.com/lfvascon/pdf-comparator-local.git
cd pdf-comparator-local

# 2. Dar permisos de ejecución y ejecutar instalación
chmod +x install.sh run.sh
./install.sh

# 3. Ejecutar la aplicación
./run.sh
```

## 📖 Instalación Manual

Si prefieres instalar manualmente:

```bash
# 1. Instalar uv (si no lo tienes)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Crear entorno virtual e instalar dependencias
uv venv
uv pip install -r requirements.txt

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Ejecutar la aplicación
python menu_principal.py
```

## 📖 Uso

### Modo Carpetas (Lotes)

1. Abre la aplicación
2. Selecciona "📁 Procesar Carpetas (Lotes)"
3. Selecciona la carpeta origen (PDFs originales)
4. Selecciona la carpeta destino (PDFs modificados)
5. Selecciona carpeta de salida para los resultados
6. Haz clic en "🔍 ANALIZAR COINCIDENCIAS"
7. Revisa y edita los emparejamientos si es necesario (doble clic en la tabla)
8. Haz clic en "✅ PROCESAR PDFs"

### Modo Archivos Individuales

1. Abre la aplicación
2. Selecciona "📄 Archivos Individuales"
3. Selecciona el PDF original
4. Selecciona el PDF nuevo
5. Selecciona carpeta de salida
6. Haz clic en "⚡ PROCESAR COMPARACIÓN"

### Configuración

1. Haz clic en "⚙️ Configuración" en el menú principal
2. Ajusta los parámetros según tus necesidades:
   - **Resolución (DPI)**: Calidad de conversión (150-600)
   - **Tamaño de Lote**: Páginas procesadas simultáneamente
   - **Sensibilidad de Detección**: Área mínima para detectar cambios
   - **Umbral de Similitud**: Porcentaje para emparejar archivos
   - **Puntos de Alineación**: Precisión de alineación de páginas
3. Haz clic en "💾 GUARDAR Y CERRAR"

## 🏗️ Estructura del Proyecto

```
pdf-comparator/
├── menu_principal.py          # Punto de entrada principal
├── interfaz_carpetas.py       # Interfaz para procesar carpetas
├── interfaz_archivos.py       # Interfaz para archivos individuales
├── funciones_comparador.py     # Lógica de procesamiento
├── configuracion.py           # Sistema de configuración
├── requirements.txt           # Dependencias del proyecto
├── pyproject.toml             # Configuración del proyecto (uv)
├── install.bat / install.sh   # Scripts de instalación con uv
├── run.bat / run.sh           # Scripts de ejecución rápida
├── config.json                # Configuración guardada (se crea automáticamente)
└── README.md                  # Este archivo
```

## 📦 Dependencias

- **PyMuPDF** (>=1.23.0): Procesamiento de PDFs
- **opencv-python** (>=4.8.0): Procesamiento de imágenes y alineación
- **Pillow** (>=10.0.0): Manipulación de imágenes
- **numpy** (>=1.24.0): Operaciones numéricas
- **joblib** (>=1.3.0): Procesamiento paralelo
- **PyPDF2** (>=3.0.0): Fallback para lectura de PDFs

## 🔧 Solución de Problemas

### Error: "uv no está instalado"

El script de instalación intentará instalar uv automáticamente. Si falla:

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### Error: "PyMuPDF no está instalado"

```bash
uv pip install PyMuPDF
```

### Error: "No module named 'cv2'"

```bash
uv pip install opencv-python
```

### La aplicación no inicia

1. Verifica que Python 3.10+ esté instalado: `python --version`
2. Asegúrate de haber activado el entorno virtual: `.venv\Scripts\activate` (Windows) o `source .venv/bin/activate` (Linux/macOS)
3. Reinstala las dependencias: `uv pip install -r requirements.txt --force-reinstall`

### Problemas de memoria con PDFs grandes

1. Abre la configuración
2. Reduce el **Tamaño de Lote** a 2 o 3
3. Reduce la **Resolución (DPI)** a 200 o 150

## 🎯 Parámetros de Configuración

| Parámetro | Descripción | Valores Recomendados |
|-----------|-------------|---------------------|
| **DPI** | Calidad de conversión | 300 (alta calidad) |
| **Tamaño de Lote** | Páginas simultáneas | 5 (balance) |
| **Sensibilidad** | Detección de cambios | 5 (recomendado) |
| **Umbral Similitud** | Emparejamiento archivos | 50% (balance) |
| **Puntos Alineación** | Precisión alineación | 10000 (recomendado) |

## 💡 Ventajas de usar uv

- ⚡ **10-100x más rápido** que pip para instalar paquetes
- 🔒 **Reproducibilidad**: Lock files para versiones exactas
- 🎯 **Gestión automática** de entornos virtuales
- 📦 **Compatibilidad total** con requirements.txt

## 🔨 Crear Ejecutable (.exe)

Para crear un ejecutable standalone que incluya Python y todas las dependencias:

### Windows

```bash
# 1. Instalar PyInstaller (si no está instalado)
uv pip install pyinstaller

# 2. Ejecutar el script de build
build.bat
```

El ejecutable se generará en `dist/PDFComparator.exe`

### Linux/macOS

```bash
# 1. Instalar PyInstaller (si no está instalado)
uv pip install pyinstaller

# 2. Dar permisos de ejecución y ejecutar
chmod +x build.sh
./build.sh
```

El ejecutable se generará en `dist/PDFComparator`

### Opciones Avanzadas

Si necesitas personalizar la compilación, edita `PDFComparator.spec`:

- **Agregar icono**: Descomenta y modifica la línea `icon=None` en el archivo `.spec`
- **Incluir archivos adicionales**: Agrega rutas en la sección `datas`
- **Modificar nombre**: Cambia `name='PDFComparator'` en el archivo `.spec`

### Notas sobre el Ejecutable

- **Tamaño**: El ejecutable será grande (~100-200 MB) porque incluye Python y todas las dependencias
- **Primera ejecución**: Puede tardar unos segundos en iniciar la primera vez
- **Antivirus**: Algunos antivirus pueden marcar el ejecutable como sospechoso (falso positivo). Es seguro.
- **Distribución**: Puedes distribuir solo el `.exe` sin necesidad de instalar Python

## 📝 Notas

- La configuración se guarda en `config.json` (se crea automáticamente)
- El entorno virtual se crea en `.venv/` (ignorado por Git)
- Los PDFs de salida se guardan en la carpeta que especifiques

---

⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!

