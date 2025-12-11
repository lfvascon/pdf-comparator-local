"""
PDF Comparison Functions Module.
Provides functionality to compare PDF documents and highlight differences.
"""
from __future__ import annotations

import gc
import logging
import multiprocessing
import os
from contextlib import contextmanager
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import cv2
import numpy as np
from joblib import Parallel, delayed
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PyMuPDF (fitz) - Pure Python library for PDF handling
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed. Install with: pip install PyMuPDF")

# ==========================================
# CONFIGURATION
# ==========================================

Image.MAX_IMAGE_PIXELS = None

# Import configuration module
try:
    from configuracion import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Configuration getters - use config file if available, otherwise defaults
def get_dpi() -> int:
    """Get DPI setting."""
    return get_config().dpi if CONFIG_AVAILABLE else 300

def get_batch_size() -> int:
    """Get batch size setting."""
    return get_config().batch_size if CONFIG_AVAILABLE else 5

def get_min_contour_area() -> int:
    """Get minimum contour area setting."""
    return get_config().min_contour_area if CONFIG_AVAILABLE else 5

def get_similarity_threshold() -> float:
    """Get similarity threshold setting."""
    return get_config().similarity_threshold if CONFIG_AVAILABLE else 0.5

def get_orb_max_features() -> int:
    """Get ORB max features setting."""
    return get_config().orb_max_features if CONFIG_AVAILABLE else 10000

def get_match_ratio() -> float:
    """Get match ratio setting."""
    return get_config().match_ratio if CONFIG_AVAILABLE else 0.20

def get_min_matches_homography() -> int:
    """Get minimum matches for homography setting."""
    return get_config().min_matches_homography if CONFIG_AVAILABLE else 4


@dataclass(frozen=True)
class Colors:
    """Color constants for difference highlighting."""
    GREEN: tuple[int, int, int] = (0, 200, 0)      # New content
    MAGENTA: tuple[int, int, int] = (255, 0, 180)  # Removed content
    WHITE: int = 255


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def get_base_path() -> Path:
    """Get base path, works for both script and frozen executable."""
    import sys
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def verificar_pymupdf_disponible() -> bool:
    """Check if PyMuPDF is available."""
    return PYMUPDF_AVAILABLE


@contextmanager
def open_pdf(pdf_path: str | Path) -> Generator[fitz.Document, None, None]:
    """Context manager for safely opening and closing PDF documents."""
    doc = fitz.open(str(pdf_path))
    try:
        yield doc
    finally:
        doc.close()


# ==========================================
# TEXT AND FILE MATCHING LOGIC
# ==========================================

def encontrar_texto_comun(str1: str, str2: str) -> str:
    """Find the longest common substring between two strings."""
    matcher = SequenceMatcher(None, str1, str2)
    match = matcher.find_longest_match(0, len(str1), 0, len(str2))
    return str1[match.a:match.a + match.size] if match.size > 0 else ""


def detectar_mejor_patron(lista_archivos: list[str], umbral: float | None = None) -> str | None:
    """
    Detect the best common pattern among a list of filenames.
    
    Args:
        lista_archivos: List of filenames to analyze
        umbral: Similarity threshold (0.0 to 1.0)
    
    Returns:
        Best pattern found or None
    """
    if umbral is None:
        umbral = get_similarity_threshold()
    
    if not lista_archivos:
        return None
    
    lista_ordenada = sorted(lista_archivos)
    mejor_patron: str | None = None
    max_repeticiones = 0
    visitados: set[int] = set()

    for i, base in enumerate(lista_ordenada):
        if i in visitados:
            continue
        
        patron_candidato = base
        contador = 1
        visitados.add(i)

        for j in range(i + 1, len(lista_ordenada)):
            if j in visitados:
                continue
            
            candidato = lista_ordenada[j]
            ratio = SequenceMatcher(None, base, candidato).ratio()
            
            if ratio >= umbral:
                visitados.add(j)
                contador += 1
                patron_candidato = encontrar_texto_comun(patron_candidato, candidato)
        
        patron_candidato = patron_candidato.strip()
        if contador > max_repeticiones and len(patron_candidato) > 3:
            max_repeticiones = contador
            mejor_patron = patron_candidato
    
    return mejor_patron


