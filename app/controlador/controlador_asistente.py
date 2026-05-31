import fasttext
import os
import shutil
import re
from pathlib import Path
from app.modelo.modelo import ModeloOrganizador

class AsistenteVigiData:
    def __init__(self):
        self.modelo = None
        ruta_modelo = Path(__file__).resolve().parent.parent / 'recursos' / 'modelo_asistente.bin'
        
        if ruta_modelo.exists():
            try:
                self.modelo = fasttext.load_model(str(ruta_modelo))
            except Exception:
                self.modelo = None

        self.modelo_org = ModeloOrganizador()
        self.umbral_confianza = 0.20

        self.rutas_atajo = {
            "escritorio": str(Path.home() / "Desktop"),
            "documentos": str(Path.home() / "Documents"),
            "descargas": str(Path.home() / "Downloads"),
            "fotos": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
            "mi pendrive": self._buscar_unidad_extraible(),
            "mis proyectos": str(Path.home() / "Documents" / "GitHub" / "Pyorganizer"),
            "universidad": str(Path.home() / "Documents" / "UNELLEZ"),
            "respaldos": "D:\\Respaldos" if os.path.exists("D:\\") else str(Path.home() / "Documents" / "Respaldos")
        }

        # Cargar las reglas de organización guardadas en la Base de Datos
        self.reglas_carpetas = self.modelo_org.obtener_todas_las_reglas()

    def _buscar_unidad_extraible(self):
        for letra in ["D", "E", "F", "G", "H"]:
            ruta_unidad = f"{letra}:\\"
            if os.path.exists(ruta_unidad):
                return ruta_unidad
        return str(Path.home() / "Desktop")

    def actualizar_reglas_en_memoria(self):
        """Sincroniza las reglas del controlador tras un cambio en la vista"""
        self.reglas_carpetas = self.modelo_org.obtener_todas_las_reglas()

    def procesar_peticion(self, texto):
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

        if probabilidad < self.umbral_confianza:
            return f"🤔 No tengo certeza suficiente ({probabilidad*100:.1f}%). Requiero mínimo {self.umbral_confianza*100:.0f}%."

        # ACCIÓN A: CREAR CARPETA
        if etiqueta == "crear":
            match = re.search(r'crea.*carpeta.*(?:llamada|llamado)\s+([\w\d_-]+)\s+(?:en|en el|en la)\s+(.+)', texto, re.IGNORECASE)
            if match:
                nombre_carpeta = match.group(1).strip()
                destino_alias = match.group(2).strip().lower()
                ruta_padre = self.rutas_atajo.get(destino_alias, self.rutas_atajo["escritorio"])
                return self.crear_carpeta_intuitiva(ruta_padre, nombre_carpeta)
            return "❌ Formato no reconocido. Ej: 'crea una carpeta llamada unellez en documentos'."

        # ACCIÓN B: MOVER ARCHIVOS CON VALIDACIÓN DE REGLAS
        if etiqueta == "mover":
            # Sintaxis compleja: "mueve X a la carpeta Y en Z"
            match_complejo = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+?)\s+(?:en\s+el\s+|en\s+la\s+|en\s+)(.+)', texto, re.IGNORECASE)
            
            if match_complejo:
                elemento_origen = match_complejo.group(1).strip().lower()
                destino_carpeta = match_complejo.group(2).strip()
                ubicacion_padre = match_complejo.group(3).strip().lower()
                
                ruta_padre = self.rutas_atajo.get(ubicacion_padre, self.rutas_atajo["escritorio"])
                ruta_destino = str(Path(ruta_padre) / destino_carpeta)
                alias_evaluacion = destino_carpeta.lower()
            else:
                # Sintaxis simple: "mueve X a Y"
                match_simple = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+)', texto, re.IGNORECASE)
                if match_simple:
                    elemento_origen = match_simple.group(1).strip().lower()
                    destino_peticion = match_simple.group(2).strip()
                    alias_evaluacion = destino_peticion.lower()
                    
                    if alias_evaluacion in self.rutas_atajo:
                        ruta_destino = self.rutas_atajo[alias_evaluacion]
                    else:
                        posible_carpeta_escritorio = Path(self.rutas_atajo["escritorio"]) / destino_peticion
                        if posible_carpeta_escritorio.exists() and posible_carpeta_escritorio.is_dir():
                            ruta_destino = str(posible_carpeta_escritorio)
                        else:
                            ruta_destino = str(posible_carpeta_escritorio)
                else:
                    return "❌ No logré descifrar el comando. Ej: 'mueve tarea a unellez'."

            return self.ejecutar_movimiento_inteligente(elemento_origen, ruta_destino, alias_evaluacion)

        return f"Intención '{etiqueta}' detectada sin ejecutor operativo."

    def crear_carpeta_intuitiva(self, ruta_padre, nombre_carpeta):
        try:
            ruta_final = Path(ruta_padre) / nombre_carpeta
            ruta_final.mkdir(parents=True, exist_ok=True)
            return f"✅ Carpeta '{nombre_carpeta}' creada con éxito en '{Path(ruta_padre).name}'."
        except Exception as e:
            return f"❌ Error al crear la carpeta: {str(e)}"

    def ejecutar_movimiento_inteligente(self, origen, ruta_destino, alias_carpeta):
        """Mueve archivos aplicando filtros y restricciones normativas por carpeta"""
        try:
            destino_dir = Path(ruta_destino)
            destino_dir.mkdir(parents=True, exist_ok=True)

            carpetas_busqueda = [Path(self.rutas_atajo["descargas"]), Path(self.rutas_atajo["escritorio"])]
            archivos_movidos = []
            archivos_bloqueados_por_regla = 0

            formatos_validos = ["pdf", "docx", "png", "jpg", "txt", "xlsx", "pptx", "zip", "rar"]
            es_extension_pura = origen in formatos_validos
            
            # Obtener si esta carpeta específica posee reglas restrictivas
            regla = self.reglas_carpetas.get(alias_carpeta)

            for carpeta in carpetas_busqueda:
                if not carpeta.exists():
                    continue
                    
                for item in carpeta.iterdir():
                    if item.is_file():
                        debe_moverse = False
                        
                        if es_extension_pura and item.suffix.lower() == f".{origen}":
                            debe_moverse = True
                        elif not es_extension_pura and origen in item.name.lower():
                            debe_moverse = True
                        
                        if debe_moverse:
                            # --- CONTROL POLICIAL DE LA IA (APLICAR REGLAS) ---
                            if regla:
                                ext_archivo = item.suffix.lower().replace(".", "")
                                nombre_archivo = item.name.lower()
                                
                                # 1. Validar restricción de extensiones si existen
                                if regla["extensiones"]:
                                    if ext_archivo not in regla["extensiones"]:
                                        archivos_bloqueados_por_regla += 1
                                        continue
                                
                                # 2. Validar restricción de palabras clave si existen
                                if regla["palabras"]:
                                    cumple_palabra = any(p in nombre_archivo for p in regla["palabras"])
                                    if not cumple_palabra:
                                        archivos_bloqueados_por_regla += 1
                                        continue
                            
                            # Proceder con la transferencia física
                            ruta_final = destino_dir / item.name
                            tamano_archivo = item.stat().st_size
                            shutil.move(str(item), str(ruta_final))
                            
                            self.modelo_org.registrar_accion(
                                nombre=item.name, tipo=item.suffix,
                                origen=str(carpeta), destino=str(destino_dir),
                                tamano_bytes=tamano_archivo
                            )
                            archivos_movidos.append(item.name)

            # Dar retroalimentación detallada al usuario en la UI
            if archivos_movidos:
                msg = f"📁 ¡Éxito! Se trasladaron {len(archivos_movidos)} archivos a '{destino_dir.name}'."
                if archivos_bloqueados_por_regla > 0:
                    msg += f" (⚠️ {archivos_bloqueados_por_regla} archivos fueron retenidos por no cumplir las reglas de organización)."
                return msg
            
            if archivos_bloqueados_por_regla > 0:
                return f"⚠️ Los archivos que coinciden fueron localizados, pero ninguno cumple las reglas estipuladas para la carpeta '{destino_dir.name}'."
                
            return f"🔍 No localicé ningún archivo que coincida con '{origen}' en Descargas o Escritorio."
        
        except Exception as e:
            return f"❌ Error en la transferencia: {str(e)}"