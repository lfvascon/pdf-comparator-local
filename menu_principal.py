import tkinter as tk
from tkinter import filedialog, messagebox
import sys

# --- IMPORTANTE: CONECTAR CON LA INTERFAZ DE CARPETAS ---
# Asegúrate de que el archivo 'interfaz_carpetas.py' esté en la misma carpeta.
try:
    from interfaz_carpetas import AppComparador
except ImportError:
    AppComparador = None

def abrir_interfaz_archivos():
    # Crear una ventana secundaria (Toplevel)
    ventana_pdf = tk.Toplevel(root)
    ventana_pdf.title("Comparación de Archivos PDF (Modo Individual)")
    ventana_pdf.geometry("500x400")

    # Variables
    ruta_pdf1 = tk.StringVar()
    ruta_pdf2 = tk.StringVar()

    def seleccionar_pdf_1():
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Original",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            ruta_pdf1.set(archivo)
            lbl_info1.config(text=f"...{archivo[-40:]}", fg="blue")

    def seleccionar_pdf_2():
        archivo = filedialog.askopenfilename(
            title="Seleccionar PDF Nuevo",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            ruta_pdf2.set(archivo)
            lbl_info2.config(text=f"...{archivo[-40:]}", fg="blue")

    def comparar():
        p1 = ruta_pdf1.get()
        p2 = ruta_pdf2.get()
        
        if not p1 or not p2:
            messagebox.showwarning("Atención", "Selecciona ambos archivos primero.")
            return
            
        messagebox.showinfo("Info", "Aquí se conectaría la lógica de 'procesar_par_de_archivos' individualmente.")
        # Aquí podrías llamar a funciones_comparador.procesar_par_de_archivos(...) si quisieras integrarlo.

    # --- UI Archivos ---
    tk.Label(ventana_pdf, text="Comparación Individual", font=("Arial", 12, "bold")).pack(pady=15)

    frame_1 = tk.Frame(ventana_pdf, relief="groove", bd=2)
    frame_1.pack(fill="x", padx=20, pady=5)
    tk.Button(frame_1, text="1. Seleccionar Original", command=seleccionar_pdf_1).pack(pady=5)
    lbl_info1 = tk.Label(frame_1, text="Sin selección", fg="gray")
    lbl_info1.pack(pady=2)

    frame_2 = tk.Frame(ventana_pdf, relief="groove", bd=2)
    frame_2.pack(fill="x", padx=20, pady=5)
    tk.Button(frame_2, text="2. Seleccionar Nuevo", command=seleccionar_pdf_2).pack(pady=5)
    lbl_info2 = tk.Label(frame_2, text="Sin selección", fg="gray")
    lbl_info2.pack(pady=2)

    tk.Button(ventana_pdf, text="⚡ EJECUTAR COMPARACIÓN", bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), command=comparar, height=2).pack(pady=20, fill="x", padx=50)


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