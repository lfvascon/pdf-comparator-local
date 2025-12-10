import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import os
import threading
import gc

# --- IMPORTANTE: CONECTAR CON LA INTERFAZ DE CARPETAS ---
# Asegúrate de que el archivo 'interfaz_carpetas.py' esté en la misma carpeta.
try:
    from interfaz_carpetas import AppComparador
except ImportError:
    AppComparador = None

# Importar funciones del comparador
import funciones_comparador as fc

def abrir_interfaz_archivos():
    # Crear una ventana secundaria (Toplevel)
    ventana_pdf = tk.Toplevel(root)
    ventana_pdf.title("Comparación de Archivos PDF (Modo Individual)")
    ventana_pdf.geometry("550x450")

    # Variables
    ruta_pdf1 = tk.StringVar()
    ruta_pdf2 = tk.StringVar()
    ruta_salida = tk.StringVar()
    poppler_path = None
    procesando = False

    def verificar_poppler():
        nonlocal poppler_path
        poppler_path = fc.verificar_poppler_disponible()
        if poppler_path:
            status_label.config(text=f"✓ Poppler detectado")
        else:
            status_label.config(text="⚠️ Poppler no detectado")
            messagebox.showerror(
                "Error Crítico", 
                "No se encontró Poppler.\nEdita 'funciones_comparador.py' y corrige la variable POPPLER_PATH_MANUAL."
            )

    def seleccionar_pdf_1():
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Original",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            ruta_pdf1.set(archivo)
            lbl_info1.config(text=f"...{archivo[-45:]}", fg="blue")

    def seleccionar_pdf_2():
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Nuevo",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            ruta_pdf2.set(archivo)
            lbl_info2.config(text=f"...{archivo[-45:]}", fg="blue")

    def seleccionar_carpeta_salida():
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if carpeta:
            ruta_salida.set(carpeta)
            lbl_info_salida.config(text=f"...{carpeta[-45:]}", fg="blue")

    def comparar():
        nonlocal procesando
        if procesando:
            return
        
        p1 = ruta_pdf1.get()
        p2 = ruta_pdf2.get()
        salida = ruta_salida.get()
        
        if not p1 or not p2:
            messagebox.showwarning("Atención", "Selecciona ambos archivos primero.")
            return
        
        if not salida:
            messagebox.showwarning("Atención", "Selecciona la carpeta de salida.")
            return
        
        if not os.path.exists(p1) or not os.path.exists(p2):
            messagebox.showerror("Error", "Uno o ambos archivos no existen.")
            return
        
        if not poppler_path:
            messagebox.showerror("Error", "Poppler no disponible.")
            return
        
        if not os.path.exists(salida):
            os.makedirs(salida)
        
        procesando = True
        progress_var.set(0)
        status_label.config(text="Procesando comparación...")
        
        # Crear registro_match directamente sin detección de patrones
        registro_match = {
            'origen': {
                'clave': os.path.basename(p1),
                'valor': os.path.basename(p1),
                'ruta': p1
            },
            'destino': {
                'clave': os.path.basename(p2),
                'valor': os.path.basename(p2),
                'ruta': p2
            },
            'tipo': 'match',
            'similitud_pct': '100%'
        }
        
        def worker():
            def cb_prog(nombre):
                ventana_pdf.after(0, lambda: progress_var.set(100))
            
            def cb_estado(msg):
                ventana_pdf.after(0, lambda: status_label.config(text=msg))
            
            res = fc.procesar_par_de_archivos(
                registro_match,
                poppler_path,
                salida,
                callback_progreso=cb_prog,
                callback_estado=cb_estado
            )
            
            ventana_pdf.after(0, lambda: finalizar(res, salida))
        
        threading.Thread(target=worker, daemon=True).start()

    def finalizar(exitoso, ruta):
        nonlocal procesando
        procesando = False
        progress_var.set(100)
        
        if exitoso:
            status_label.config(text="✓ Proceso completado exitosamente.")
            messagebox.showinfo("Éxito", f"Comparación guardada en:\n{ruta}")
        else:
            status_label.config(text="✗ Error al procesar.")
            messagebox.showerror("Error", "No se pudo completar la comparación.")

    # --- UI Archivos ---
    tk.Label(ventana_pdf, text="Comparación Individual de PDFs", font=("Arial", 14, "bold")).pack(pady=10)

    # Frame de selección
    frame_seleccion = tk.Frame(ventana_pdf)
    frame_seleccion.pack(fill="x", padx=20, pady=5)

    frame_1 = tk.Frame(frame_seleccion, relief="groove", bd=2)
    frame_1.pack(fill="x", pady=5)
    tk.Label(frame_1, text="Archivo Origen:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
    tk.Button(frame_1, text="📄 Seleccionar Original", command=seleccionar_pdf_1).pack(pady=2)
    lbl_info1 = tk.Label(frame_1, text="Sin selección", fg="gray", wraplength=500)
    lbl_info1.pack(pady=2)

    frame_2 = tk.Frame(frame_seleccion, relief="groove", bd=2)
    frame_2.pack(fill="x", pady=5)
    tk.Label(frame_2, text="Archivo Destino:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
    tk.Button(frame_2, text="📄 Seleccionar Nuevo", command=seleccionar_pdf_2).pack(pady=2)
    lbl_info2 = tk.Label(frame_2, text="Sin selección", fg="gray", wraplength=500)
    lbl_info2.pack(pady=2)

    frame_salida = tk.Frame(frame_seleccion, relief="groove", bd=2)
    frame_salida.pack(fill="x", pady=5)
    tk.Label(frame_salida, text="Carpeta de Salida:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
    tk.Button(frame_salida, text="📂 Seleccionar Carpeta", command=seleccionar_carpeta_salida).pack(pady=2)
    lbl_info_salida = tk.Label(frame_salida, text="Sin selección", fg="gray", wraplength=500)
    lbl_info_salida.pack(pady=2)

    # Botón de procesamiento
    tk.Button(ventana_pdf, text="⚡ PROCESAR COMPARACIÓN", bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), command=comparar, height=2).pack(pady=15, fill="x", padx=50)

    # Barra de progreso y estado
    frame_progreso = tk.Frame(ventana_pdf)
    frame_progreso.pack(fill="x", padx=20, pady=5)
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame_progreso, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(side="left", padx=5)
    
    status_label = tk.Label(frame_progreso, text="Listo", anchor="w")
    status_label.pack(side="left", padx=5, fill="x", expand=True)

    # Verificar Poppler al abrir
    verificar_poppler()


def abrir_interfaz_carpetas():
    if AppComparador is None:
        messagebox.showerror("Error", "No se encontró el archivo 'interfaz_carpetas.py'.\nAsegúrate de tenerlo en la misma carpeta.")
        return

    # Creamos una ventana secundaria para la interfaz de carpetas
    ventana_carpetas = tk.Toplevel(root)
    
    # Instanciamos la clase AppComparador pasándole esta nueva ventana como root
    app = AppComparador(ventana_carpetas)
    
    # Nota: AppComparador se encargará de configurar el título y tamaño de 'ventana_carpetas'


# ==========================================
# VENTANA PRINCIPAL (Menú)
# ==========================================
root = tk.Tk()
root.title("Menú de Herramientas PDF")
root.geometry("400x300")

# Título
tk.Label(root, text="Sistema de Comparación PDF", font=("Arial", 16, "bold"), fg="#333").pack(pady=20)
tk.Label(root, text="Selecciona el modo de trabajo:", font=("Arial", 10)).pack()

# Contenedor de botones
frame_botones = tk.Frame(root)
frame_botones.pack(pady=20)

# Botón Archivos
btn_archivos = tk.Button(frame_botones, text="📄 Archivos Individuales", font=("Arial", 11), 
                         width=25, height=2, command=abrir_interfaz_archivos)
btn_archivos.pack(pady=10)

# Botón Carpetas (AHORA CONECTADO)
btn_carpetas = tk.Button(frame_botones, text="📁 Procesar Carpetas (Lotes)", font=("Arial", 11), 
                         width=25, height=2, command=abrir_interfaz_carpetas)
btn_carpetas.pack(pady=10)

# Pie de página
tk.Label(root, text="v1.0 - Edición Local", fg="#999", font=("Arial", 8)).pack(side="bottom", pady=10)

root.mainloop()