def procesar_carpeta(ruta: str | Path) -> dict[str, dict[str, str]]:
    """
    Process a folder and extract file information with pattern detection.
    
    Args:
        ruta: Path to the folder
    
    Returns:
        Dictionary with filename as key and metadata as value
    """
    path_obj = Path(ruta)
    if not path_obj.exists():
        return {}
    
    archivos = [f.name for f in path_obj.iterdir() if f.is_file()]
    if not archivos:
        return {}

    patron = detectar_mejor_patron(archivos)
    resultados: dict[str, dict[str, str]] = {}

    for nombre_archivo in archivos:
        ruta_completa = path_obj / nombre_archivo
        
        if patron:
            try:
                valor_procesado = nombre_archivo.split(patron)[-1]
            except (ValueError, IndexError):
                valor_procesado = nombre_archivo.replace(patron, "").strip()
            valor_procesado = valor_procesado.strip("-_.")
        else:
            valor_procesado = nombre_archivo

        resultados[nombre_archivo] = {
            "valor": valor_procesado,
            "path": str(ruta_completa)
        }
    
    return resultados


def comparar_listas_completo(
    dic1: dict[str, dict[str, str]], 
    dic2: dict[str, dict[str, str]], 
    umbral: float | None = None
) -> list[dict]:
    """
    Compare two file dictionaries and find matches.
    
    Args:
        dic1: Source files dictionary
        dic2: Destination files dictionary
        umbral: Similarity threshold
    
    Returns:
        List of match records
    """
    if umbral is None:
        umbral = get_similarity_threshold()
    
    resultados: list[dict] = []
    destinos_emparejados: set[str] = set()

    # Find matches from source to destination
    for clave1, datos1 in dic1.items():
        valor1 = datos1.get("valor", "")
        ruta1 = datos1.get("path", "")
        
        mejor_match: tuple[str | None, dict | None, float] = (None, None, 0.0)

        for clave2, datos2 in dic2.items():
            valor2 = datos2.get("valor", "")
            ratio = SequenceMatcher(None, valor1, valor2).ratio()

            if ratio > mejor_match[2]:
                mejor_match = (clave2, datos2, ratio)

        if mejor_match[2] >= umbral and mejor_match[0] and mejor_match[1]:
            registro = {
                "tipo": "match",
                "origen": {"clave": clave1, "valor": valor1, "ruta": ruta1},
                "destino": {
                    "clave": mejor_match[0], 
                    "valor": mejor_match[1]["valor"], 
                    "ruta": mejor_match[1]["path"]
                },
                "similitud_pct": f"{mejor_match[2]:.0%}"
            }
            destinos_emparejados.add(mejor_match[0])
        else:
            registro = {
                "tipo": "solo_origen",
                "origen": {"clave": clave1, "valor": valor1, "ruta": ruta1},
                "destino": {"clave": "---", "valor": "", "ruta": ""},
                "similitud_pct": "0%"
            }
        resultados.append(registro)

    # Find orphan destinations
    for clave2, datos2 in dic2.items():
        if clave2 not in destinos_emparejados:
            resultados.append({
                "tipo": "solo_destino",
                "origen": {"clave": "---", "valor": "", "ruta": ""},
                "destino": {"clave": clave2, "valor": datos2["valor"], "ruta": datos2["path"]},
                "similitud_pct": "0%"
            })

    return sorted(resultados, key=lambda x: x["tipo"])


# ==========================================
# IMAGE PROCESSING
# ==========================================

def limpiar_ruido_mascara(mask: np.ndarray, min_area: int | None = None) -> np.ndarray:
    """
    Remove noise from a binary mask by filtering small contours.
    
    Args:
        mask: Binary mask image
        min_area: Minimum contour area to keep
    
    Returns:
        Cleaned binary mask
    """
    if min_area is None:
        min_area = get_min_contour_area()
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_clean = np.zeros_like(mask)
    
    for cnt in contours:
        if cv2.contourArea(cnt) > min_area:
            cv2.drawContours(mask_clean, [cnt], -1, Colors.WHITE, -1)
    
    return mask_clean


def alinear_imagen(img_base: np.ndarray, img_a_mover: np.ndarray) -> np.ndarray:
    """
    Align an image to a base image using ORB feature matching and homography.
    
    Args:
        img_base: Reference image
        img_a_mover: Image to align
    
    Returns:
        Aligned image
    """
    # Convert to grayscale if needed
    gray_base = cv2.cvtColor(img_base, cv2.COLOR_RGB2GRAY) if img_base.ndim == 3 else img_base
    gray_move = cv2.cvtColor(img_a_mover, cv2.COLOR_RGB2GRAY) if img_a_mover.ndim == 3 else img_a_mover

    # Feature detection
    orb = cv2.ORB_create(get_orb_max_features())
    keypoints1, descriptors1 = orb.detectAndCompute(gray_move, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray_base, None)

    # Fallback to resize if no descriptors
    target_size = (img_base.shape[1], img_base.shape[0])
    if descriptors1 is None or descriptors2 is None:
        return cv2.resize(img_a_mover, target_size)

    # Match features
    bf = cv2.BFMatcher(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING, crossCheck=True)
    matches = sorted(bf.match(descriptors1, descriptors2), key=lambda x: x.distance)
    good_matches = matches[:int(len(matches) * get_match_ratio())]

    if len(good_matches) < get_min_matches_homography():
        return cv2.resize(img_a_mover, target_size)

    # Calculate homography
    points1 = np.array([keypoints1[m.queryIdx].pt for m in good_matches], dtype=np.float32)
    points2 = np.array([keypoints2[m.trainIdx].pt for m in good_matches], dtype=np.float32)

    h, _ = cv2.findHomography(points1, points2, cv2.RANSAC)
    
    if h is None:
        return cv2.resize(img_a_mover, target_size)
    
    return cv2.warpPerspective(img_a_mover, h, target_size)


