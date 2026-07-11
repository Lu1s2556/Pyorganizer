import fasttext
import os
import shutil
import re
import sqlite3
from pathlib import Path
from app.modelo.modelo import ModeloOrganizador
from app.signals import app_signals

class AsistenteVigiData:
    def __init__(self):
        self.modelo = None
        ruta_modelo = Path(__file__).resolve().parent.parent / 'recursos' / 'modelo_asistente.bin'
        
        # Carga fluida del modelo predictivo binario
        if ruta_modelo.exists():
            try:
                self.modelo = fasttext.load_model(str(ruta_modelo))
            except Exception:
                self.modelo = None

        self.modelo_org = ModeloOrganizador()
        self.umbral_confianza = 0.20 # Sensibilidad de la IA por defecto

        # Mapa dinámico de rutas y atajos intuitivos
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

        # Carga inicial de las reglas de organización desde SQLite (Fase 2)
        self.actualizar_reglas_en_memoria()

    def _buscar_unidad_extraible(self):
        """Escanea letras de unidades físicas buscando almacenamientos USB externos"""
        for letra in ["D", "E", "F", "G", "H"]:
            ruta_unidad = f"{letra}:\\"
            if os.path.exists(ruta_unidad):
                return ruta_unidad
        return str(Path.home() / "Desktop")

    def actualizar_reglas_en_memoria(self):
        """Sincroniza la lógica del controlador tras cambios asíncronos en la Vista (Fase 2)"""
        self.reglas_carpetas = {}
        try:
            conn = sqlite3.connect(str(self.modelo_org.db_path))
            cursor = conn.cursor()
            # Garantizar la existencia de la tabla de la Fase 2
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reglas_organizacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    extension TEXT,
                    carpeta_destino TEXT NOT NULL,
                    activa BOOLEAN DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("SELECT extension, carpeta_destino FROM reglas_organizacion WHERE activa = 1")
            
            for fila in cursor.fetchall():
                ext = fila[0].strip().lower() if fila[0] else None
                # Normalizar extensión con punto para consistencia absoluta con la Fase 2
                if ext and not ext.startswith('.'):
                    ext = f".{ext}"
                
                alias_carpeta = fila[1].lower().strip()
                if alias_carpeta not in self.reglas_carpetas:
                    self.reglas_carpetas[alias_carpeta] = []
                self.reglas_carpetas[alias_carpeta].append(ext)
                
            conn.close()
        except Exception as e:
            print(f"Error al sincronizar en memoria reglas de Fase 2: {e}")

    # ------------------ Nuevo: IA intención + extractor de entidades ------------------
    def procesar_comando_ia(self, texto_usuario: str) -> str:
        texto_limpio = (texto_usuario or "").strip().lower()
        if not texto_limpio:
            return "Escribe un comando para ayudarte."

        if not self.modelo:
            return "❌ El motor de IA no está disponible. Ejecuta el entrenamiento primero."

        try:
            etiquetas, probs = self.modelo.predict(texto_limpio, k=1)
            etiqueta = etiquetas[0]
        except Exception as e:
            return f"⚠️ Error al predecir intención: {e}"

        if etiqueta == '__label__config_origen':
            return self._ia_configurar_origen(texto_limpio)
        if etiqueta == '__label__config_destino':
            return self._ia_configurar_destino(texto_limpio)
        if etiqueta == '__label__config_regla':
            return self._ia_configurar_regla(texto_limpio)

        return "🤔 No te entendí del todo. ¿Puedes especificar la carpeta o la regla?"

    def _ia_configurar_origen(self, texto: str) -> str:
        # Sin alias: se abre el explorador y se usa el nombre de la carpeta seleccionada
        try:
            app_signals.solicitar_carpeta_origen.emit("")
        except Exception:
            pass
        return "📂 Abriendo explorador para seleccionar la carpeta de origen..."

    def _ia_configurar_destino(self, texto: str) -> str:
        # Extraer alias del texto del usuario
        patron_alias = r"(?:llamad[ao]|carpeta|destino|para|nombre|como)\s+([a-zA-Z0-9_ñáéíóúÑÁÉÍÓÚ]+)"
        match = re.search(patron_alias, texto)
        alias = match.group(1).strip() if match else ""

        if not alias:
            for atajo in self.rutas_atajo.keys():
                if atajo in texto:
                    alias = atajo
                    break

        if not alias:
            return "🔍 Dime el alias para este destino. Ejemplo: 'pon destino llamado universidad'"

        # Emitir señal para abrir el explorador de carpetas
        try:
            app_signals.solicitar_carpeta_destino.emit(alias)
        except Exception:
            pass
        return f"📂 Abriendo explorador para seleccionar la carpeta de destino '{alias}'..."

    def _ia_configurar_regla(self, texto: str) -> str:
        # Extraer palabras clave
        m_clave = re.search(r'(?:palabra(?: clave)?|que digan?|nombre|se llame)\s+([\w\d_-]+)', texto, re.IGNORECASE)
        palabra_clave = m_clave.group(1).strip() if m_clave else None

        # Captura extensiones
        patron_ext = r"\b\.?([a-zA-Z0-9]{2,5})\b"
        extensiones_detectadas = re.findall(patron_ext, texto)
        palabras_bloqueadas = set(["para", "crea", "una", "tipo", "con", "los", "las", "por", "regla", "archivos", "que", "hacia", "mueve", "todo", "lo", "sea", "contenga", "palabra", "clave", "destino"]) 
        extensiones_limpias = [e.lower().lstrip('.') for e in extensiones_detectadas if e.lower() not in palabras_bloqueadas]
        if palabra_clave and palabra_clave in extensiones_limpias:
            extensiones_limpias.remove(palabra_clave)
            
        # Detectar destino
        destino = None
        for atajo in self.rutas_atajo.keys():
            if re.search(rf'\b{atajo}\b', texto, re.IGNORECASE):
                destino = atajo
                break
        
        if not destino:
            m_dest = re.search(r'(?:hacia|en|a|guárdalos en|guárdalo en|mándalo a|van para|mueva a|envíalos a|al destino|al)\s+(?:la carpeta\s+|el destino\s+)?([\w\d_-]+)', texto, re.IGNORECASE)
            if m_dest:
                destino = m_dest.group(1).strip()

        seen = set(); extensiones_unicas = []
        for e in extensiones_limpias:
            if e not in seen and len(e) >= 2 and (not destino or e.lower() != destino.lower()):
                seen.add(e); extensiones_unicas.append(e)

        if not extensiones_unicas and not palabra_clave:
            return "🔍 No logré identificar extensiones ni palabras clave. Di: 'regla para pdf que diga factura hacia documentos'."

        if not destino:
            return "🔍 Debes especificar la carpeta de destino en el mismo comando. Por ejemplo: 'regla para pdf hacia universidad'."

        ext = extensiones_unicas[0] if extensiones_unicas else ""
        nombre_regla = f"Regla_{destino}_{ext or palabra_clave}"

        # Resolver el alias del destino al valor que usa vista_reglas (nombre_alias)
        # vista_reglas filtra por carpeta_destino == nombre_alias de directorios_destino
        alias_final = destino
        ruta_final = None
        try:
            if getattr(self.modelo_org, 'gestor', None):
                filas_destino = self.modelo_org.gestor.obtener_directorios_destino()
                for fila in filas_destino:
                    # fila puede ser un sqlite3.Row: ruta, nombre_alias
                    try:
                        alias_db = str(fila['nombre_alias'] or '').lower().strip()
                        ruta_db = str(fila['ruta'] or '').strip()
                    except (TypeError, KeyError):
                        try:
                            alias_db = str(fila[1] or '').lower().strip()
                            ruta_db = str(fila[0] or '').strip()
                        except Exception:
                            continue
                    if alias_db == destino.lower().strip():
                        alias_final = fila['nombre_alias'] if hasattr(fila, 'keys') else fila[1]
                        ruta_final = ruta_db
                        break
        except Exception:
            pass

        # Si no encontró en BD, buscar en rutas_atajo y registrar el destino automáticamente
        if not ruta_final and destino.lower() in self.rutas_atajo:
            ruta_fisica = self.rutas_atajo[destino.lower()]
            alias_final = destino.capitalize()
            try:
                Path(ruta_fisica).mkdir(parents=True, exist_ok=True)
                if getattr(self.modelo_org, 'gestor', None):
                    self.modelo_org.gestor.agregar_directorio_destino(ruta_fisica, alias_final)
            except Exception:
                pass
            ruta_final = ruta_fisica

        if not ruta_final:
            return f"🔍 No encontré el destino '{destino}'. Agrégalo primero con: 'agrega destino {destino} en documentos'."
        
        try:
            ok = False
            if getattr(self.modelo_org, 'gestor', None):
                ok = self.modelo_org.gestor.agregar_regla(nombre_regla, ext, alias_final, True, palabra_clave)
            if ok:
                try:
                    self.actualizar_reglas_en_memoria()
                    app_signals.stats_changed.emit()
                except Exception:
                    pass
                cond_msg = f"ext: {ext}" if ext else f"clave: '{palabra_clave}'"
                if ext and palabra_clave: cond_msg = f"ext: {ext} y clave: '{palabra_clave}'"
                return f"✅ Regla creada: {cond_msg} → {alias_final}"
            return f"❌ Falló al añadir la regla para {ext or palabra_clave}. ¿El destino '{alias_final}' está registrado?"
        except Exception as e:
            return f"❌ Error al crear regla: {e}"


    def procesar_peticion(self, texto):
        """Determina la intención semántica del usuario y enruta el flujo operativo"""
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

        # Si la etiqueta corresponde al nuevo pipeline de configuración, enrutar allí
        if etiqueta.startswith('config_'):
            return self.procesar_comando_ia(texto)

        # Confirmar creación y registro: 'confirmar crear destino <alias> en <ruta>'
        m_confirm_dest = re.search(r'^confirmar\s+crear\s+destin[ao]\s+([\w\d_-]+)\s+(?:en\s+)?(.+)', texto, re.IGNORECASE)
        if m_confirm_dest:
            alias = m_confirm_dest.group(1).strip()
            ruta_raw = m_confirm_dest.group(2).strip()
            ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
            ruta_path = Path(ruta)
            try:
                ruta_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"❌ No pude crear la carpeta física: {e}"
            # Registrar
            try:
                ok = None
                if hasattr(self.modelo_org, 'agregar_directorio_destino'):
                    ok = self.modelo_org.agregar_directorio_destino(str(ruta_path), alias)
                elif getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.gestor.agregar_directorio_destino(str(ruta_path), alias)
                if ok == 'integrity_error':
                    return f"❌ El alias o la ruta ya existen para: {ruta_path}"
                if ok:
                    try:
                        self.actualizar_reglas_en_memoria()
                    except Exception:
                        pass
                    try:
                        app_signals.stats_changed.emit()
                        app_signals.destinos_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Carpeta creada y registrada: {alias} → {ruta}"
                return f"❌ Error al registrar destino tras crear carpeta."
            except Exception as e:
                return f"❌ Error finalizando registro: {e}"

        # Soporte directo: 'crear destino <alias> en <ruta>' (sin confirmar)
        m_create_dest = re.search(r'^(?:crear|crear destino|crear_destino)\s*(?:destin[ao]\s*)?([\w\d_-]+)\s+(?:en\s+)?(.+)$', texto, re.IGNORECASE)
        if m_create_dest:
            alias = m_create_dest.group(1).strip()
            ruta_raw = m_create_dest.group(2).strip()
            ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
            ruta_path = Path(ruta)
            try:
                ruta_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"❌ No pude crear la carpeta física: {e}"
            try:
                ok = None
                if hasattr(self.modelo_org, 'agregar_directorio_destino'):
                    ok = self.modelo_org.agregar_directorio_destino(str(ruta_path), alias)
                elif getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.gestor.agregar_directorio_destino(str(ruta_path), alias)
                if ok == 'integrity_error':
                    return f"❌ El alias o la ruta ya existen para: {ruta_path}"
                if ok:
                    try:
                        self.actualizar_reglas_en_memoria()
                    except Exception:
                        pass
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Carpeta creada y registrada: {alias} → {ruta}"
                return f"❌ Error al registrar destino tras crear carpeta."
            except Exception as e:
                return f"❌ Error finalizando registro: {e}"

        # Confirmar creación de origen: 'confirmar agregar origen <alias> en <ruta>'
        m_confirm_origen = re.search(r'^confirmar\s+agregar\s+origen\s+([\w\d_-]+)\s+(?:en\s+)?(.+)$', texto, re.IGNORECASE)
        if m_confirm_origen:
            alias = m_confirm_origen.group(1).strip()
            ruta_raw = m_confirm_origen.group(2).strip()
            ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
            ruta_path = Path(ruta)
            try:
                ruta_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"❌ No pude crear la carpeta física: {e}"
            try:
                ok = None
                if getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.agregar_carpeta_monitoreada(str(ruta_path), alias)
                if ok == 'integrity_error':
                    return f"❌ La carpeta '{ruta_path}' ya está siendo monitoreada."
                if ok:
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Origen creado y registrado: {alias} → {ruta}"
                return f"❌ Error al registrar origen tras crearlo."
            except Exception as e:
                return f"❌ Error al finalizar registro de origen: {e}"

        # Monitorizar / agregar origen: 'monitorizar <ruta> como <alias>' or 'agregar origen <alias> en <ruta>'
        m_mon = re.search(r'^(?:monitorizar|monitorear)\s+(.+?)\s+como\s+([\w\d_-]+)$', texto, re.IGNORECASE)
        if m_mon:
            ruta_raw = m_mon.group(1).strip()
            alias = m_mon.group(2).strip()
            ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
            ruta_path = Path(ruta)
            if not ruta_path.exists():
                return f"La ruta '{ruta}' no existe. Responde 'confirmar agregar origen {alias} en {ruta}' para crearla y registrarla."
            try:
                ok = None
                if getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.agregar_carpeta_monitoreada(str(ruta_path), alias)
                if ok == 'integrity_error':
                    return f"❌ La carpeta '{ruta_path}' ya está siendo monitoreada."
                if ok:
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Origen registrado: {alias} → {ruta}"
                return f"❌ No se pudo registrar origen {alias}."
            except Exception as e:
                return f"❌ Error al registrar origen: {e}"

        m_mon = re.search(r'^(?:agregar)\s+origen\s+([\w\d_-]+)\s+(?:en\s+)?(.+)$', texto, re.IGNORECASE)
        if m_mon:
            alias = m_mon.group(1).strip()
            ruta_raw = m_mon.group(2).strip()
            ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
            ruta_path = Path(ruta)
            if not ruta_path.exists():
                return f"La ruta '{ruta}' no existe. Responde 'confirmar agregar origen {alias} en {ruta}' para crearla y registrarla."
            try:
                ok = False
                if getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.agregar_carpeta_monitoreada(str(ruta_path), alias)
                if ok:
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Origen registrado: {alias} → {ruta}"
                return f"❌ No se pudo registrar origen {alias}."
            except Exception as e:
                return f"❌ Error al registrar origen: {e}"

        # Asignar regla por extensión: 'asignar .pdf a <alias>' o 'regla: .jpg -> fotos'
        m_reg = re.search(r'(?:asignar|regla:?)\s*\.?([A-Za-z0-9]+)\s*(?:->|a)\s+([\w\d_-]+)', texto, re.IGNORECASE)
        if m_reg:
            ext = m_reg.group(1).strip().lower()
            if not ext.startswith('.'):
                ext = f'.{ext}'
            destino_alias = m_reg.group(2).strip()
            # Resolver ruta destino
            ruta_destino = self.rutas_atajo.get(destino_alias.lower())
            if not ruta_destino:
                # intentar buscar en directorios_destino
                try:
                    destinos = []
                    if getattr(self.modelo_org, 'gestor', None):
                        filas = self.modelo_org.obtener_directorios_destino()
                        for f in filas:
                            # fila puede ser sqlite Row or tuple
                            try:
                                alias = f['nombre_alias'] if isinstance(f, dict) or hasattr(f, 'keys') else f[2]
                                ruta = f['ruta'] if isinstance(f, dict) or hasattr(f, 'keys') else f[1]
                            except Exception:
                                alias = None; ruta = None
                            if alias and alias.lower() == destino_alias.lower():
                                ruta_destino = ruta
                                break
                except Exception:
                    ruta_destino = None
            if not ruta_destino:
                return f"❌ No encontré el destino '{destino_alias}'. Crea primero un destino o usa una ruta absoluta."
            # Crear regla
            nombre_regla = f"Regla_{destino_alias}_{ext.strip('.') }"
            try:
                ok = False
                if getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.gestor.agregar_regla(nombre_regla, ext, ruta_destino)
                if ok:
                    try:
                        self.actualizar_reglas_en_memoria()
                    except Exception:
                        pass
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Regla añadida: {ext} → {destino_alias} ({ruta_destino})"
                return f"❌ Falló al añadir la regla {ext}."
            except Exception as e:
                return f"❌ Error al crear regla: {e}"

        # INTENCIÓN: ELIMINAR ORIGEN, DESTINO O REGLA
        if etiqueta == "eliminar_origen":
            m = re.search(r'(?:elimina|borra|quita|deja de vigilar|ignora|desactiva(?:.*en)?|saca|ya no revises)\s+(?:el origen|la carpeta(?: de)?|la entrada de)?\s*([\w\d_-\s]+)', texto, re.IGNORECASE)
            if m:
                alias = m.group(1).strip().lower()
                alias = re.sub(r'^(el|la|los|las)\s+', '', alias).strip()
                try:
                    ok = False
                    if getattr(self.modelo_org, 'gestor', None):
                        ok = self.modelo_org.gestor.eliminar_carpeta_monitoreada_por_alias(alias)
                    if ok:
                        try:
                            app_signals.stats_changed.emit()
                            app_signals.origenes_changed.emit()
                        except Exception: pass
                        return f"✅ Origen eliminado: {alias}"
                    return f"❌ No se encontró el origen '{alias}'."
                except Exception as e:
                    return f"❌ Error: {e}"
            return "🔍 Indica qué origen eliminar. Ej: 'elimina el origen descargas'"

        if etiqueta == "eliminar_destino":
            m = re.search(r'(?:elimina|borra|quita|desvincula|suprime|ya no uses|ya no vamos a usar)\s+(?:el destino|la carpeta(?: de destino)?|la ruta(?: de salida(?: de)?)?|la salida llamada)?\s*([\w\d_-\s]+)', texto, re.IGNORECASE)
            if m:
                alias = m.group(1).strip().lower()
                alias = re.sub(r'^(el|la|los|las)\s+', '', alias).strip()
                try:
                    ok = False
                    if getattr(self.modelo_org, 'gestor', None):
                        ok = self.modelo_org.gestor.eliminar_directorio_destino(alias)
                    if ok:
                        try:
                            app_signals.stats_changed.emit()
                            app_signals.destinos_changed.emit()
                        except Exception: pass
                        return f"✅ Destino eliminado: {alias}"
                    return f"❌ No se encontró el destino '{alias}'."
                except Exception as e:
                    return f"❌ Error: {e}"
            return "🔍 Indica qué destino eliminar. Ej: 'borra el destino universidad'"

        if etiqueta == "eliminar_regla" or re.search(r'(?:eliminar|quitar)\s+regla\s+\.?([A-Za-z0-9]+)', texto, re.IGNORECASE):
            m_elim = re.search(r'(?:elimina|borra|quita|suprime|deshazte de|desactiva)\s+(?:la regla(?: de(?: la| las)?)?|el filtro(?: de(?: los)?)?|esa regla de|la condicion que mueve)\s+(?:los archivos|extensiones|palabra clave)?\s*\.?([\w\d_-\s]+)', texto, re.IGNORECASE)
            if not m_elim:
                m_elim = re.search(r'\.?([A-Za-z0-9]+)$', texto)
            if m_elim:
                ext_o_clave = m_elim.group(1).strip().lower()
                ext_o_clave = re.sub(r'^(el|la|los|las)\s+', '', ext_o_clave).strip()
                if ext_o_clave.startswith('.'):
                    ext_o_clave = f'.{ext_o_clave.strip(".")}'
                else:
                    if len(ext_o_clave) <= 4 and " " not in ext_o_clave and ext_o_clave.isalnum():
                        ext_o_clave = f'.{ext_o_clave}'
                try:
                    ok = False
                    if getattr(self.modelo_org, 'gestor', None):
                        ok = self.modelo_org.gestor.eliminar_regla(ext_o_clave)
                    if ok:
                        try:
                            self.actualizar_reglas_en_memoria()
                            app_signals.stats_changed.emit()
                        except: pass
                        return f"✅ Regla eliminada: {ext_o_clave}"
                    return f"❌ No se encontró la regla '{ext_o_clave}'."
                except Exception as e:
                    return f"❌ Error al eliminar regla: {e}"
            return "🔍 Indica qué regla eliminar. Ej: 'elimina la regla pdf'"

        # Listados: 'listar reglas', 'mostrar destinos', 'mostrar orígenes'
        m_list = re.search(r'^(?:listar|mostrar)\s+(reglas|destinos|origenes|orígenes|origenes)$', texto, re.IGNORECASE)
        if m_list:
            q = m_list.group(1).lower()
            try:
                if q.startswith('reg'):
                    filas = []
                    if getattr(self.modelo_org, 'gestor', None):
                        filas = self.modelo_org.gestor.obtener_reglas(solo_activas=False)
                    if not filas:
                        return "(vacio) No hay reglas definidas."
                    lines = []
                    for f in filas:
                        try:
                            ext = f['extension'] if isinstance(f, dict) or hasattr(f, 'keys') else f[2]
                            dest = f['carpeta_destino'] if isinstance(f, dict) or hasattr(f, 'keys') else f[3]
                        except Exception:
                            ext = f[2]; dest = f[3]
                        lines.append(f"{ext} → {dest}")
                    return "\n".join(lines)
                if q.startswith('dest'):
                    filas = []
                    if getattr(self.modelo_org, 'gestor', None):
                        filas = self.modelo_org.obtener_directorios_destino()
                    if not filas:
                        return "(vacio) No hay destinos registrados."
                    lines = []
                    for f in filas:
                        try:
                            alias = f['nombre_alias'] if isinstance(f, dict) or hasattr(f, 'keys') else f[2]
                            ruta = f['ruta'] if isinstance(f, dict) or hasattr(f, 'keys') else f[1]
                        except Exception:
                            alias = f[2]; ruta = f[1]
                        lines.append(f"{alias} → {ruta}")
                    return "\n".join(lines)
                if q.startswith('orig'):
                    filas = []
                    if getattr(self.modelo_org, 'gestor', None):
                        filas = self.modelo_org.gestor.obtener_carpetas_monitoreadas()
                    if not filas:
                        return "(vacio) No hay orígenes registrados."
                    lines = []
                    for f in filas:
                        try:
                            alias = f['nombre_alias'] if isinstance(f, dict) or hasattr(f, 'keys') else f[2]
                            ruta = f['ruta'] if isinstance(f, dict) or hasattr(f, 'keys') else f[1]
                        except Exception:
                            alias = f[2]; ruta = f[1]
                        lines.append(f"{alias} → {ruta}")
                    return "\n".join(lines)
            except Exception as e:
                return f"❌ Error listando: {e}"

        # INTENCIÓN: ESTADÍSTICAS (nuevo)
        if etiqueta == "estadisticas":
            try:
                stats = self.modelo_org.obtener_estadisticas()
                total = stats.get('total_operaciones', 0)
                operaciones_hoy = stats.get('operaciones_hoy', 0)
                por_tipo = stats.get('por_tipo', {})
                total_bytes = stats.get('total_bytes', 0)
                lines = [f"📊 Reporte: Operaciones totales: {total}", f"Hoy: {operaciones_hoy} operaciones", f"Almacenamiento procesado: {total_bytes} bytes"]
                for k, v in por_tipo.items():
                    lines.append(f"- {k}: {v}")
                return "\n".join(lines)
            except Exception as e:
                return f"❌ Error obteniendo estadísticas: {e}"

        # INTENCIÓN: CONFIGURACIÓN (nuevo)
        if etiqueta == "configuracion":
            # Ejemplo: 'cambia el destino de descargas a D:/Respaldos' o 'ajusta la ruta de descargas a respaldos'
            m_conf = re.search(r"(?:cambia|ajusta|configura|establece|modifica).*(?:destin[ao]|ruta).*descargas.*(?:a|en|hacia)\s*(.+)$", texto, re.IGNORECASE)
            if m_conf:
                ruta_raw = m_conf.group(1).strip().strip('"').strip("'")
                ruta = self.rutas_atajo.get(ruta_raw.lower(), ruta_raw)
                ruta = os.path.expanduser(ruta)
                ruta_path = Path(ruta)
                if not ruta_path.is_absolute() and not ruta_path.exists():
                    ruta_path = Path.home() / ruta
                ruta = str(ruta_path)
                try:
                    ruta_path.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                try:
                    ok = False
                    if hasattr(self.modelo_org, 'guardar_configuracion'):
                        ok = self.modelo_org.guardar_configuracion('ruta_default_descargas', ruta)
                    if ok:
                        return f"✅ Ruta por defecto de Descargas actualizada a: {ruta}"
                    else:
                        return f"❌ No pude guardar la configuración. Intenta manualmente."
                except Exception as e:
                    return f"❌ Error al guardar configuración: {e}"
            return "🔍 Indica la ruta de descargas. Ej: 'cambia el destino de descargas a D:/Respaldos'"

        # INTENCIÓN: CREAR CARPETA
        if etiqueta == "crear":
            match = re.search(r"crea.*carpeta.*(?:llamada|llamado)\s+\"?([^\"']+?)\"?\s+(?:en\s+(?:el\s+|la\s+)?)(.+)$", texto, re.IGNORECASE)
            if match:
                nombre_carpeta = match.group(1).strip()
                destino_alias = match.group(2).strip().lower()
                ruta_padre = self.rutas_atajo.get(destino_alias, None)
                if ruta_padre is None:
                    ruta_padre = Path.home() / destino_alias
                return self.crear_carpeta_intuitiva(ruta_padre, nombre_carpeta)
            return "❌ Formato no reconocido. Ej: 'crea una carpeta llamada unellez en documentos'."

        # INTENCIÓN: MOVER ARCHIVOS (Soporte Estructura Simple y Compleja)
        if etiqueta == "mover":
            match_complejo = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+?)\s+(?:en\s+el\s+|en\s+la\s+|en\s+)(.+)', texto, re.IGNORECASE)
            
            if match_complejo:
                elemento_origen = match_complejo.group(1).strip().lower()
                destino_carpeta = match_complejo.group(2).strip()
                ubicacion_padre = match_complejo.group(3).strip().lower()
                
                ruta_padre = self.rutas_atajo.get(ubicacion_padre, self.rutas_atajo["escritorio"])
                ruta_destino = str(Path(ruta_padre) / destino_carpeta)
                alias_evaluacion = destino_carpeta.lower().strip()
            else:
                match_simple = re.search(r'mueve\s+(?:los archivos de|el archivo|todos los|la carpeta)?\s*(.+?)\s+a\s+(?:la carpeta\s+)?(.+)', texto, re.IGNORECASE)
                if match_simple:
                    elemento_origen = match_simple.group(1).strip().lower()
                    destino_peticion = match_simple.group(2).strip()
                    alias_evaluacion = destino_peticion.lower().strip()
                    
                    if alias_evaluacion in self.rutas_atajo:
                        ruta_destino = self.rutas_atajo[alias_evaluacion]
                    else:
                        posible_carpeta_escritorio = Path(self.rutas_atajo["escritorio"]) / destino_peticion
                        ruta_destino = str(posible_carpeta_escritorio)
                else:
                    return "❌ No logré descifrar el comando de transferencia. Ej: 'mueve tarea a unellez en el escritorio'."

            return self.ejecutar_movimiento_inteligente(elemento_origen, ruta_destino, alias_evaluacion)

        return f"Intención '{etiqueta}' detectada con éxito, pero carece de un método ejecutor activo."

    def crear_carpeta_intuitiva(self, ruta_padre, nombre_carpeta):
        try:
            ruta_final = Path(ruta_padre) / nombre_carpeta
            ruta_final.mkdir(parents=True, exist_ok=True)
            return f"✅ Carpeta '{nombre_carpeta}' creada con éxito en '{Path(ruta_padre).name}'."
        except Exception as e:
            return f"❌ Error al crear la carpeta: {str(e)}"

    def ejecutar_movimiento_inteligente(self, origen, ruta_destino, alias_carpeta):
        """Mueve archivos aplicando de forma estricta los filtros regulados de la Fase 2"""
        try:
            self.actualizar_reglas_en_memoria() # Actualización Just-In-Time de la BD antes del barrido
            destino_dir = Path(ruta_destino)
            destino_dir.mkdir(parents=True, exist_ok=True)

            carpetas_busqueda = [Path(self.rutas_atajo["descargas"]), Path(self.rutas_atajo["escritorio"])]
            archivos_movidos = []
            archivos_bloqueados_por_regla = 0

            formatos_validos = ["pdf", "docx", "png", "jpg", "txt", "xlsx", "pptx", "zip", "rar"]
            es_extension_pura = origen in formatos_validos
            
            # Obtener las extensiones permitidas para esta carpeta desde las reglas de la Fase 2
            extensiones_permitidas = self.reglas_carpetas.get(alias_carpeta, [])

            for carpeta in carpetas_busqueda:
                if not carpeta.exists():
                    continue
                    
                for item in carpeta.iterdir():
                    if item.is_file():
                        debe_moverse = False
                        
                        # Comprobación de coincidencia por extensión o por lexema en el nombre
                        if es_extension_pura and item.suffix.lower() == f".{origen}":
                            debe_moverse = True
                        elif not es_extension_pura and origen in item.name.lower():
                            debe_moverse = True
                        
                        if debe_moverse:
                            # --- CONTROL POLICIAL DE LA FASE 2 ---
                            # Si la carpeta tiene reglas activas asignadas, filtramos por extensión
                            if extensiones_permitidas:
                                ext_archivo = item.suffix.lower().strip()
                                # Si no está explícitamente en la lista y tampoco hay regla universal (None)
                                if ext_archivo not in extensiones_permitidas and None not in extensiones_permitidas:
                                    archivos_bloqueados_por_regla += 1
                                    continue
                            
                            # Procesamiento físico e inserción histórica estructurada
                            tamano_archivo = item.stat().st_size
                            if self._move_and_register(item, destino_dir, str(carpeta)):
                                archivos_movidos.append(item.name)

            if archivos_movidos:
                msg = f"✅ ¡Éxito! Se trasladaron {len(archivos_movidos)} archivos a '{destino_dir.name}'."
                if archivos_bloqueados_por_regla > 0:
                    msg += f"\n⚠️ Nota: {archivos_bloqueados_por_regla} archivos fueron retenidos por restricciones de la Fase 2."
                return msg
            
            if archivos_bloqueados_por_regla > 0:
                return f"⚠️ Archivos localizados, pero retenidos: No cumplen las reglas de extensión de la Fase 2 para la carpeta '{destino_dir.name}'."
                
            return f"🔍 No localicé ningún archivo que coincida con '{origen}' en Descargas o Escritorio."
        
        except Exception as e:
            return f"❌ Error en la transferencia física: {str(e)}"

    def _move_and_register(self, archivo_path, ruta_final_dir, origen_padre):
        """Método de soporte modular requerido por el Motor Organizador Core."""
        try:
            archivo_path = Path(archivo_path)
            ruta_final_dir = Path(ruta_final_dir)
            ruta_final_archivo = ruta_final_dir / archivo_path.name

            # Resolver colisiones de nombres nativamente
            if ruta_final_archivo.exists():
                nombre_base = archivo_path.stem
                ext_archivo = archivo_path.suffix.lower()
                contador = 1
                while ruta_final_archivo.exists():
                    ruta_final_archivo = ruta_final_dir / f"{nombre_base}_{contador}{ext_archivo}"
                    contador += 1

            tamano_archivo = archivo_path.stat().st_size
            shutil.move(str(archivo_path), str(ruta_final_archivo))

            # Registro persistente en el historial técnico
            self.modelo_org.registrar_accion(
                nombre=ruta_final_archivo.name,
                tipo=ruta_final_archivo.suffix,
                origen=str(origen_padre),
                destino=str(ruta_final_dir),
                tamano_bytes=tamano_archivo
            )
            return True
        except Exception as e:
            print(f"Error interno en _move_and_register: {e}")
            return False