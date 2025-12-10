import tkinter as tk

# 1. Crear la ventana principal
root = tk.Tk()
root.title("Comparador pdfs")
root.geometry("300x200") # Tamaño de la ventana: ancho x alto

# 2. Crear el botón de Archivos
btn_archivos = tk.Button(root, text="Archivos", font=("Arial", 12))
btn_archivos.pack(pady=20) # pady agrega espacio vertical

# 3. Crear el botón de Carpetas
btn_carpetas = tk.Button(root, text="Carpetas", font=("Arial", 12))
btn_carpetas.pack(pady=20)

# 4. Iniciar el bucle de la aplicación
root.mainloop()