def procesar_hoja_premium(
    img_base_pil: Image.Image | None, 
    img_move_pil: Image.Image | None, 
    index: int
) -> Image.Image | None:
    """
    Process a page pair and create a comparison image with differences highlighted.
    
    Args:
        img_base_pil: Base/original page image
        img_move_pil: New/modified page image
        index: Page index (for logging)
    
    Returns:
        Comparison image with differences highlighted, or None on error
    """
    try:
        # Convert PIL to numpy
        img_base_np = np.array(img_base_pil) if img_base_pil else None
        img_move_np = np.array(img_move_pil) if img_move_pil else None

        # Handle missing pages
        if img_base_np is None and img_move_np is not None:
            h, w = img_move_np.shape[:2]
            img_base = np.full((h, w, 3), Colors.WHITE, dtype=np.uint8)
            img_move_raw = img_move_np
        elif img_move_np is None and img_base_np is not None:
            h, w = img_base_np.shape[:2]
            img_base = img_base_np
            img_move_raw = np.full((h, w, 3), Colors.WHITE, dtype=np.uint8)
        elif img_base_np is not None and img_move_np is not None:
            img_base = img_base_np
            img_move_raw = img_move_np
        else:
            return None

        # Align images
        try:
            img_new = alinear_imagen(img_base, img_move_raw)
        except cv2.error:
            img_new = cv2.resize(img_move_raw, (img_base.shape[1], img_base.shape[0]))

        # Convert to grayscale
        gray_base = cv2.cvtColor(img_base, cv2.COLOR_RGB2GRAY) if img_base.ndim == 3 else img_base
        gray_new = cv2.cvtColor(img_new, cv2.COLOR_RGB2GRAY) if img_new.ndim == 3 else img_new
        gray_base_copy = gray_base.copy()

        # Create binary masks
        inv_base = cv2.bitwise_not(gray_base)
        inv_new = cv2.bitwise_not(gray_new)
        _, bin_base = cv2.threshold(inv_base, 10, Colors.WHITE, cv2.THRESH_TOZERO)
        _, bin_new = cv2.threshold(inv_new, 10, Colors.WHITE, cv2.THRESH_TOZERO)

        # Calculate differences
        kernel = np.ones((2, 2), np.uint8)
        raw_green = cv2.subtract(bin_new, cv2.dilate(bin_base, kernel, iterations=1))
        raw_magenta = cv2.subtract(bin_base, cv2.dilate(bin_new, kernel, iterations=1))

        _, mask_green = cv2.threshold(raw_green, 1, Colors.WHITE, cv2.THRESH_BINARY)
        _, mask_magenta = cv2.threshold(raw_magenta, 1, Colors.WHITE, cv2.THRESH_BINARY)

        # Clean noise
        c_green = limpiar_ruido_mascara(mask_green)
        c_magenta = limpiar_ruido_mascara(mask_magenta)

        # Create output image
        ghost = cv2.addWeighted(gray_base_copy, 0.3, np.full_like(gray_base_copy, Colors.WHITE), 0.7, 0)
        final = cv2.cvtColor(ghost, cv2.COLOR_GRAY2RGB)
        final[c_green > 0] = Colors.GREEN
        final[c_magenta > 0] = Colors.MAGENTA

        return Image.fromarray(final)
    
    except Exception as e:
        logger.error(f"Error processing page {index}: {e}")
        return None


# ==========================================
# PDF PROCESSING
# ==========================================

def obtener_numero_paginas(pdf_path: str | Path) -> int:
    """
    Get the number of pages in a PDF document.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Number of pages, or 1 on error
    """
    if not PYMUPDF_AVAILABLE:
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages)
        except Exception:
            return 1
    
    try:
        with open_pdf(pdf_path) as doc:
            return len(doc)
    except Exception:
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages)
        except Exception:
            return 1


