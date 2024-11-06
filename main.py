import os
import json
from tkinter import Tk, filedialog, Listbox, Label, Button, END, Toplevel, Entry, StringVar, messagebox, Frame
from PIL import Image, ImageTk
from tkinter import LEFT, RIGHT, BOTH, Y


class GIFDataExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Data Extractor")
        self.root.configure(bg="black")  # Fondo negro de la ventana principal

        # Diccionarios para almacenar metadata y rutas
        self.file_metadata = {}
        self.metadata_file = "metadata.json"
        self.file_paths = {}

        # Inicializar índice y lista de fotogramas
        self.current_frame_index = 0
        self.frames = []

        # Etiqueta para el GIF (será usada en una ventana emergente)
        self.gif_label = Label(root)

        # Verificar si es la primera ejecución
        if os.path.exists(self.metadata_file):
            self.load_metadata()
        else:
            messagebox.showinfo("Primera vez", "Es la primera vez que abres la aplicación. Selecciona una carpeta "
                                               "para comenzar.")

        # Crear un contenedor para dividir la interfaz en paneles izquierdo y derecho
        main_frame = Frame(root, bg="black")
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Crear el Listbox a la izquierda
        self.gif_list = Listbox(main_frame, width=50, height=20, bg="gray25", fg="white", font=("Arial", 12))
        self.gif_list.pack(side=LEFT, fill=Y, padx=(0, 10))  # Espacio entre el Listbox y los botones

        # Crear un contenedor para los botones a la derecha
        button_frame = Frame(main_frame, bg="black")
        button_frame.pack(side=RIGHT, fill=Y)

        # Configuración de botones con estilo verde y tamaño aumentado
        button_style = {
            "bg": "green",
            "fg": "white",
            "font": ("Arial", 14, "bold"),
            "width": 15,
            "height": 2
        }

        # Crear los botones y aplicarlos al frame derecho
        self.load_button = Button(button_frame, text="Cargar Carpeta", command=self.load_folder, **button_style)
        self.save_button = Button(button_frame, text="Guardar Metadata", command=self.save_metadata, **button_style)
        self.edit_button = Button(button_frame, text="Editar Metadata", command=self.edit_metadata, **button_style)

        # Ubicar los botones en el panel derecho con espacio entre ellos
        self.load_button.pack(pady=(0, 10))  # Espacio superior para el primer botón
        self.save_button.pack(pady=(0, 10))  # Espacio entre los botones
        self.edit_button.pack(pady=(0, 10))  # Espacio inferior para el último botón

        # Evento de selección en el Listbox
        self.gif_list.bind('<<ListboxSelect>>', self.display_metadata)

    def load_metadata(self):
        try:
            with open(self.metadata_file, 'r') as file:
                self.file_metadata = json.load(file)
            print(f"Metadata loaded from {self.metadata_file}")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error loading metadata from {self.metadata_file}")
            self.file_metadata = {}

    def analyze_gif(self, file_path):
        metadata = {}
        try:
            with open(file_path, 'rb') as file:
                # Número de versión
                metadata['version'] = file.read(6).decode('utf-8')

                # Tamaño de imagen
                width = int.from_bytes(file.read(2), 'little')
                height = int.from_bytes(file.read(2), 'little')
                metadata['size'] = f"{width}x{height}"

                # Cantidad de colores y color de fondo
                packed_fields = int.from_bytes(file.read(1), 'little')
                color_flag = (packed_fields & 0b10000000) >> 7
                color_bits = (packed_fields & 0b01110000) >> 4
                color_count = 2 ** (color_bits + 1) if color_flag else 0
                metadata['colors'] = color_count
                metadata['background_color'] = int.from_bytes(file.read(1), 'little')

                # Tipo de compresión
                metadata['compression_type'] = "LZW"

                # Formato numérico
                metadata['numeric_format'] = "N/A"

                # Cantidad de imágenes
                metadata['image_count'] = 1

                # Guardar los metadatos en el diccionario principal
                self.file_metadata[file_path] = metadata
                print(f"Metadata for {file_path}: {metadata}")

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def search_gif_files(self, folder_path):
        gif_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.gif'):
                    gif_path = os.path.join(root, file)
                    self.analyze_gif(gif_path)
                    gif_files.append(file)
                    self.file_paths[file] = gif_path  # Guardar la ruta completa en un diccionario
        return gif_files

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            gif_files = self.search_gif_files(folder_path)
            self.gif_list.delete(0, END)
            for gif in gif_files:
                self.gif_list.insert(END, gif)

    def display_metadata(self, event):
        selection = self.gif_list.curselection()
        if selection:
            gif_name = self.gif_list.get(selection[0])
            gif_path = self.file_paths[gif_name]  # Obtener la ruta completa del diccionario
            metadata = self.file_metadata.get(gif_path, {})

            # Formatear los datos según los campos requeridos
            info_text = (
                f"Número de versión: {metadata.get('version', 'N/A')}\n"
                f"Tamaño de imagen: {metadata.get('size', 'N/A')}\n"
                f"Cantidad de colores: {metadata.get('colors', 'N/A')}\n"
                f"Tipo de compresión de imagen: {metadata.get('compression_type', 'N/A')}\n"
                f"Formato numérico: {metadata.get('numeric_format', 'N/A')}\n"
                f"Color de fondo: {metadata.get('background_color', 'N/A')}\n"
                f"Cantidad de imágenes que contiene: {metadata.get('image_count', 'N/A')}\n"
                f"Fecha de creación: {metadata.get('creation_date', 'N/A')}\n"
                f"Fecha de modificación: {metadata.get('modification_date', 'N/A')}\n"
                f"Comentarios agregados: {metadata.get('comments', 'N/A')}"
            )

            # Crear ventana emergente personalizada para mostrar texto y GIF
            popup = Toplevel(self.root)
            popup.title("Metadatos del GIF")

            # Crear un marco contenedor para organizar texto e imagen en la misma fila
            content_frame = Frame(popup)
            content_frame.pack(padx=10, pady=10)

            # Label para mostrar los metadatos a la izquierda
            info_label = Label(content_frame, text=info_text, justify="left")
            info_label.grid(row=0, column=0, padx=(0, 10))

            # Label para mostrar el GIF a la derecha
            self.gif_label = Label(content_frame)
            self.gif_label.grid(row=0, column=1)

            # Cargar y mostrar el GIF
            try:
                img = Image.open(gif_path)
                self.frames = []
                for i in range(img.n_frames):
                    img.seek(i)
                    frame = ImageTk.PhotoImage(img.copy())
                    self.frames.append(frame)
                self.current_frame_index = 0

                # Iniciar la animación solo si hay fotogramas cargados
                if self.frames:
                    self.animate_gif()
            except Exception as e:
                print(f"Error al cargar el GIF: {e}")

    def animate_gif(self):
        # Controlar la animación del GIF
        if self.frames:
            frame = self.frames[self.current_frame_index]
            self.gif_label.configure(image=frame)
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            # Llamar a la función después de 100 ms para crear una animación
            self.root.after(100, self.animate_gif)

    def save_metadata(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if save_path:
            with open(save_path, 'w') as file:
                json.dump(self.file_metadata, file, indent=4)
            print(f"Metadata saved to {save_path}")

    def edit_metadata(self):
        selection = self.gif_list.curselection()
        if selection:
            gif_name = self.gif_list.get(selection[0])
            gif_path = self.file_paths[gif_name]
            metadata = self.file_metadata.get(gif_path)
            if metadata:
                EditWindow(self.root, gif_path, metadata, self)
            else:
                messagebox.showinfo("Información", "No hay metadatos disponibles para editar")


class EditWindow:
    def __init__(self, master, file_path, metadata, appdata):
        self.top = Toplevel(master)
        self.top.title("Editar Metadata")
        self.file_path = file_path
        self.app = appdata
        self.metadata = metadata

        # Crear entradas para cada campo de metadatos
        Label(self.top, text="Número de versión:").grid(row=0, column=0)
        self.version_var = StringVar(value=metadata.get('version', 'N/A'))
        Entry(self.top, textvariable=self.version_var).grid(row=0, column=1)

        Label(self.top, text="Tamaño de imagen:").grid(row=1, column=0)
        self.size_var = StringVar(value=metadata.get('size', 'N/A'))
        Entry(self.top, textvariable=self.size_var).grid(row=1, column=1)

        Label(self.top, text="Cantidad de colores:").grid(row=2, column=0)
        self.colors_var = StringVar(value=metadata.get('colors', 'N/A'))
        Entry(self.top, textvariable=self.colors_var).grid(row=2, column=1)

        Label(self.top, text="Tipo de compresión de imagen:").grid(row=3, column=0)
        self.compression_var = StringVar(value=metadata.get('compression_type', 'N/A'))
        Entry(self.top, textvariable=self.compression_var).grid(row=3, column=1)

        Label(self.top, text="Formato numérico:").grid(row=4, column=0)
        self.numeric_format_var = StringVar(value=metadata.get('numeric_format', 'N/A'))
        Entry(self.top, textvariable=self.numeric_format_var).grid(row=4, column=1)

        Label(self.top, text="Color de fondo:").grid(row=5, column=0)
        self.background_color_var = StringVar(value=metadata.get('background_color', 'N/A'))
        Entry(self.top, textvariable=self.background_color_var).grid(row=5, column=1)

        Label(self.top, text="Cantidad de imágenes que contiene:").grid(row=6, column=0)
        self.image_count_var = StringVar(value=metadata.get('image_count', 'N/A'))
        Entry(self.top, textvariable=self.image_count_var).grid(row=6, column=1)

        Label(self.top, text="Fecha de creación:").grid(row=7, column=0)
        self.creation_date_var = StringVar(value=metadata.get('creation_date', 'N/A'))
        Entry(self.top, textvariable=self.creation_date_var).grid(row=7, column=1)

        Label(self.top, text="Fecha de modificación:").grid(row=8, column=0)
        self.modification_date_var = StringVar(value=metadata.get('modification_date', 'N/A'))
        Entry(self.top, textvariable=self.modification_date_var).grid(row=8, column=1)

        Label(self.top, text="Comentarios agregados:").grid(row=9, column=0)
        self.comments_var = StringVar(value=metadata.get('comments', 'N/A'))
        Entry(self.top, textvariable=self.comments_var).grid(row=9, column=1)

        # Botón para guardar los cambios
        Button(self.top, text="Guardar Cambios", command=self.save_changes).grid(row=10, column=0, columnspan=2)

    def save_changes(self):
        # Actualizar metadatos con los valores editados
        new_data = {
            'version': self.version_var.get(),
            'size': self.size_var.get(),
            'colors': self.colors_var.get(),
            'compression_type': self.compression_var.get(),
            'numeric_format': self.numeric_format_var.get(),
            'background_color': self.background_color_var.get(),
            'image_count': self.image_count_var.get(),
            'creation_date': self.creation_date_var.get(),
            'modification_date': self.modification_date_var.get(),
            'comments': self.comments_var.get()
        }
        self.app.file_metadata[self.file_path].update(new_data)
        messagebox.showinfo("Información", "Cambios guardados con éxito")
        self.top.destroy()


if __name__ == "__main__":
    raiz = Tk()
    app = GIFDataExtractorApp(raiz)
    raiz.mainloop()
