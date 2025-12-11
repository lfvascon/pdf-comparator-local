import cv2
import numpy as np
import os
import gc
import difflib
import sys
from pathlib import Path
from PIL import Image
from joblib import Parallel, delayed
import multiprocessing

# PyMuPDF (fitz) - Librería Python pura para trabajar con PDFs
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️  ADVERTENCIA: PyMuPDF no está instalado.")
    print("   Instálalo con: pip install PyMuPDF")

# ==========================================
# 1. CONFIGURACIÓN GLOBAL
# ==========================================

Image.MAX_IMAGE_PIXELS = None

# DPI por defecto para conversión de PDF a imagen (300 = alta calidad)
DPI_DEFAULT = 300

def get_base_path():
    """Obtiene la ruta base correcta, ya sea desde script o ejecutable."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent

def verificar_pymupdf_disponible():
    """
    Verifica si PyMuPDF está disponible.
    Retorna True si está disponible, False en caso contrario.
    """
    return PYMUPDF_AVAILABLE

# ==========================================
# 2. LÓGICA DE TEXTO Y ARCHIVOS
# ==========================================

def encontrar_texto_comun(str1, str2):
    s = difflib.SequenceMatcher(None, str1, str2)
    match = s.find_longest_match(0, len(str1), 0, len(str2))
    if match.size > 0:
        return str1[match.a: match.a + match.size]
    return ""

def detectar_mejor_patron(lista_archivos, umbral=0.5):
    if not lista_archivos: return None
    lista_ordenada = sorted(lista_archivos)
    mejor_patron = None
    max_repeticiones = 0
    visitados = set()

    for i in range(len(lista_ordenada)):
        if i in visitados: continue
        base = lista_ordenada[i]
        patron_candidato = base
        contador = 1
        visitados.add(i)

        for j in range(i + 1, len(lista_ordenada)):
            candidato = lista_ordenada[j]
            ratio = difflib.SequenceMatcher(None, base, candidato).ratio()
            if ratio < umbral: continue
            visitados.add(j)
            contador += 1
            patron_candidato = encontrar_texto_comun(patron_candidato, candidato)
        
        patron_candidato = patron_candidato.strip()
        if contador > max_repeticiones and len(patron_candidato) > 3:
            max_repeticiones = contador
            mejor_patron = patron_candidato
    
    return mejor_patron

def procesar_carpeta(ruta):
    path_obj = Path(ruta)
    if not path_obj.exists(): return {}
    
    archivos = [f.name for f in path_obj.iterdir() if f.is_file()]
    if not archivos: return {}

    patron = detectar_mejor_patron(archivos)
    diccionario_resultados = {}

    for nombre_archivo in archivos:
        ruta_completa = path_obj / nombre_archivo
        if patron:
            try:
                valor_procesado = nombre_archivo.split(patron)[-1]
            except:
                valor_procesado = nombre_archivo.replace(patron, "").strip()
            valor_procesado = valor_procesado.strip("-_.")
        else:
            valor_procesado = nombre_archivo

        diccionario_resultados[nombre_archivo] = {
            "valor": valor_procesado,
            "path": str(ruta_completa)
        }
    return diccionario_resultados

def comparar_listas_completo(dic1, dic2, umbral=0.5):
    lista_resultados = []
    destinos_ya_emparejados = set()

    # 1. Matches Origen -> Destino
    for clave1, datos1 in dic1.items():
        valor1 = datos1.get("valor", "")
        ruta1 = datos1.get("path", "")
        mejor_match_clave = None
        mejor_match_datos = None
        max_ratio = 0.0

        for clave2, datos2 in dic2.items():
            valor2 = datos2.get("valor", "")
            ratio = difflib.SequenceMatcher(None, valor1, valor2).ratio()

            if ratio > max_ratio:
                max_ratio = ratio
                mejor_match_clave = clave2
                mejor_match_datos = datos2

        if max_ratio >= umbral:
            registro = {
                "tipo": "match",
                "origen": {"clave": clave1, "valor": valor1, "ruta": ruta1},
                "destino": {"clave": mejor_match_clave, "valor": mejor_match_datos["valor"], "ruta": mejor_match_datos["path"]},
                "similitud_pct": f"{max_ratio:.0%}"
            }
            destinos_ya_emparejados.add(mejor_match_clave)
            lista_resultados.append(registro)
        else:
            registro = {
                "tipo": "solo_origen",
                "origen": {"clave": clave1, "valor": valor1, "ruta": ruta1},
                "destino": {"clave": "---", "valor": "", "ruta": ""},
                "similitud_pct": "0%"
            }
            lista_resultados.append(registro)

    # 2. Huérfanos Destino
    for clave2, datos2 in dic2.items():
        if clave2 not in destinos_ya_emparejados:
            registro = {
                "tipo": "solo_destino",
                "origen": {"clave": "---", "valor": "", "ruta": ""},
                "destino": {"clave": clave2, "valor": datos2["valor"], "ruta": datos2["path"]},
                "similitud_pct": "0%"
            }
            lista_resultados.append(registro)

    lista_resultados.sort(key=lambda x: x["tipo"], reverse=False)
    return lista_resultados

# ==========================================
# 3. PROCESAMIENTO DE IMAGEN Y PDF
# ==========================================

def limpiar_ruido_mascara(mask, min_area=20):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_clean = np.zeros_like(mask)
    for cnt in contours:
        if cv2.contourArea(cnt) > min_area:
            cv2.drawContours(mask_clean, [cnt], -1, 255, -1)
    return mask_clean

def alinear_imagen(img_base, img_a_mover):
    gray_base = cv2.cvtColor(img_base, cv2.COLOR_RGB2GRAY) if len(img_base.shape) == 3 else img_base
    gray_move = cv2.cvtColor(img_a_mover, cv2.COLOR_RGB2GRAY) if len(img_a_mover.shape) == 3 else img_a_mover

    max_features = 10000
    orb = cv2.ORB_create(max_features)
    keypoints1, descriptors1 = orb.detectAndCompute(gray_move, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray_base, None)

    if descriptors1 is None or descriptors2 is None:
        return cv2.resize(img_a_mover, (img_base.shape[1], img_base.shape[0]))

    matcher = cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING
    bf = cv2.BFMatcher(matcher, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[:int(len(matches) * 0.20)]

    if len(good_matches) < 4:
        return cv2.resize(img_a_mover, (img_base.shape[1], img_base.shape[0]))

    points1 = np.zeros((len(good_matches), 2), dtype=np.float32)
    points2 = np.zeros((len(good_matches), 2), dtype=np.float32)

    for i, match in enumerate(good_matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt

    h, _ = cv2.findHomography(points1, points2, cv2.RANSAC)
    height, width = img_base.shape[:2]
    return cv2.warpPerspective(img_a_mover, h, (width, height))

def procesar_hoja_premium(img_base_pil, img_move_pil, index):
    try:
        img_base_np = np.array(img_base_pil) if img_base_pil else None
        img_move_np = np.array(img_move_pil) if img_move_pil else None
        
        del img_base_pil, img_move_pil

        if img_base_np is None and img_move_np is not None:
            h, w = img_move_np.shape[:2]
            img_base = np.full((h, w, 3), 255, dtype=np.uint8)
            img_move_raw = img_move_np
        elif img_move_np is None and img_base_np is not None:
            h, w = img_base_np.shape[:2]
            img_base = img_base_np
            img_move_raw = np.full((h, w, 3), 255, dtype=np.uint8)
        elif img_base_np is not None and img_move_np is not None:
            img_base = img_base_np
            img_move_raw = img_move_np
        else:
            return None

        del img_base_np, img_move_np

        try:
            img_new = alinear_imagen(img_base, img_move_raw)
        except:
            img_new = cv2.resize(img_move_raw, (img_base.shape[1], img_base.shape[0]))

        del img_move_raw

        gray_base = cv2.cvtColor(img_base, cv2.COLOR_RGB2GRAY) if len(img_base.shape) == 3 else img_base
        gray_new = cv2.cvtColor(img_new, cv2.COLOR_RGB2GRAY) if len(img_new.shape) == 3 else img_new

        del img_base, img_new
        gray_base_copy = gray_base.copy()
        
        inv_base = cv2.bitwise_not(gray_base)
        inv_new = cv2.bitwise_not(gray_new)
        _, bin_base = cv2.threshold(inv_base, 10, 255, cv2.THRESH_TOZERO)
        _, bin_new = cv2.threshold(inv_new, 10, 255, cv2.THRESH_TOZERO)

        del inv_base, inv_new, gray_base, gray_new

        kernel = np.ones((2, 2), np.uint8)
        raw_green = cv2.subtract(bin_new, cv2.dilate(bin_base, kernel, iterations=1))
        raw_magenta = cv2.subtract(bin_base, cv2.dilate(bin_new, kernel, iterations=1))

        del bin_base, bin_new

        _, mask_green = cv2.threshold(raw_green, 1, 255, cv2.THRESH_BINARY)
        _, mask_magenta = cv2.threshold(raw_magenta, 1, 255, cv2.THRESH_BINARY)
        
        del raw_green, raw_magenta
        
        c_green = limpiar_ruido_mascara(mask_green, min_area=5)
        c_magenta = limpiar_ruido_mascara(mask_magenta, min_area=5)
        
        del mask_green, mask_magenta

        ghost = cv2.addWeighted(gray_base_copy, 0.3, np.full_like(gray_base_copy, 255), 0.7, 0)
        final = cv2.cvtColor(ghost, cv2.COLOR_GRAY2RGB)
        final[c_green > 0] = [0, 200, 0]
        final[c_magenta > 0] = [255, 0, 180]

        del c_green, c_magenta, ghost
        return Image.fromarray(final)
    except:
        return None

def obtener_numero_paginas(pdf_path):
    """
    Obtiene el número de páginas de un PDF usando PyMuPDF.
    
    Args:
        pdf_path: Ruta al archivo PDF
    
    Returns:
        Número de páginas o 1 si hay error
    """
    if not PYMUPDF_AVAILABLE:
        # Fallback a PyPDF2 si PyMuPDF no está disponible
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages)
        except:
            return 1
    
    try:
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
        return num_pages
    except Exception:
        # Fallback a PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages)
        except:
            return 1

def pdf_a_imagenes(pdf_path, dpi=DPI_DEFAULT, first_page=None, last_page=None):
    """
    Convierte páginas de un PDF a imágenes PIL usando PyMuPDF.
    
    Args:
        pdf_path: Ruta al archivo PDF
        dpi: Resolución en DPI (por defecto 300)
        first_page: Primera página a convertir (1-indexed, None = primera)
        last_page: Última página a convertir (1-indexed, None = última)
    
    Returns:
        Lista de objetos PIL.Image
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF no está instalado. Instálalo con: pip install PyMuPDF")
    
    try:
        doc = fitz.open(pdf_path)
        imagenes = []
        
        # Ajustar índices (PyMuPDF usa 0-indexed, pero la función usa 1-indexed)
        start_idx = (first_page - 1) if first_page else 0
        end_idx = (last_page - 1) if last_page else (len(doc) - 1)
        
        # Calcular matriz de zoom basada en DPI
        # PyMuPDF usa 72 DPI por defecto, así que necesitamos escalar
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in range(start_idx, min(end_idx + 1, len(doc))):
            page = doc[page_num]
            # Renderizar página a imagen
            pix = page.get_pixmap(matrix=mat)
            # Convertir a PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            imagenes.append(img)
            pix = None  # Liberar memoria
        
        doc.close()
        return imagenes
    except Exception as e:
        raise Exception(f"Error al convertir PDF a imágenes: {e}")

