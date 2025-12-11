import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import os
import threading
import gc

# IMPORTE CRÍTICO: Traemos la lógica del otro archivo
# Asegúrate de que ambos archivos estén en la misma carpeta
import funciones_comparador as fc

class AppComparador:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de PDFs - Interfaz Completa")
        
        # Configurar pantalla completa / maximizada
        if sys.platform == 'win32':
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)
        
        # Variables de estado
        self.ruta_base = tk.StringVar()
        self.ruta_cambio = tk.StringVar()
        self.ruta_salida = tk.StringVar()
        self.resultados = []
        self.datos_destino = {}
        self.poppler_path = None
        self.procesando = False

        self.crear_widgets()
        
        # Verificar Poppler al iniciar
        self.verificar_poppler()

    def crear_widgets(self):
        # Frame Superior (Selección de Carpetas)
        frame_top = tk.Frame(self.root, pady=10)
        frame_top.pack(fill="x", padx=10)

        # Fila 1: Origen
        tk.Label(frame_top, text="Carpeta Origen:").grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(frame_top, textvariable=self.ruta_base, width=70).grid(row=0, column=1, padx=5)
        tk.Button(frame_top, text="📂", command=lambda: self.seleccionar_carpeta(self.ruta_base)).grid(row=0, column=2)

        # Fila 2: Destino
        tk.Label(frame_top, text="Carpeta Destino:").grid(row=1, column=0, padx=5, sticky="w")
        tk.Entry(frame_top, textvariable=self.ruta_cambio, width=70).grid(row=1, column=1, padx=5)
        tk.Button(frame_top, text="📂", command=lambda: self.seleccionar_carpeta(self.ruta_cambio)).grid(row=1, column=2)

        # Fila 3: Salida
        tk.Label(frame_top, text="Guardar Resultados en:").grid(row=2, column=0, padx=5, sticky="w")
        tk.Entry(frame_top, textvariable=self.ruta_salida, width=70).grid(row=2, column=1, padx=5)
        tk.Button(frame_top, text="📂", command=lambda: self.seleccionar_carpeta(self.ruta_salida)).grid(row=2, column=2)

        # Fila 4: Botón Analizar
        tk.Button(frame_top, text="🔍 ANALIZAR COINCIDENCIAS", bg="#4CAF50", fg="white", 
                  font=("Arial", 10, "bold"), command=self.ejecutar_analisis).grid(row=3, column=0, columnspan=3, pady=10)

        # Frame Central (Tabla)
        frame_tabla = tk.Frame(self.root)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("origen", "destino", "similitud")
        self.tree = ttk.Treeview(frame_tabla, columns=columns, show="headings")
        
        self.tree.heading("origen", text="Archivo Origen")
        self.tree.heading("destino", text="Archivo Destino (Editable)")
        self.tree.heading("similitud", text="% / Estado")
        
        self.tree.column("origen", width=450)
        self.tree.column("destino", width=450)
        self.tree.column("similitud", width=120, anchor="center")

        # Colores para estados
        self.tree.tag_configure('match', background='white')
        self.tree.tag_configure('manual', background='#E0F7FA') # Azul claro
        self.tree.tag_configure('error', background='#FFCDD2') # Rojo claro

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Evento doble clic
        self.tree.bind("<Double-1>", self.abrir_editor)

        # Frame Inferior (Progreso)
        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(fill="x", padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame_bottom, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(side="left", padx=5)

        self.status_label = tk.Label(frame_bottom, text="Listo", anchor="w")
        self.status_label.pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(frame_bottom, text="✅ PROCESAR PDFs", bg="#2196F3", fg="white", 
                  font=("Arial", 11, "bold"), command=self.procesar_pdfs, pady=5).pack(side="right", padx=5)

    def verificar_poppler(self):
        """Verifica Poppler usando la función importada."""
        def check():
            self.poppler_path = fc.verificar_poppler_disponible()
            if self.poppler_path:
                self.root.after(0, lambda: self.status_label.config(text=f"Poppler detectado en: {self.poppler_path}"))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error Crítico", 
                    f"No se encontró Poppler.\nEdita 'funciones_comparador.py' y corrige la variable POPPLER_PATH_MANUAL."
                ))
        threading.Thread(target=check, daemon=True).start()

    def seleccionar_carpeta(self, variable_tk):
        # Quitar topmost temporalmente para permitir que el diálogo esté encima
        self.root.attributes('-topmost', False)
        c = filedialog.askdirectory()
        # Restaurar ventana encima después del diálogo
        self.root.lift()
        self.root.focus_force()
        if c: variable_tk.set(c)

    def ejecutar_analisis(self):
        r1 = self.ruta_base.get()
        r2 = self.ruta_cambio.get()

        if not r1 or not r2:
            messagebox.showwarning("Error", "Selecciona ambas carpetas.")
            return

        self.status_label.config(text="Analizando archivos...")
        self.root.update()

        # Llamar a funciones del backend
        res1 = fc.procesar_carpeta(r1)
        self.datos_destino = fc.procesar_carpeta(r2)
        
        self.resultados = fc.comparar_listas_completo(res1, self.datos_destino, umbral=0.5)
        
        # Limpieza
        del res1
        gc.collect()
        
        self.refrescar_tabla()
        n_match = len([r for r in self.resultados if r['tipo'] in ['match', 'manual']])
        self.status_label.config(text=f"Análisis completado: {n_match} coincidencias.")

    def refrescar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, match in enumerate(self.resultados):
            if match is None: continue

            tipo = match['tipo']
            if tipo == 'match': tag = 'match'
            elif tipo == 'manual': tag = 'manual'
            else: tag = 'error'
            
            val_origen = match['origen']['clave']
            val_destino = match['destino']['clave']
            val_score = match['similitud_pct']
            
            if tag == 'error': val_score = "HUÉRFANO"

            self.tree.insert("", "end", iid=i, values=(val_origen, val_destino, val_score), tags=(tag,))

    def abrir_editor(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        idx = int(sel[0])
        reg = self.resultados[idx]

        editor = tk.Toplevel(self.root)
        editor.title("Editar Relación")
        editor.geometry("600x300")
        editor.transient(self.root)  # Mantiene encima de la principal pero no de diálogos del sistema
        editor.lift()
        editor.focus_force()

        tk.Label(editor, text="Origen:", font=("Arial", 10, "bold")).pack(pady=5)
        tk.Label(editor, text=reg['origen']['clave'], fg="blue").pack()

        tk.Label(editor, text="Selecciona Destino Correcto:", font=("Arial", 10, "bold")).pack(pady=10)

        opciones = sorted(list(self.datos_destino.keys()))
        combo = ttk.Combobox(editor, values=opciones, width=70)
        combo.pack(pady=5)
        
        actual = reg['destino']['clave']
        if actual in opciones: combo.set(actual)

        def guardar():
            nuevo = combo.get()
            if not nuevo: return
            datos = self.datos_destino.get(nuevo)
            if datos:
                self.resultados[idx]['destino'] = {"clave": nuevo, "valor": datos["valor"], "ruta": datos["path"]}
                self.resultados[idx]['tipo'] = 'manual'
                self.resultados[idx]['similitud_pct'] = '100% (Manual)'
                self.refrescar_tabla()
                editor.destroy()

        def borrar():
            self.resultados[idx]['destino'] = {"clave": "---", "valor": "", "ruta": ""}
            self.resultados[idx]['tipo'] = 'solo_origen'
            self.resultados[idx]['similitud_pct'] = '0%'
            self.refrescar_tabla()
            editor.destroy()

        f_btn = tk.Frame(editor)
        f_btn.pack(pady=20)
        tk.Button(f_btn, text="💾 GUARDAR", bg="#4CAF50", fg="white", command=guardar).pack(side="left", padx=10)
        tk.Button(f_btn, text="❌ DESVINCULAR", bg="#F44336", fg="white", command=borrar).pack(side="left", padx=10)

    def procesar_pdfs(self):
        if not self.poppler_path:
            messagebox.showerror("Error", "Poppler no disponible.")
            return

        lista_final = [r for r in self.resultados if r and r['tipo'] in ['match', 'manual']]
        if not lista_final:
            messagebox.showwarning("Alerta", "No hay coincidencias válidas.")
            return

        salida = self.ruta_salida.get()
        if not salida:
            messagebox.showwarning("Alerta", "Selecciona carpeta de salida.")
            return
        if not os.path.exists(salida): os.makedirs(salida)

        if self.procesando: return
        self.procesando = True
        self.progress_var.set(0)

        def worker():
            exitosos = 0
            fallidos = 0
            total = len(lista_final)

            def cb_prog(nombre):
                nonlocal exitosos
                exitosos += 1
                p = (exitosos / total) * 100 if total > 0 else 0
                self.root.after(0, lambda: self.progress_var.set(p))

            def cb_estado(msg):
                self.root.after(0, lambda: self.status_label.config(text=msg))

            for i, match in enumerate(lista_final):
                nombre = os.path.basename(match['origen']['ruta'])
                self.root.after(0, lambda p=(i/total)*100: self.progress_var.set(p))
                
                res = fc.procesar_par_de_archivos(
                    match, 
                    self.poppler_path, 
                    salida, 
                    callback_progreso=cb_prog, 
                    callback_estado=cb_estado
                )
                
                if not res:
                    fallidos += 1
                    exitosos += 1 # Contamos como procesado aunque falle para la barra
                
                if (i+1) % 3 == 0: gc.collect()

            self.root.after(0, lambda: self.finalizar(exitosos, fallidos, salida))

        threading.Thread(target=worker, daemon=True).start()

    def finalizar(self, ok, fail, ruta):
        self.procesando = False
        self.progress_var.set(100)
        self.status_label.config(text="Proceso finalizado.")
        messagebox.showinfo("Fin", f"Exitosos: {ok}\nFallidos: {fail}\nGuardado en: {ruta}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppComparador(root)
    root.mainloop()