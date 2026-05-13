import fasttext
import os
import shutil
import re
from pathlib import Path
from app.modelo.modelo import ModeloOrganizador

class AsistenteVigiData:
    def __init__(self):
        # Cargar el modelo entrenado (asegúrate de haberlo generado antes)
        self.modelo = None
        ruta_modelo = Path(__file__).resolve().parent.parent / 'recursos' / 'modelo_asistente.bin'
        if ruta_modelo.exists():
            try:
                self.modelo = fasttext.load_model(str(ruta_modelo))
            except Exception:
                self.modelo = None

        self.modelo_org = ModeloOrganizador()

        self.rutas = {
            "documentos": str(Path.home() / "Documents"),
            "fotos": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
            "descargas": str(Path.home() / "Downloads")
        }

    def mover_por_patron(self, patron, destino_clave):
        """Busca archivos que contengan el patrón y los mueve al destino."""
        try:
            ruta_origen = Path(self.rutas["descargas"])
            ruta_destino = Path(self.rutas.get(destino_clave, self.rutas["documentos"]))
            
            archivos_encontrados = []
            for archivo in ruta_origen.iterdir():
                # Si el nombre del archivo contiene el texto indicado por el usuario
                if archivo.is_file() and patron.lower() in archivo.name.lower():
                    # Usamos shutil para moverlo
                    shutil.move(str(archivo), str(ruta_destino / archivo.name))
                    archivos_encontrados.append(archivo.name)
            
            if archivos_encontrados:
                cantidad = len(archivos_encontrados)
                return f"✅ He movido {cantidad} archivos con el nombre '{patron}' a {destino_clave}."
            else:
                return f"❌ No encontré archivos que contengan '{patron}' en Descargas."
                
        except Exception as e:
            return f"⚠️ Error al mover archivos: {str(e)}"

    def procesar_peticion(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return "Escribe un texto para que pueda ayudarte."

        if self.modelo is None:
            return "No tengo un modelo cargado. Ejecuta entrenar_ia.py para generar app/recursos/modelo_asistente.bin."

        try:
            etiquetas, probabilidades = self.modelo.predict(texto, k=1)
            etiquetas = [e.decode() if isinstance(e, bytes) else str(e) for e in etiquetas]
            probabilidades = [float(p) for p in probabilidades]
        except Exception as e:
            return f"⚠️ Error al procesar la petición: {str(e)}"

        if not etiquetas:
            return "No pude identificar la intención de tu mensaje."

        etiqueta = etiquetas[0].replace("__label__", "")
        probabilidad = probabilidades[0] if probabilidades else 0.0

        return self._formatear_respuesta(etiqueta, probabilidad, texto)

    def _formatear_respuesta(self, etiqueta, probabilidad, texto):
        """Convierte la etiqueta FastText en una respuesta para la UI."""
        if probabilidad < 0.20:
            return "No estoy seguro de qué quieres. Intenta usar otra frase."

        # --- LÓGICA PARA CREAR ---
        if etiqueta == "crear":
            match = re.search(r'crea.*carpeta.*(?:en el|en)\s+(\w+).*llamada?\s+(.+)', texto, re.IGNORECASE)
            if match:
                ruta_base = match.group(1).lower()
                nombre_carpeta = match.group(2).strip()
                return self.modelo_org.crear_carpeta(ruta_base, nombre_carpeta)
            return "❌ No pude entender la ruta o nombre. Ejemplo: 'crea una carpeta en el escritorio llamada Tareas'."

        # --- NUEVA LÓGICA PARA MOVER POR NOMBRE ---
        if etiqueta == "mover":
            # Ejemplo: "mueve los archivos de tarea mod 1 a documentos"
            # Captura lo que está entre "de" y "a" como el nombre, y lo que sigue a "a" como el destino
            match = re.search(r'mueve.*archivos\s+(?:de|llamados|con nombre)\s+(.+)\s+a\s+(\w+)', texto, re.IGNORECASE)
            
            if match:
                patron_nombre = match.group(1).strip()
                destino_clave = match.group(2).lower().strip()
                return self.mover_por_patron(patron_nombre, destino_clave)
            else:
                return "❌ No entendí qué mover. Intenta: 'mueve los archivos de tarea mod 1 a documentos'."

        respuestas = {
            "crear": "✅ Entendido, voy a crear la carpeta o el recurso que necesitas.",
            "mover": "✅ Voy a mover el elemento al destino indicado.",
            "borrar": "✅ Voy a eliminar lo que has pedido.",
            "documentos": "Puedo ayudarte a manejar documentos.",
            "imagenes": "Puedo ayudarte a organizar imágenes.",
            "videos": "Puedo ayudarte a organizar tus videos.",
            "codigo": "Puedo ayudarte con archivos de código.",
        }

        if etiqueta in respuestas:
            return respuestas[etiqueta]

        return f"Detecté la intención '{etiqueta}' con {probabilidad:.2f} de confianza."

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