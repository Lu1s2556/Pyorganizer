import os
from pathlib import Path

class ModeloOrganizador:
    def __init__(self):
        self.rutas_base = {
            "escritorio": Path.home() / "Desktop",
            "documentos": Path.home() / "Documents"
        }

    def crear_carpeta(self, ruta_base, nombre_carpeta):
        """
        Crea una carpeta en la ruta especificada.
        ruta_base: clave como 'escritorio' o 'documentos'
        nombre_carpeta: nombre de la nueva carpeta
        """
        try:
            if ruta_base not in self.rutas_base:
                return f"❌ Ruta base '{ruta_base}' no reconocida. Usa 'escritorio' o 'documentos'."

            ruta_completa = self.rutas_base[ruta_base] / nombre_carpeta
            ruta_completa.mkdir(parents=True, exist_ok=True)
            return f"✅ Carpeta '{nombre_carpeta}' creada en {ruta_base}."
        except Exception as e:
            return f"❌ Error al crear carpeta: {str(e)}"