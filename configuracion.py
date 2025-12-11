"""
Configuration Module.
Manages application settings with a GUI interface.
"""
from __future__ import annotations

import json
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any


@dataclass
class ConfiguracionApp:
    """Application configuration with default values."""
    
    # PDF to Image conversion
    dpi: int = 300
    
    # Batch processing
    batch_size: int = 5
    
    # Image comparison
    min_contour_area: int = 5
    
    # File matching
    similarity_threshold: float = 0.5
    
    # Image alignment
    orb_max_features: int = 10000
    match_ratio: float = 0.20
    min_matches_homography: int = 4

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfiguracionApp:
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Global configuration instance
_config = ConfiguracionApp()
_config_file = Path(__file__).parent / "config.json"


def get_config() -> ConfiguracionApp:
    """Get the current configuration."""
    return _config


def save_config(config: ConfiguracionApp) -> None:
    """Save configuration to file and update global instance."""
    global _config
    _config = config
    
    try:
        with open(_config_file, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


def load_config() -> ConfiguracionApp:
    """Load configuration from file."""
    global _config
    
    if _config_file.exists():
        try:
            with open(_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _config = ConfiguracionApp.from_dict(data)
        except Exception:
            _config = ConfiguracionApp()
    
    return _config


# Load config on module import
load_config()


# ==========================================
# CONFIGURATION OPTIONS
# ==========================================

CONFIG_OPTIONS = {
    "dpi": {
        "label": "Resolución (DPI)",
        "description": "Calidad de conversión PDF → Imagen.\n"
                      "• 150: Rápido, archivos pequeños, calidad media\n"
                      "• 200: Balance velocidad/calidad\n"
                      "• 300: Alta calidad (recomendado)\n"
                      "• 450: Muy alta calidad, más lento\n"
                      "• 600: Máxima calidad, muy lento",
        "values": [150, 200, 300, 450, 600],
        "default": 300,
        "type": "combo"
    },
    "batch_size": {
        "label": "Tamaño de Lote",
        "description": "Páginas procesadas simultáneamente.\n"
                      "• 2: Bajo consumo de RAM, más lento\n"
                      "• 3: Conservador\n"
                      "• 5: Balance (recomendado)\n"
                      "• 8: Más rápido, más RAM\n"
                      "• 10: Máxima velocidad, mucha RAM",
        "values": [2, 3, 5, 8, 10],
        "default": 5,
        "type": "combo"
    },
    "min_contour_area": {
        "label": "Sensibilidad de Detección",
        "description": "Área mínima para detectar cambios.\n"
                      "• 2: Muy sensible (detecta todo, incluye ruido)\n"
                      "• 5: Sensible (recomendado)\n"
                      "• 10: Normal\n"
                      "• 20: Baja sensibilidad\n"
                      "• 50: Solo cambios grandes",
        "values": [2, 5, 10, 20, 50],
        "default": 5,
        "type": "combo"
    },
    "similarity_threshold": {
        "label": "Umbral de Similitud",
        "description": "Porcentaje mínimo para emparejar archivos.\n"
                      "• 30%: Empareja nombres poco similares\n"
                      "• 40%: Flexible\n"
                      "• 50%: Balance (recomendado)\n"
                      "• 70%: Estricto\n"
                      "• 80%: Muy estricto",
        "values": [0.30, 0.40, 0.50, 0.70, 0.80],
        "display_values": ["30%", "40%", "50%", "70%", "80%"],
        "default": 0.50,
        "type": "combo"
    },
    "orb_max_features": {
        "label": "Puntos de Alineación",
        "description": "Puntos de referencia para alinear páginas.\n"
                      "• 5000: Rápido, menos preciso\n"
                      "• 10000: Balance (recomendado)\n"
                      "• 15000: Más preciso\n"
                      "• 20000: Alta precisión, lento\n"
                      "• 30000: Máxima precisión, muy lento",
        "values": [5000, 10000, 15000, 20000, 30000],
        "default": 10000,
        "type": "combo"
    },
    "match_ratio": {
        "label": "Ratio de Coincidencias",
        "description": "Porcentaje de puntos usados para alinear.\n"
                      "• 10%: Solo los mejores, más preciso\n"
                      "• 15%: Conservador\n"
                      "• 20%: Balance (recomendado)\n"
                      "• 30%: Más robusto\n"
                      "• 40%: Muy robusto",
        "values": [0.10, 0.15, 0.20, 0.30, 0.40],
        "display_values": ["10%", "15%", "20%", "30%", "40%"],
        "default": 0.20,
        "type": "combo"
    },
    "min_matches_homography": {
        "label": "Mínimo de Coincidencias",
        "description": "Puntos mínimos para calcular alineación.\n"
                      "• 4: Mínimo matemático (recomendado)\n"
                      "• 6: Más robusto\n"
                      "• 8: Conservador\n"
                      "• 10: Estricto\n"
                      "• 15: Muy estricto",
        "values": [4, 6, 8, 10, 15],
        "default": 4,
        "type": "combo"
    }
}


class InterfazConfiguracion:
    """Configuration interface class."""
    
    def __init__(self, root: tk.Tk | tk.Toplevel) -> None:
        self.root = root
        self.root.title("⚙️ Configuración")
        self.root.geometry("680x600")
        self.root.resizable(False, True)
        
        # Store widget references
        self.widgets: dict[str, ttk.Combobox] = {}
        self.config = get_config()
        self.canvas: tk.Canvas | None = None
        
        self._crear_widgets()
    
    def _crear_widgets(self) -> None:
        """Create all configuration widgets."""
        # Create canvas with scrollbar for scrollable content
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(container)
        canvas = self.canvas
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Scrollable frame inside canvas
        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when window is closed via X button
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Main content frame
        main_frame = tk.Frame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=5)
        
        # Title
        tk.Label(
            main_frame,
            text="⚙️ Configuración del Comparador",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 10))
        
        # Instructions
        tk.Label(
            main_frame,
            text="Selecciona los valores para cada opción. Los cambios se aplican al guardar.",
            font=("Arial", 9),
            fg="gray"
        ).pack(pady=(0, 15))
        
        # Create config sections
        self._crear_seccion(main_frame, "📄 Conversión PDF", ["dpi", "batch_size"])
        self._crear_seccion(main_frame, "🔍 Detección de Cambios", ["min_contour_area"])
        self._crear_seccion(main_frame, "📁 Emparejamiento de Archivos", ["similarity_threshold"])
        self._crear_seccion(main_frame, "🎯 Alineación de Imágenes", 
                           ["orb_max_features", "match_ratio", "min_matches_homography"])
        
        # Buttons frame (fixed at bottom, outside scroll area)
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=10, fill="x", padx=10)
        
        tk.Button(
            frame_botones,
            text="🔄 Restaurar Valores por Defecto",
            font=("Arial", 10),
            command=self._restaurar_defecto,
            width=25
        ).pack(side="left", padx=10)
        
        tk.Button(
            frame_botones,
            text="💾 GUARDAR Y CERRAR",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self._guardar_y_cerrar,
            width=20
        ).pack(side="right", padx=10)
        
        tk.Button(
            frame_botones,
            text="❌ Cancelar",
            font=("Arial", 10),
            command=self._cerrar,
            width=12
        ).pack(side="right", padx=5)
    
    def _crear_seccion(self, parent: tk.Frame, titulo: str, keys: list[str]) -> None:
        """Create a configuration section with multiple options."""
        # Section frame
        section_frame = tk.LabelFrame(parent, text=titulo, font=("Arial", 10, "bold"), padx=10, pady=10)
        section_frame.pack(fill="x", pady=5)
        
        for key in keys:
            self._crear_opcion(section_frame, key)
    
    def _crear_opcion(self, parent: tk.Frame, key: str) -> None:
        """Create a single configuration option."""
        opt = CONFIG_OPTIONS[key]
        
        # Option frame
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=5)
        
        # Left side: Label and description
        left_frame = tk.Frame(frame)
        left_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            left_frame,
            text=opt["label"],
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(anchor="w")
        
        tk.Label(
            left_frame,
            text=opt["description"],
            font=("Arial", 8),
            fg="gray",
            justify="left",
            anchor="w"
        ).pack(anchor="w")
        
        # Right side: Combobox
        right_frame = tk.Frame(frame)
        right_frame.pack(side="right", padx=10)
        
        # Get display values
        display_values = opt.get("display_values", [str(v) for v in opt["values"]])
        
        combo = ttk.Combobox(
            right_frame,
            values=display_values,
            state="readonly",
            width=12,
            font=("Arial", 10)
        )
        combo.pack()
        
        # Set current value
        current_value = getattr(self.config, key)
        try:
            idx = opt["values"].index(current_value)
            combo.current(idx)
        except ValueError:
            # If value not in list, use default
            idx = opt["values"].index(opt["default"])
            combo.current(idx)
        
        # Store reference
        self.widgets[key] = combo
    
    def _restaurar_defecto(self) -> None:
        """Restore all settings to default values."""
        for key, combo in self.widgets.items():
            opt = CONFIG_OPTIONS[key]
            idx = opt["values"].index(opt["default"])
            combo.current(idx)
        
        messagebox.showinfo("Info", "Valores restaurados a los valores por defecto.\nPresiona 'Guardar' para aplicar.")
    
    def _cerrar(self) -> None:
        """Close the window and unbind events."""
        if self.canvas:
            self.canvas.unbind_all("<MouseWheel>")
        self.root.destroy()
    
    def _guardar_y_cerrar(self) -> None:
        """Save configuration and close window."""
        # Collect values
        new_config = {}
        
        for key, combo in self.widgets.items():
            opt = CONFIG_OPTIONS[key]
            idx = combo.current()
            new_config[key] = opt["values"][idx]
        
        # Create and save config
        config = ConfiguracionApp(**new_config)
        save_config(config)
        
        messagebox.showinfo(
            "✅ Guardado",
            "La configuración se ha guardado correctamente.\n"
            "Los cambios se aplicarán en las próximas comparaciones."
        )
        
        self._cerrar()


def abrir_configuracion(parent: tk.Tk | tk.Toplevel | None = None) -> None:
    """Open the configuration window."""
    if parent:
        ventana = tk.Toplevel(parent)
        ventana.transient(parent)
    else:
        ventana = tk.Tk()
    
    ventana.lift()
    ventana.focus_force()
    InterfazConfiguracion(ventana)
    
    if not parent:
        ventana.mainloop()


if __name__ == "__main__":
    abrir_configuracion()

