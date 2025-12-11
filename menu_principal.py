"""
Main Menu Module.
Entry point for the PDF Comparison application.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

# Import interfaces with graceful fallback
try:
    from interfaz_carpetas import AppComparador
except ImportError:
    AppComparador = None

try:
    from interfaz_archivos import AppComparadorArchivos
except ImportError:
    AppComparadorArchivos = None

try:
    from configuracion import abrir_configuracion
except ImportError:
    abrir_configuracion = None


class MainMenu:
    """Main menu application class."""
    
    VERSION = "dic 2025 lfvasconez.ext@acciona.com"
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Menú de Herramientas PDF")
        self.root.geometry("400x350")
        self.root.resizable(True, True)  # Enable maximize and minimize buttons
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Title
        tk.Label(
            self.root, 
            text="Sistema de Comparación PDF", 
            font=("Arial", 16, "bold"), 
            fg="#333"
        ).pack(pady=20)
        
        tk.Label(
            self.root, 
            text="Selecciona el modo de trabajo:", 
            font=("Arial", 10)
        ).pack()

        # Button container
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=20)

        # Individual files button
        tk.Button(
            frame_botones, 
            text="📄 Archivos Individuales", 
            font=("Arial", 11),
            width=25, 
            height=2, 
            command=self._abrir_interfaz_archivos
        ).pack(pady=10)

        # Batch folders button
        tk.Button(
            frame_botones, 
            text="📁 Procesar Carpetas (Lotes)", 
            font=("Arial", 11),
            width=25, 
            height=2, 
            command=self._abrir_interfaz_carpetas
        ).pack(pady=10)

        # Configuration button
        tk.Button(
            frame_botones, 
            text="⚙️ Configuración", 
            font=("Arial", 10),
            width=25, 
            height=1, 
            command=self._abrir_configuracion,
            fg="#666"
        ).pack(pady=5)

        # Footer
        tk.Label(
            self.root, 
            text=f"{self.VERSION} - Edición Local", 
            fg="#999", 
            font=("Arial", 8)
        ).pack(side="bottom", pady=10)

    def _abrir_interfaz_archivos(self) -> None:
        """Open the individual files interface."""
        if AppComparadorArchivos is None:
            messagebox.showerror(
                "Error", 
                "No se encontró el archivo 'interfaz_archivos.py'.\n"
                "Asegúrate de tenerlo en la misma carpeta."
            )
            return

        ventana = tk.Toplevel(self.root)
        ventana.transient(self.root)
        ventana.lift()
        ventana.focus_force()
        AppComparadorArchivos(ventana)

    def _abrir_interfaz_carpetas(self) -> None:
        """Open the folder batch interface."""
        if AppComparador is None:
            messagebox.showerror(
                "Error", 
                "No se encontró el archivo 'interfaz_carpetas.py'.\n"
                "Asegúrate de tenerlo en la misma carpeta."
            )
            return

        ventana = tk.Toplevel(self.root)
        ventana.transient(self.root)
        ventana.lift()
        ventana.focus_force()
        AppComparador(ventana)

    def _abrir_configuracion(self) -> None:
        """Open the configuration interface."""
        if abrir_configuracion is None:
            messagebox.showerror(
                "Error", 
                "No se encontró el archivo 'configuracion.py'.\n"
                "Asegúrate de tenerlo en la misma carpeta."
            )
            return
        
        abrir_configuracion(self.root)


def main() -> None:
    """Application entry point."""
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()


if __name__ == "__main__":
    # Fix for PyInstaller multiprocessing on Windows
    import sys
    import multiprocessing
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        multiprocessing.freeze_support()
    main()
