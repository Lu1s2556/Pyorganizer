import fasttext
import os
import shutil
import re
from pathlib import Path
from difflib import get_close_matches
from PySide6.QtCore import QObject, Signal
from app.modelo.modelo import ModeloOrganizador
from app.signals import app_signals


class AsistenteVigiData(QObject):
    actualizar_estadisticas = Signal(dict)

    def __init__(self):
        super().__init__()
         # Cargar el modelo entrenado
        self.modelo = None
        # Ubicación dinámica del modelo binario de FastText
        ruta_modelo = Path(__file__).resolve().parent.parent / 'recursos' / 'modelo_asistente.bin'
        
        if ruta_modelo.exists():
            try:
                self.modelo = fasttext.load_model(str(ruta_modelo))
            except Exception:
                self.modelo = None

        self.modelo_org = ModeloOrganizador()

        # Cargar frases de entrenamiento para sugerencias (fuzzy)
        self._entrenamiento_path = Path(__file__).resolve().parent.parent / 'recursos' / 'entrenamiento.txt'
        self._frases_entrenamiento = []
        try:
            if self._entrenamiento_path.exists():
                with open(self._entrenamiento_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('__label__'):
                            # store the human phrase part after the label
                            parts = line.split(maxsplit=1)
                            if len(parts) == 2:
                                self._frases_entrenamiento.append(parts[1].lower())
        except Exception:
            self._frases_entrenamiento = []

        # =========================================================================
        # PARTE 1: MAPA DE RUTAS INSTINTIVAS (ATAJOS)
        # =========================================================================
        # Traducción de alias cotidianos a rutas físicas del dispositivo
        self.rutas_atajo = {
            "escritorio": str(Path.home() / "Desktop"),
            "documentos": str(Path.home() / "Documents"),
            "descargas": str(Path.home() / "Downloads"),
            "fotos": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
            
            # Atajos personalizados pensados para el usuario final
            "mi pendrive": self._buscar_unidad_extraible(),
            "mis proyectos": str(Path.home() / "Documents" / "GitHub" / "Pyorganizer"),
            "universidad": str(Path.home() / "Documents" / "UNELLEZ"),
            "respaldos": "D:\\Respaldos" if os.path.exists("D:\\") else str(Path.home() / "Documents" / "Respaldos")
        }

    def _buscar_unidad_extraible(self):
        """Detecta de forma dinámica si hay un almacenamiento USB conectado al equipo"""
        for letra in ["D", "E", "F", "G", "H"]:
            ruta_unidad = f"{letra}:\\"
            if os.path.exists(ruta_unidad):
                return ruta_unidad
        # Fallback de seguridad si no hay pendrive introducido
        return str(Path.home() / "Desktop")

    def procesar_peticion(self, texto):
        """Recibe el texto de la Vista, predice la intención y ejecuta la acción"""
        texto = (texto or "").strip()
        if not texto:
            return "Escribe un comando para ayudarte."

        if self.modelo is None:
            return "⚠️ IA Desconectada. Primero ejecuta 'python entrenar_ia.py' para generar el cerebro."

        try:
            etiquetas, probabilidades = self.modelo.predict(texto, k=1)
            etiqueta = etiquetas[0].replace("__label__", "")
            probabilidad = probabilidades[0]
        except Exception as e:
            return f"⚠️ Error al analizar texto: {str(e)}"

        if probabilidad < 0.20:
            # Generar sugerencias usando frases de entrenamiento (fuzzy match)
            texto_l = texto.lower()
            suggestions = get_close_matches(texto_l, self._frases_entrenamiento, n=5, cutoff=0.4)
            # Si no hay matches por similitud, ofrecer ejemplos comunes
            if not suggestions:
                suggestions = [
                    "crea una carpeta llamada proyecto en documentos",
                    "mueve pdf a mis proyectos",
                    "muéstrame el reporte de estadísticas",
                    "ayuda",
                ]

            return {
                'message': "🤔 No entiendo bien tu instrucción. Prueba una de estas sugerencias:",
                'suggestions': suggestions
            }

        # =========================================================================
        # PARTE 2: FILTRADO DE INTENCIONES CON REGEX E IDIOMA NATURAL
        # =========================================================================
        
        # ACCIÓN A: CREAR CARPETA UTILIZANDO ALIAS
        if etiqueta == "crear":
            # Sintaxis intuitiva: "crea una carpeta llamada [nombre] en [alias]"
            match = re.search(r'crea.*carpeta.*(?:llamada|llamado)\s+([\w\d_-]+)\s+(?:en|en el|en la)\s+(.+)', texto, re.IGNORECASE)
            if match:
                nombre_carpeta = match.group(1).strip()
                destino_alias = match.group(2).strip().lower()
                
                # Resuelve el alias a una ruta real o usa el Escritorio por defecto
                ruta_padre = self.rutas_atajo.get(destino_alias, self.rutas_atajo["escritorio"])
                resultado = self.crear_carpeta_intuitiva(ruta_padre, nombre_carpeta)
                # Emitir señal de actualización con metadata mínima
                try:
                    self.actualizar_estadisticas.emit({'accion': 'crear', 'nombre': nombre_carpeta, 'destino': str(ruta_padre)})
                except Exception:
                    pass
                return resultado
                
            return "❌ Formato de creación no reconocido. Intenta: 'crea una carpeta llamada unellez en documentos'."

        # ACCIÓN B: MOVER ARCHIVOS (Soporta indicar la ubicación exacta de la carpeta)
        if etiqueta == "mover":
            # 1. Intentar buscar formato complejo: "mueve X a la carpeta Y en Z"
            # Ejemplo: "mueve el archivo tarea a la carpeta unellez en el escritorio"
            match_complejo = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+?)\s+(?:en\s+el\s+|en\s+la\s+|en\s+)(.+)', texto, re.IGNORECASE)
            
            if match_complejo:
                elemento_origen = match_complejo.group(1).strip().lower()
                destino_carpeta = match_complejo.group(2).strip() # Nombre real de la carpeta (ej: unellez)
                ubicacion_padre = match_complejo.group(3).strip().lower() # Lugar (ej: escritorio)
                
                # Resolver la ubicación del padre (ej: Escritorio, Documentos) o usar Escritorio por defecto
                ruta_padre = self.rutas_atajo.get(ubicacion_padre, self.rutas_atajo["escritorio"])
                ruta_destino = str(Path(ruta_padre) / destino_carpeta)
                
            else:
                # 2. Si no especifica ubicación ("en el X"), usar la lógica simple anterior
                # Ejemplo: "mueve pdf a universidad" o "mueve tarea a unellez"
                match_simple = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+)', texto, re.IGNORECASE)
                
                if match_simple:
                    elemento_origen = match_simple.group(1).strip().lower()
                    destino_peticion = match_simple.group(2).strip()
                    destino_clave = destino_peticion.lower()
                    
                    # Verificaciones dinámicas por defecto
                    if destino_clave in self.rutas_atajo:
                        ruta_destino = self.rutas_atajo[destino_clave]
                    else:
                        posible_carpeta_escritorio = Path(self.rutas_atajo["escritorio"]) / destino_peticion
                        posible_carpeta_documentos = Path(self.rutas_atajo["documentos"]) / destino_peticion
                        
                        if posible_carpeta_escritorio.exists() and posible_carpeta_escritorio.is_dir():
                            ruta_destino = str(posible_carpeta_escritorio)
                        elif posible_carpeta_documentos.exists() and posible_carpeta_documentos.is_dir():
                            ruta_destino = str(posible_carpeta_documentos)
                        else:
                            ruta_destino = str(posible_carpeta_escritorio)
                else:
                    return "❌ No logré descifrar qué mover o a dónde ir. Intenta: 'mueve tarea a unellez en el escritorio'."

            # Ejecutar el movimiento inteligente con la ruta resuelta
            resultado = self.ejecutar_movimiento_inteligente(elemento_origen, ruta_destino)
            # Emitir señal con conteo aproximado si hubo éxito
            try:
                # intentar inferir cuántos archivos fueron movidos desde el mensaje
                count = 0
                if isinstance(resultado, str):
                    m = re.search(r"Movidos (\d+) archivos", resultado)
                    if m:
                        count = int(m.group(1))
                    elif 'He movido el archivo' in resultado:
                        count = 1
                self.actualizar_estadisticas.emit({'accion': 'mover', 'origen': elemento_origen, 'destino': ruta_destino, 'cantidad': count})
            except Exception:
                pass
            return resultado

        return f"Intención detectada: '{etiqueta}' con {probabilidad*100:.1f}% de confianza, pero sin ejecutor."

    def crear_carpeta_intuitiva(self, ruta_padre, nombre_carpeta):
        """Crea físicamente un directorio utilizando las rutas simplificadas"""
        try:
            ruta_final = Path(ruta_padre) / nombre_carpeta
            ruta_final.mkdir(parents=True, exist_ok=True)
            return f"✅ Carpeta '{nombre_carpeta}' creada con éxito en '{Path(ruta_padre).name}'."
        except Exception as e:
            return f"❌ Error al crear la carpeta: {str(e)}"

    def ejecutar_movimiento_inteligente(self, origen, ruta_destino):
        """
        Analiza dinámicamente si el origen solicitado corresponde a una extensión pura,
        a un archivo único específico o a un grupo de archivos con el mismo patrón de nombre.
        """
        try:
            destino_dir = Path(ruta_destino)
            destino_dir.mkdir(parents=True, exist_ok=True) # Crea la carpeta destino (y padres) si no existe

            # Zonas de rastreo inicial (Descargas y Escritorio son las más comunes)
            carpetas_busqueda = [Path(self.rutas_atajo["descargas"]), Path(self.rutas_atajo["escritorio"])]
            archivos_movidos = []

            # Validar si el usuario introdujo únicamente una extensión de formato
            formatos_validos = ["pdf", "docx", "png", "jpg", "txt", "xlsx", "pptx", "zip", "rar"]
            es_extension_pura = origen in formatos_validos
            
            for carpeta in carpetas_busqueda:
                if not carpeta.exists():
                    continue
                    
                for item in carpeta.iterdir():
                    if item.is_file():
                        debe_moverse = False
                        
                        # Escenario A: Filtrado global por tipo de extensión (Ej: "mueve pdf a unellez en el escritorio")
                        if es_extension_pura and item.suffix.lower() == f".{origen}":
                            debe_moverse = True
                            
                        # Escenario B: Coincidencia de nombre (Mueve todo lo que contenga la frase, ej: "tarea")
                        elif not es_extension_pura and origen in item.name.lower():
                            debe_moverse = True
                        
                        # Ejecución física del traslado y almacenamiento en BD
                        if debe_moverse:
                            # Use shared helper to move and register
                            moved = self._move_and_register(item, destino_dir, carpeta)
                            if moved:
                                archivos_movidos.append(item.name)

                            # Emitir señal global de cambio de estadísticas
                            try:
                                app_signals.stats_changed.emit()
                            except Exception:
                                pass

            # Respuesta conversacional limpia para el chat de VigiData
            if archivos_movidos:
                if len(archivos_movidos) == 1:
                    return f"✅ He movido el archivo '{archivos_movidos[0]}' a su destino."
                return f"📁 ¡Éxito! Movidos {len(archivos_movidos)} archivos ('{origen}') hacia la ubicación asignada."
                
            return f"🔍 No localicé ningún archivo que coincida con '{origen}' en Descargas o Escritorio."
        
        except Exception as e:
            return f"❌ Error en la transferencia: {str(e)}"

    def _move_and_register(self, item, destino_dir: Path, carpeta: Path) -> bool:
        """Mueve un archivo físicamente, registra en la BD y emite señal global."""
        try:
            ruta_final = destino_dir / item.name
            tamano_archivo = item.stat().st_size

            # Manejo simple de colisiones
            if ruta_final.exists():
                nombre_base = item.stem
                ext = item.suffix.lstrip('.')
                contador = 1
                while ruta_final.exists():
                    ruta_final = destino_dir / f"{nombre_base}_{contador}.{ext}"
                    contador += 1

            shutil.move(str(item), str(ruta_final))

            # Registro histórico
            try:
                self.modelo_org.registrar_accion(
                    nombre=item.name,
                    tipo=item.suffix,
                    origen=str(carpeta),
                    destino=str(destino_dir),
                    tamano_bytes=tamano_archivo
                )
            except Exception:
                pass

            # Emitir señal global de cambio de estadísticas
            try:
                from app.signals import app_signals
                app_signals.stats_changed.emit()
            except Exception:
                pass

            return True
        except Exception:
            return False