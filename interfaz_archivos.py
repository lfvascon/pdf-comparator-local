import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import os
import threading
import gc

# IMPORTE CRÍTICO: Traemos la lógica del otro archivo
# Asegúrate de que ambos archivos estén en la misma carpeta
import funciones_comparador as fc

class AppComparadorArchivos:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparación de Archivos PDF (Modo Individual)")
        self.root.geometry("550x450")
        
        # Variables de estado
        self.ruta_pdf1 = tk.StringVar()
        self.ruta_pdf2 = tk.StringVar()
        self.ruta_salida = tk.StringVar()
        self.poppler_path = None
        self.procesando = False

        self.crear_widgets()
        
        # Verificar Poppler al iniciar
        self.verificar_poppler()

    def crear_widgets(self):
        # Título
        tk.Label(self.root, text="Comparación Individual de PDFs", font=("Arial", 14, "bold")).pack(pady=10)

        # Frame de selección
        frame_seleccion = tk.Frame(self.root)
        frame_seleccion.pack(fill="x", padx=20, pady=5)

        # Archivo Origen
        frame_1 = tk.Frame(frame_seleccion, relief="groove", bd=2)
        frame_1.pack(fill="x", pady=5)
        tk.Label(frame_1, text="Archivo Origen:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        tk.Button(frame_1, text="📄 Seleccionar Original", command=self.seleccionar_pdf_1).pack(pady=2)
        self.lbl_info1 = tk.Label(frame_1, text="Sin selección", fg="gray", wraplength=500)
        self.lbl_info1.pack(pady=2)

        # Archivo Destino
        frame_2 = tk.Frame(frame_seleccion, relief="groove", bd=2)
        frame_2.pack(fill="x", pady=5)
        tk.Label(frame_2, text="Archivo Destino:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        tk.Button(frame_2, text="📄 Seleccionar Nuevo", command=self.seleccionar_pdf_2).pack(pady=2)
        self.lbl_info2 = tk.Label(frame_2, text="Sin selección", fg="gray", wraplength=500)
        self.lbl_info2.pack(pady=2)

        # Carpeta de Salida
        frame_salida = tk.Frame(frame_seleccion, relief="groove", bd=2)
        frame_salida.pack(fill="x", pady=5)
        tk.Label(frame_salida, text="Carpeta de Salida:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        tk.Button(frame_salida, text="📂 Seleccionar Carpeta", command=self.seleccionar_carpeta_salida).pack(pady=2)
        self.lbl_info_salida = tk.Label(frame_salida, text="Sin selección", fg="gray", wraplength=500)
        self.lbl_info_salida.pack(pady=2)

        # Botón de procesamiento
        tk.Button(self.root, text="⚡ PROCESAR COMPARACIÓN", bg="#4CAF50", fg="white", 
                  font=("Arial", 11, "bold"), command=self.comparar, height=2).pack(pady=15, fill="x", padx=50)

        # Barra de progreso y estado
        frame_progreso = tk.Frame(self.root)
        frame_progreso.pack(fill="x", padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame_progreso, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(side="left", padx=5)
        
        self.status_label = tk.Label(frame_progreso, text="Listo", anchor="w")
        self.status_label.pack(side="left", padx=5, fill="x", expand=True)

    def verificar_poppler(self):
        """Verifica Poppler usando la función importada."""
        def check():
            self.poppler_path = fc.verificar_poppler_disponible()
            if self.poppler_path:
                self.root.after(0, lambda: self.status_label.config(text="✓ Poppler detectado"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="⚠️ Poppler no detectado"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error Crítico", 
                    "No se encontró Poppler.\nEdita 'funciones_comparador.py' y corrige la variable POPPLER_PATH_MANUAL."
                ))
        threading.Thread(target=check, daemon=True).start()

    def seleccionar_pdf_1(self):
        # Quitar topmost temporalmente para permitir que el diálogo esté encima
        self.root.attributes('-topmost', False)
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Original",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        # Restaurar ventana encima después del diálogo
        self.root.lift()
        self.root.focus_force()
        if archivo:
            self.ruta_pdf1.set(archivo)
            self.lbl_info1.config(text=f"...{archivo[-45:]}", fg="blue")

    def seleccionar_pdf_2(self):
        # Quitar topmost temporalmente para permitir que el diálogo esté encima
        self.root.attributes('-topmost', False)
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Nuevo",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        # Restaurar ventana encima después del diálogo
        self.root.lift()
        self.root.focus_force()
        if archivo:
            self.ruta_pdf2.set(archivo)
            self.lbl_info2.config(text=f"...{archivo[-45:]}", fg="blue")

    def seleccionar_carpeta_salida(self):
        # Quitar topmost temporalmente para permitir que el diálogo esté encima
        self.root.attributes('-topmost', False)
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        # Restaurar ventana encima después del diálogo
        self.root.lift()
        self.root.focus_force()
        if carpeta:
            self.ruta_salida.set(carpeta)
            self.lbl_info_salida.config(text=f"...{carpeta[-45:]}", fg="blue")

    def comparar(self):
        if self.procesando:
            return
        
        p1 = self.ruta_pdf1.get()
        p2 = self.ruta_pdf2.get()
        salida = self.ruta_salida.get()
        
        if not p1 or not p2:
            messagebox.showwarning("Atención", "Selecciona ambos archivos primero.")
            return
        
        if not salida:
            messagebox.showwarning("Atención", "Selecciona la carpeta de salida.")
            return
        
        if not os.path.exists(p1) or not os.path.exists(p2):
            messagebox.showerror("Error", "Uno o ambos archivos no existen.")
            return
        
        if not self.poppler_path:
            messagebox.showerror("Error", "Poppler no disponible.")
            return
        
        if not os.path.exists(salida):
            os.makedirs(salida)
        
        self.procesando = True
        self.progress_var.set(0)
        self.status_label.config(text="Procesando comparación...")
        
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
                self.root.after(0, lambda: self.progress_var.set(100))
            
            def cb_estado(msg):
                self.root.after(0, lambda: self.status_label.config(text=msg))
            
            res = fc.procesar_par_de_archivos(
                registro_match,
                self.poppler_path,
                salida,
                callback_progreso=cb_prog,
                callback_estado=cb_estado
            )
            
            self.root.after(0, lambda: self.finalizar(res, salida))
        
        threading.Thread(target=worker, daemon=True).start()

    def finalizar(self, exitoso, ruta):
        self.procesando = False
        self.progress_var.set(100)
        
        if exitoso:
            self.status_label.config(text="✓ Proceso completado exitosamente.")
            messagebox.showinfo("Éxito", f"Comparación guardada en:\n{ruta}")
        else:
            self.status_label.config(text="✗ Error al procesar.")
            messagebox.showerror("Error", "No se pudo completar la comparación.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppComparadorArchivos(root)
    root.mainloop()

