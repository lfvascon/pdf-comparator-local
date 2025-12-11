"""
Individual File Comparison Interface Module.
Provides GUI for comparing two individual PDF files.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import funciones_comparador as fc


class AppComparadorArchivos:
    """Application class for individual PDF file comparison."""
    
    def __init__(self, root: tk.Tk | tk.Toplevel) -> None:
        self.root = root
        self.root.title("Comparación de Archivos PDF (Modo Individual)")
        self.root.geometry("550x450")
        
        # State variables
        self.ruta_pdf1 = tk.StringVar()
        self.ruta_pdf2 = tk.StringVar()
        self.ruta_salida = tk.StringVar()
        self.pymupdf_disponible = False
        self.procesando = False

        self._crear_widgets()
        self._verificar_pymupdf()

    def _crear_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Title
        tk.Label(
            self.root, 
            text="Comparación Individual de PDFs", 
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Selection frame
        frame_seleccion = tk.Frame(self.root)
        frame_seleccion.pack(fill="x", padx=20, pady=5)

        # File selection frames
        self._crear_frame_archivo(
            frame_seleccion, 
            "Archivo Origen:", 
            "📄 Seleccionar Original",
            self._seleccionar_pdf_1,
            "lbl_info1"
        )
        
        self._crear_frame_archivo(
            frame_seleccion, 
            "Archivo Destino:", 
            "📄 Seleccionar Nuevo",
            self._seleccionar_pdf_2,
            "lbl_info2"
        )
        
        self._crear_frame_archivo(
            frame_seleccion, 
            "Carpeta de Salida:", 
            "📂 Seleccionar Carpeta",
            self._seleccionar_carpeta_salida,
            "lbl_info_salida"
        )

        # Process button
        tk.Button(
            self.root, 
            text="⚡ PROCESAR COMPARACIÓN", 
            bg="#4CAF50", 
            fg="white",
            font=("Arial", 11, "bold"), 
            command=self._comparar, 
            height=2
        ).pack(pady=15, fill="x", padx=50)

        # Progress frame
        frame_progreso = tk.Frame(self.root)
        frame_progreso.pack(fill="x", padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame_progreso, 
            variable=self.progress_var, 
            maximum=100, 
            length=400
        )
        self.progress_bar.pack(side="left", padx=5)
        
        self.status_label = tk.Label(frame_progreso, text="Listo", anchor="w")
        self.status_label.pack(side="left", padx=5, fill="x", expand=True)

    def _crear_frame_archivo(
        self, 
        parent: tk.Frame, 
        label_text: str, 
        button_text: str,
        command: callable,
        label_attr: str
    ) -> None:
        """Create a file/folder selection frame."""
        frame = tk.Frame(parent, relief="groove", bd=2)
        frame.pack(fill="x", pady=5)
        
        tk.Label(frame, text=label_text, font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        tk.Button(frame, text=button_text, command=command).pack(pady=2)
        
        label = tk.Label(frame, text="Sin selección", fg="gray", wraplength=500)
        label.pack(pady=2)
        setattr(self, label_attr, label)

    def _verificar_pymupdf(self) -> None:
        """Verify PyMuPDF availability in background thread."""
        def check() -> None:
            self.pymupdf_disponible = fc.verificar_pymupdf_disponible()
            msg = "✓ PyMuPDF disponible" if self.pymupdf_disponible else "⚠️ PyMuPDF no detectado"
            self.root.after(0, lambda: self.status_label.config(text=msg))
            
            if not self.pymupdf_disponible:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error Crítico",
                    "PyMuPDF no está instalado.\nInstálalo con: pip install PyMuPDF"
                ))
        
        threading.Thread(target=check, daemon=True).start()

    def _seleccionar_archivo_pdf(self, variable: tk.StringVar, label: tk.Label, title: str) -> None:
        """Generic method for PDF file selection."""
        self.root.attributes('-topmost', False)
        archivo = filedialog.askopenfilename(
            title=title,
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        self.root.lift()
        self.root.focus_force()
        
        if archivo:
            variable.set(archivo)
            # Show truncated path
            display_text = f"...{archivo[-45:]}" if len(archivo) > 45 else archivo
            label.config(text=display_text, fg="blue")

    def _seleccionar_pdf_1(self) -> None:
        """Open dialog to select the original PDF."""
        self._seleccionar_archivo_pdf(
            self.ruta_pdf1, 
            self.lbl_info1, 
            "Seleccionar PDF Original"
        )

    def _seleccionar_pdf_2(self) -> None:
        """Open dialog to select the new PDF."""
        self._seleccionar_archivo_pdf(
            self.ruta_pdf2, 
            self.lbl_info2, 
            "Seleccionar PDF Nuevo"
        )

    def _seleccionar_carpeta_salida(self) -> None:
        """Open dialog to select output folder."""
        self.root.attributes('-topmost', False)
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        self.root.lift()
        self.root.focus_force()
        
        if carpeta:
            self.ruta_salida.set(carpeta)
            display_text = f"...{carpeta[-45:]}" if len(carpeta) > 45 else carpeta
            self.lbl_info_salida.config(text=display_text, fg="blue")

    def _comparar(self) -> None:
        """Execute the PDF comparison."""
        if self.procesando:
            return
        
        p1 = self.ruta_pdf1.get()
        p2 = self.ruta_pdf2.get()
        salida = self.ruta_salida.get()
        
        # Validation
        if not p1 or not p2:
            messagebox.showwarning("Atención", "Selecciona ambos archivos primero.")
            return
        
        if not salida:
            messagebox.showwarning("Atención", "Selecciona la carpeta de salida.")
            return
        
        if not os.path.exists(p1) or not os.path.exists(p2):
            messagebox.showerror("Error", "Uno o ambos archivos no existen.")
            return
        
        if not self.pymupdf_disponible:
            messagebox.showerror("Error", "PyMuPDF no disponible.\nInstálalo con: pip install PyMuPDF")
            return
        
        os.makedirs(salida, exist_ok=True)
        
        self.procesando = True
        self.progress_var.set(0)
        self.status_label.config(text="Procesando comparación...")
        
        # Create match record
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
        
        def worker() -> None:
            def cb_prog(nombre: str) -> None:
                self.root.after(0, lambda: self.progress_var.set(100))
            
            def cb_estado(msg: str) -> None:
                self.root.after(0, lambda: self.status_label.config(text=msg))
            
            resultado = fc.procesar_par_de_archivos(
                registro_match,
                salida,
                callback_progreso=cb_prog,
                callback_estado=cb_estado
            )
            
            self.root.after(0, lambda: self._finalizar(resultado, salida))
        
        threading.Thread(target=worker, daemon=True).start()

    def _finalizar(self, exitoso: bool, ruta: str) -> None:
        """Finalize processing and show result."""
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
