import os
import json
import time
from tkinter import Tk, filedialog, Listbox, Label, Button, END, Toplevel, Entry, StringVar, messagebox


class GIFDataExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Data Extractor")
        self.file_metadata = {}
        self.metadata_file = "metadata.json"

        # Verificar si ya se ha abierto antes
        if os.path.exists(self.metadata_file):
            self.load_metadata()
        else:
            messagebox.showinfo("Primera vez",
                                "Es la primera vez que abres la aplicación. Selecciona una carpeta para comenzar.")

        # Widgets principales
        self.gif_list = Listbox(root, width=50, height=20)
        self.label = Label(root, text="Información del GIF seleccionada:")
        self.info_label = Label(root, text="")
        self.load_button = Button(root, text="Cargar Carpeta", command=self.load_folder)
        self.save_button = Button(root, text="Guardar Metadata", command=self.save_metadata)
        self.edit_button = Button(root, text="Editar Metadata", command=self.edit_metadata)

        # Ubicación de widgets
        self.load_button.pack()
        self.gif_list.pack()
        self.label.pack()
        self.info_label.pack()
        self.save_button.pack()
        self.edit_button.pack()

        # Evento de selección de GIF
        self.gif_list.bind('<<ListboxSelect>>', self.display_metadata)

    # Cargar los metadatos si el archivo existe
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
                metadata['compression_type'] = "LZW"  # GIF usa LZW por estándar, no requiere cambio.

                # Formato numérico (sin datos en GIF, se establece como "N/A")
                metadata['numeric_format'] = "N/A"

                # Cantidad de imágenes en GIF
                image_count = 0
                while True:
                    block = file.read(1)
                    if block == b'\x2C':  # El bloque de imagen comienza con byte 0x2C
                        image_count += 1
                    elif block == b'\x3B':  # Byte 0x3B indica el fin del archivo GIF
                        break
                    elif not block:
                        break  # Final de archivo inesperado
                metadata['image_count'] = image_count

                # Fecha de creación y modificación del sistema de archivos
                metadata['creation_date'] = time.ctime(os.path.getctime(file_path))
                metadata['modification_date'] = time.ctime(os.path.getmtime(file_path))

                # Bloque de comentarios
                file.seek(13)  # Nos desplazamos después de los encabezados iniciales
                comments = []
                while True:
                    block = file.read(1)
                    if block == b'\x21':  # El bloque de extensión comienza con 0x21
                        label = file.read(1)
                        if label == b'\xFE':  # El bloque de comentarios tiene una etiqueta 0xFE
                            while True:
                                sub_block_size = ord(file.read(1))
                                if sub_block_size == 0:
                                    break
                                comments.append(file.read(sub_block_size).decode('utf-8', errors='ignore'))
                    elif block == b'\x3B':  # Fin del archivo
                        break
                    elif not block:
                        break  # Final de archivo inesperado
                metadata['comments'] = ' '.join(comments) if comments else "N/A"

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
                    gif_files.append(gif_path)
        return gif_files

    # Funciones de la GUI
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
            gif_path = self.gif_list.get(selection[0])
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

            messagebox.showinfo("Metadatos del GIF", info_text)

    def save_metadata(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if save_path:
            with open(save_path, 'w') as file:
                json.dump(self.file_metadata, file, indent=4)
            print(f"Metadata saved to {save_path}")

    def edit_metadata(self):
        selection = self.gif_list.curselection()
        if selection:
            gif_path = self.gif_list.get(selection[0])
            metadata = self.file_metadata.get(gif_path)
            if metadata:
                EditWindow(self.root, gif_path, metadata, self)
            else:
                messagebox.showinfo("Información", "No hay metadatos disponibles para editar")


class EditWindow:
    def __init__(self, master, file_path, metadata, app):
        self.top = Toplevel(master)
        self.top.title("Editar Metadata")
        self.file_path = file_path
        self.app = app
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
    root = Tk()
    app = GIFDataExtractorApp(root)
    root.mainloop()