def pdf_a_imagenes(
    pdf_path: str | Path, 
    dpi: int | None = None, 
    first_page: int | None = None, 
    last_page: int | None = None
) -> list[Image.Image]:
    """
    Convert PDF pages to PIL Images using PyMuPDF.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution in DPI (default 300)
        first_page: First page to convert (1-indexed, None = first)
        last_page: Last page to convert (1-indexed, None = last)
    
    Returns:
        List of PIL Image objects
    
    Raises:
        ImportError: If PyMuPDF is not installed
        Exception: If conversion fails
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF not installed. Install with: pip install PyMuPDF")
    
    if dpi is None:
        dpi = get_dpi()
    
    try:
        with open_pdf(pdf_path) as doc:
            # Adjust indices (PyMuPDF is 0-indexed, function is 1-indexed)
            start_idx = (first_page - 1) if first_page else 0
            end_idx = (last_page - 1) if last_page else (len(doc) - 1)
            
            # Calculate zoom matrix for DPI
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            imagenes: list[Image.Image] = []
            for page_num in range(start_idx, min(end_idx + 1, len(doc))):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                imagenes.append(img)
            
            return imagenes
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {e}") from e


def procesar_par_de_archivos(
    registro_match: dict,
    carpeta_salida: str | Path,
    callback_progreso: Callable[[str], None] | None = None,
    callback_estado: Callable[[str], None] | None = None,
    dpi: int | None = None
) -> bool:
    """
    Process a pair of PDF files and generate a comparison PDF.
    
    Args:
        registro_match: Dictionary with file information to compare
        carpeta_salida: Output folder path
        callback_progreso: Progress callback function
        callback_estado: Status callback function
        dpi: Resolution for conversion (default 300)
    
    Returns:
        True if successful, False otherwise
    """
    if not PYMUPDF_AVAILABLE:
        if callback_estado:
            callback_estado("❌ PyMuPDF not installed. Install with: pip install PyMuPDF")
        return False
    
    if dpi is None:
        dpi = get_dpi()
    
    ruta_original = registro_match['origen']['ruta']
    ruta_nueva = registro_match['destino']['ruta']
    nombre_base = os.path.basename(ruta_original)
    ruta_salida_pdf = Path(carpeta_salida) / f"Comparativa_{nombre_base}"

    if not os.path.exists(ruta_original) or not os.path.exists(ruta_nueva):
        if callback_estado:
            callback_estado(f"❌ Not found: {nombre_base}")
        return False

    try:
        if callback_estado:
            callback_estado(f"📊 Analyzing: {nombre_base[:40]}...")
        
        n_a = obtener_numero_paginas(ruta_original)
        n_b = obtener_numero_paginas(ruta_nueva)
        max_pages = max(n_a, n_b)
        
        imagenes_finales: list[Image.Image] = []
        cores = max(1, min(2, multiprocessing.cpu_count() - 1))
        
        batch_size = get_batch_size()
        for lote_inicio in range(1, max_pages + 1, batch_size):
            lote_fin = min(lote_inicio + batch_size - 1, max_pages)
            
            if callback_estado:
                callback_estado(f"📄 Page {lote_inicio}-{lote_fin}/{max_pages}: {nombre_base[:30]}...")
            
            # Load batch
            try:
                pages_a = pdf_a_imagenes(ruta_original, dpi=dpi, first_page=lote_inicio, last_page=lote_fin)
            except Exception as e:
                logger.warning(f"Error loading original file: {e}")
                pages_a = []
            
            try:
                pages_b = pdf_a_imagenes(ruta_nueva, dpi=dpi, first_page=lote_inicio, last_page=lote_fin)
            except Exception as e:
                logger.warning(f"Error loading new file: {e}")
                pages_b = []
            
            # Normalize batch size
            lote_size = max(len(pages_a), len(pages_b))
            pages_a.extend([None] * (lote_size - len(pages_a)))
            pages_b.extend([None] * (lote_size - len(pages_b)))
            
            # Process in parallel
            imgs_lote = Parallel(n_jobs=cores, verbose=0)(
                delayed(procesar_hoja_premium)(pages_a[i], pages_b[i], lote_inicio + i) 
                for i in range(lote_size)
            )
            imagenes_finales.extend(img for img in imgs_lote if img is not None)
            
            # Clean up batch
            gc.collect()

        if imagenes_finales:
            if callback_estado:
                callback_estado(f"💾 Saving: {nombre_base[:40]}...")
            
            imagenes_finales[0].save(
                str(ruta_salida_pdf), 
                save_all=True, 
                append_images=imagenes_finales[1:], 
                optimize=True
            )
            
            # Clean up
            for img in imagenes_finales:
                img.close()
            gc.collect()
            
            if callback_progreso:
                callback_progreso(nombre_base)
            return True
        
        return False

    except Exception as e:
        logger.error(f"Error processing files: {e}")
        if callback_estado:
            callback_estado(f"❌ Error: {str(e)[:50]}")
        gc.collect()
        return False