def procesar_par_de_archivos(registro_match, carpeta_salida, callback_progreso=None, callback_estado=None, dpi=DPI_DEFAULT):
    """
    Procesa un par de archivos PDF y genera un PDF comparativo.
    
    Args:
        registro_match: Diccionario con información de los archivos a comparar
        carpeta_salida: Carpeta donde guardar el resultado
        callback_progreso: Función callback para actualizar progreso
        callback_estado: Función callback para actualizar estado
        dpi: Resolución para la conversión (por defecto 300)
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    if not PYMUPDF_AVAILABLE:
        if callback_estado:
            callback_estado("❌ PyMuPDF no está instalado. Instálalo con: pip install PyMuPDF")
        return False
    
    ruta_original = registro_match['origen']['ruta']
    ruta_nueva = registro_match['destino']['ruta']
    nombre_base = os.path.basename(ruta_original)
    ruta_salida_pdf = os.path.join(carpeta_salida, f"Comparativa_{nombre_base}")

    if not os.path.exists(ruta_original) or not os.path.exists(ruta_nueva):
        if callback_estado: callback_estado(f"❌ No encontrado: {nombre_base}")
        return False

    try:
        if callback_estado: callback_estado(f"📊 Analizando: {nombre_base[:40]}...")
        
        n_a = obtener_numero_paginas(ruta_original)
        n_b = obtener_numero_paginas(ruta_nueva)
        max_pages = max(n_a, n_b)
        
        TAMANO_LOTE = 5
        imagenes_finales = []
        
        for lote_inicio in range(1, max_pages + 1, TAMANO_LOTE):
            lote_fin = min(lote_inicio + TAMANO_LOTE - 1, max_pages)
            if callback_estado: callback_estado(f"📄 Pág {lote_inicio}-{lote_fin}/{max_pages}: {nombre_base[:30]}...")
            
            # Cargar lote usando PyMuPDF
            try:
                pages_a = pdf_a_imagenes(ruta_original, dpi=dpi, first_page=lote_inicio, last_page=lote_fin)
            except Exception as e:
                if callback_estado: callback_estado(f"⚠️  Error en archivo original: {str(e)[:30]}")
                pages_a = []
            
            try:
                pages_b = pdf_a_imagenes(ruta_nueva, dpi=dpi, first_page=lote_inicio, last_page=lote_fin)
            except Exception as e:
                if callback_estado: callback_estado(f"⚠️  Error en archivo nuevo: {str(e)[:30]}")
                pages_b = []
            
            # Normalizar lote
            lote_size = max(len(pages_a), len(pages_b))
            pages_a += [None]*(lote_size - len(pages_a))
            pages_b += [None]*(lote_size - len(pages_b))
            
            # Procesar
            cores = max(1, min(2, multiprocessing.cpu_count()-1))
            imgs_lote = Parallel(n_jobs=cores, verbose=0)(
                delayed(procesar_hoja_premium)(pages_a[i], pages_b[i], lote_inicio+i) for i in range(lote_size)
            )
            imagenes_finales.extend([x for x in imgs_lote if x])
            
            del pages_a, pages_b, imgs_lote
            gc.collect()

        if imagenes_finales:
            if callback_estado: callback_estado(f"💾 Guardando: {nombre_base[:40]}...")
            imagenes_finales[0].save(ruta_salida_pdf, save_all=True, append_images=imagenes_finales[1:], optimize=True)
            for i in imagenes_finales: 
                if hasattr(i, 'close'): i.close()
            del imagenes_finales
            gc.collect()
            
            if callback_progreso: callback_progreso(nombre_base)
            return True
        return False

    except Exception as e:
        if callback_estado: callback_estado(f"❌ Error: {str(e)[:50]}")
        gc.collect()
        return False