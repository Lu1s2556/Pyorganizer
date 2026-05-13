import fasttext
import os
import shutil
from pathlib import Path

class AsistenteVigiData:
    def __init__(self):
        # Cargar el modelo entrenado (asegúrate de haberlo generado antes)
        
        self.modelo = fasttext.load_model('app/recursos/modelo_asistente.bin')
        
        self.rutas = {
            "documentos": str(Path.home() / "Documents"),
            "fotos": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
            "descargas": str(Path.home() / "Downloads")
        }

    def procesar_peticion(self, texto):
        # 1. Predecir intención con FastText
        # etiqueta, probabilidad = self.modelo.predict(texto)
        
        # 2. Lógica de ejecución (Ejemplo de cómo manejar el guardado)
        # Si la intención es 'guardar_foto' y el usuario indica una ruta:
        # self.guardar_elemento(origen, "fotos")
        pass

    def guardar_elemento(self, ruta_origen, tipo_destino):
        """Mueve un archivo a la carpeta correspondiente (Fotos, Videos, etc.)"""
        try:
            destino = self.rutas.get(tipo_destino)
            if destino and os.path.exists(ruta_origen):
                shutil.move(ruta_origen, destino)
                return f"✅ Archivo movido a {tipo_destino}"
            return "❌ No se encontró el destino o el archivo origen."
        except Exception as e:
            return f"⚠️ Error: {str(e)}"