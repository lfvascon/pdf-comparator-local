"""
Folder Comparison Interface Module.
Provides GUI for batch PDF comparison between two folders.
"""
from __future__ import annotations

import gc
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

import funciones_comparador as fc

if TYPE_CHECKING:
    from tkinter import Event


class AppComparador:
    """Main application class for folder-based PDF comparison."""
    
    def __init__(self, root: tk.Tk | tk.Toplevel) -> None:
        self.root = root
        self.root.title("Comparador de PDFs - Interfaz Completa")
        
        # Configure window - MUST be done first
        self._configure_window()
        
        # State variables
        self.ruta_base = tk.StringVar()
        self.ruta_cambio = tk.StringVar()
        self.ruta_salida = tk.StringVar()
        self.resultados: list[dict] = []
        self.datos_destino: dict[str, dict[str, str]] = {}
        self.pymupdf_disponible = False
        self.procesando = False

        self._crear_widgets()
        self._verificar_pymupdf()
        
        # Update layout after widgets are created
        self.root.update_idletasks()

    def _configure_window(self) -> None:
        """Configure window size and properties."""
        # Enable maximize and minimize buttons
        self.root.resizable(True, True)
        # Maximize window to full screen
        self.root.after_idle(self._maximize_to_fullscreen)
    
    def _maximize_to_fullscreen(self) -> None:
        """Maximize window to full screen after layout is complete."""
        if sys.platform == 'win32':
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)
        # Force update to ensure bottom frame is visible
        self.root.update_idletasks()

    def _crear_widgets(self) -> None:
        """Create and layout all GUI widgets using grid for better control."""
        # Configure root grid weights
        self.root.grid_rowconfigure(1, weight=1)  # Middle row expands
        self.root.grid_columnconfigure(0, weight=1)
        
        # Top frame (row 0) - contains folder selection AND progress/button
        self._crear_frame_superior()
        
        # Middle frame (row 1) - expandable table
        self._crear_frame_tabla()

    def _crear_frame_superior(self) -> None:
        """Create the top frame with folder selection inputs and progress/process controls."""
        frame_top = tk.Frame(self.root, pady=10)
        frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame_top.grid_columnconfigure(0, weight=1)  # Left side expands
        frame_top.grid_columnconfigure(1, weight=0)  # Right side fixed

        # Left side: Folder selection
        frame_left = tk.Frame(frame_top)
        frame_left.grid(row=0, column=0, sticky="w", padx=(0, 20))

        # Row configuration
        labels = ["Carpeta Origen:", "Carpeta Destino:", "Guardar Resultados en:"]
        variables = [self.ruta_base, self.ruta_cambio, self.ruta_salida]

        for row, (label_text, var) in enumerate(zip(labels, variables)):
            tk.Label(frame_left, text=label_text).grid(row=row, column=0, padx=5, sticky="w")
            tk.Entry(frame_left, textvariable=var, width=50).grid(row=row, column=1, padx=5)
            tk.Button(
                frame_left, 
                text="📂", 
                command=lambda v=var: self._seleccionar_carpeta(v)
            ).grid(row=row, column=2)

        # Analyze button
        tk.Button(
            frame_left, 
            text="🔍 ANALIZAR COINCIDENCIAS", 
            bg="#4CAF50", 
            fg="white",
            font=("Arial", 10, "bold"), 
            command=self._ejecutar_analisis
        ).grid(row=3, column=0, columnspan=3, pady=10, sticky="w")

        # Right side: Progress bar and process button
        frame_right = tk.Frame(frame_top)
        frame_right.grid(row=0, column=1, sticky="ne", padx=10)

        # Progress bar and status
        progress_frame = tk.Frame(frame_right)
        progress_frame.pack(fill="x", pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100, 
            length=300,
            mode='determinate'
        )
        self.progress_bar.pack(side="top", pady=2)

        self.status_label = tk.Label(progress_frame, text="Listo", anchor="w", font=("Arial", 9))
        self.status_label.pack(side="top", fill="x")

        # Process button
        tk.Button(
            frame_right, 
            text="✅ PROCESAR PDFs", 
            bg="#2196F3", 
            fg="white",
            font=("Arial", 11, "bold"), 
            command=self._procesar_pdfs, 
            pady=8,
            width=18,
            cursor="hand2"
        ).pack(side="top", pady=5)

    def _crear_frame_tabla(self) -> None:
        """Create the central frame with results table."""
        frame_tabla = tk.Frame(self.root)
        frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columns = ("origen", "destino", "similitud")
        self.tree = ttk.Treeview(frame_tabla, columns=columns, show="headings")
        
        # Configure columns
        headings = [
            ("origen", "Archivo Origen", 450),
            ("destino", "Archivo Destino (Editable)", 450),
            ("similitud", "% / Estado", 120)
        ]
        for col_id, text, width in headings:
            self.tree.heading(col_id, text=text)
            anchor = "center" if col_id == "similitud" else "w"
            self.tree.column(col_id, width=width, anchor=anchor)

        # Configure tags for row colors
        self.tree.tag_configure('match', background='white')
        self.tree.tag_configure('manual', background='#E0F7FA')
        self.tree.tag_configure('error', background='#FFCDD2')

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Double-click event
        self.tree.bind("<Double-1>", self._abrir_editor)


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

    def _seleccionar_carpeta(self, variable_tk: tk.StringVar) -> None:
        """Open folder selection dialog."""
        self.root.attributes('-topmost', False)
        carpeta = filedialog.askdirectory()
        self.root.lift()
        self.root.focus_force()
        
        if carpeta:
            variable_tk.set(carpeta)

    def _ejecutar_analisis(self) -> None:
        """Execute folder analysis and find file matches."""
        r1, r2 = self.ruta_base.get(), self.ruta_cambio.get()

        if not r1 or not r2:
            messagebox.showwarning("Error", "Selecciona ambas carpetas.")
            return

        self.status_label.config(text="Analizando archivos...")
        self.root.update()

        # Process folders
        res1 = fc.procesar_carpeta(r1)
        self.datos_destino = fc.procesar_carpeta(r2)
        self.resultados = fc.comparar_listas_completo(res1, self.datos_destino, umbral=0.5)
        
        self._refrescar_tabla()
        n_match = sum(1 for r in self.resultados if r['tipo'] in ('match', 'manual'))
        self.status_label.config(text=f"Análisis completado: {n_match} coincidencias.")

    def _refrescar_tabla(self) -> None:
        """Refresh the results table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        tag_map = {'match': 'match', 'manual': 'manual'}
        
        for i, match in enumerate(self.resultados):
            if match is None:
                continue

            tag = tag_map.get(match['tipo'], 'error')
            val_score = "HUÉRFANO" if tag == 'error' else match['similitud_pct']

            self.tree.insert(
                "", "end", 
                iid=i, 
                values=(match['origen']['clave'], match['destino']['clave'], val_score), 
                tags=(tag,)
            )

    def _abrir_editor(self, event: Event) -> None:
        """Open the relationship editor dialog."""
        sel = self.tree.selection()
        if not sel:
            return
        
        idx = int(sel[0])
        reg = self.resultados[idx]

        editor = tk.Toplevel(self.root)
        editor.title("Editar Relación")
        editor.geometry("600x300")
        editor.resizable(True, True)  # Enable maximize and minimize buttons
        editor.transient(self.root)
        editor.lift()
        editor.focus_force()

        tk.Label(editor, text="Origen:", font=("Arial", 10, "bold")).pack(pady=5)
        tk.Label(editor, text=reg['origen']['clave'], fg="blue").pack()

        tk.Label(editor, text="Selecciona Destino Correcto:", font=("Arial", 10, "bold")).pack(pady=10)

        opciones = sorted(self.datos_destino.keys())
        combo = ttk.Combobox(editor, values=opciones, width=70)
        combo.pack(pady=5)
        
        if reg['destino']['clave'] in opciones:
            combo.set(reg['destino']['clave'])

        def guardar() -> None:
            nuevo = combo.get()
            if not nuevo:
                return
            datos = self.datos_destino.get(nuevo)
            if datos:
                self.resultados[idx]['destino'] = {
                    "clave": nuevo, 
                    "valor": datos["valor"], 
                    "ruta": datos["path"]
                }
                self.resultados[idx]['tipo'] = 'manual'
                self.resultados[idx]['similitud_pct'] = '100% (Manual)'
                self._refrescar_tabla()
                editor.destroy()

        def borrar() -> None:
            self.resultados[idx]['destino'] = {"clave": "---", "valor": "", "ruta": ""}
            self.resultados[idx]['tipo'] = 'solo_origen'
            self.resultados[idx]['similitud_pct'] = '0%'
            self._refrescar_tabla()
            editor.destroy()

        frame_btn = tk.Frame(editor)
        frame_btn.pack(pady=20)
        tk.Button(frame_btn, text="💾 GUARDAR", bg="#4CAF50", fg="white", command=guardar).pack(side="left", padx=10)
        tk.Button(frame_btn, text="❌ DESVINCULAR", bg="#F44336", fg="white", command=borrar).pack(side="left", padx=10)

    def _procesar_pdfs(self) -> None:
        """Process all matched PDFs and generate comparisons."""
        if not self.pymupdf_disponible:
            messagebox.showerror("Error", "PyMuPDF no disponible.\nInstálalo con: pip install PyMuPDF")
            return

        lista_final = [r for r in self.resultados if r and r['tipo'] in ('match', 'manual')]
        if not lista_final:
            messagebox.showwarning("Alerta", "No hay coincidencias válidas.")
            return

        salida = self.ruta_salida.get()
        if not salida:
            messagebox.showwarning("Alerta", "Selecciona carpeta de salida.")
            return
        
        os.makedirs(salida, exist_ok=True)

        if self.procesando:
            return
        
        self.procesando = True
        self.progress_var.set(0)

        def worker() -> None:
            exitosos = 0
            fallidos = 0
            total = len(lista_final)

            def cb_prog(nombre: str) -> None:
                nonlocal exitosos
                exitosos += 1
                progress = (exitosos / total) * 100 if total > 0 else 0
                self.root.after(0, lambda: self.progress_var.set(progress))

            def cb_estado(msg: str) -> None:
                self.root.after(0, lambda: self.status_label.config(text=msg))

            for i, match in enumerate(lista_final):
                self.root.after(0, lambda p=(i / total) * 100: self.progress_var.set(p))
                
                if not fc.procesar_par_de_archivos(
                    match, salida, 
                    callback_progreso=cb_prog, 
                    callback_estado=cb_estado
                ):
                    fallidos += 1
                    exitosos += 1
                
                if (i + 1) % 3 == 0:
                    gc.collect()

            self.root.after(0, lambda: self._finalizar(exitosos, fallidos, salida))

        threading.Thread(target=worker, daemon=True).start()

    def _finalizar(self, ok: int, fail: int, ruta: str) -> None:
        """Finalize processing and show results."""
        self.procesando = False
        self.progress_var.set(100)
        self.status_label.config(text="Proceso finalizado.")
        messagebox.showinfo("Fin", f"Exitosos: {ok}\nFallidos: {fail}\nGuardado en: {ruta}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppComparador(root)
    root.mainloop()
