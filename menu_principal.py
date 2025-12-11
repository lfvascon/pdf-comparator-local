import tkinter as tk
from tkinter import messagebox
import sys

# --- IMPORTANTE: CONECTAR CON LAS INTERFACES ---
# Asegúrate de que los archivos estén en la misma carpeta.
try:
    from interfaz_carpetas import AppComparador
except ImportError:
    AppComparador = None

try:
    from interfaz_archivos import AppComparadorArchivos
except ImportError:
    AppComparadorArchivos = None

def abrir_interfaz_archivos():
    if AppComparadorArchivos is None:
        messagebox.showerror("Error", "No se encontró el archivo 'interfaz_archivos.py'.\nAsegúrate de tenerlo en la misma carpeta.")
        return

    # Creamos una ventana secundaria para la interfaz de archivos
    ventana_archivos = tk.Toplevel(root)
    ventana_archivos.transient(root)  # Mantiene encima de la principal pero no de diálogos del sistema
    ventana_archivos.lift()
    ventana_archivos.focus_force()
    
    # Instanciamos la clase AppComparadorArchivos pasándole esta nueva ventana como root
    app = AppComparadorArchivos(ventana_archivos)
    
    # Nota: AppComparadorArchivos se encargará de configurar el título y tamaño de 'ventana_archivos'


def abrir_interfaz_carpetas():
    if AppComparador is None:
        messagebox.showerror("Error", "No se encontró el archivo 'interfaz_carpetas.py'.\nAsegúrate de tenerlo en la misma carpeta.")
        return

    # Creamos una ventana secundaria para la interfaz de carpetas
    ventana_carpetas = tk.Toplevel(root)
    ventana_carpetas.transient(root)  # Mantiene encima de la principal pero no de diálogos del sistema
    ventana_carpetas.lift()
    ventana_carpetas.focus_force()
    
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