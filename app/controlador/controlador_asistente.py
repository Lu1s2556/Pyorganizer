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
        # Detectar ruta base por atajos conocidos
        ruta_base = None
        for atajo, path_fisico in self.rutas_atajo.items():
            if atajo in texto:
                ruta_base = Path(path_fisico)
                break

        if not ruta_base:
            return "🔍 Dime si es 'Descargas', 'Escritorio' o 'Documentos' para añadir el origen."

        # Buscar si el usuario solicita crear una subcarpeta
        patron_carpeta = r"(?:llamada|carpeta|para|nombre)\s+([a-zA-Z0-9_ñáéíóú]+)"
        match = re.search(patron_carpeta, texto)
        carpeta_final = ruta_base
        mensaje_adicional = ""
        if match:
            nombre_subcarpeta = match.group(1).strip()
            carpeta_final = ruta_base / nombre_subcarpeta
            try:
                if not carpeta_final.exists():
                    carpeta_final.mkdir(parents=True, exist_ok=True)
                    mensaje_adicional = f" (No existía '{nombre_subcarpeta}', la creé por ti)"
                else:
                    mensaje_adicional = f" (La carpeta '{nombre_subcarpeta}' ya existía)"
            except Exception as e:
                return f"❌ Intenté crear la subcarpeta '{nombre_subcarpeta}' pero falló: {e}"

        # Registrar en la BD usando API existente
        try:
            alias = carpeta_final.name
            ok = None
            if getattr(self.modelo_org, 'gestor', None):
                ok = self.modelo_org.gestor.agregar_carpeta_monitoreada(str(carpeta_final), alias)
            elif hasattr(self.modelo_org, 'agregar_carpeta_monitoreada'):
                ok = self.modelo_org.agregar_carpeta_monitoreada(str(carpeta_final), alias)
            if ok == 'integrity_error':
                return f"❌ La carpeta '{carpeta_final}' ya está siendo monitoreada."
            if ok:
                try:
                    self.actualizar_reglas_en_memoria()
                except Exception:
                    pass
                try:
                    app_signals.stats_changed.emit()
                except Exception:
                    pass
                return f"✅ ¡Origen configurado! Ahora vigilo: {carpeta_final}{mensaje_adicional}"
            return f"❌ No pude registrar '{carpeta_final}' como origen (ya existe o fallo en BD)."
        except Exception as e:
            return f"❌ Error guardando origen en BD: {e}"

    def _ia_configurar_destino(self, texto: str) -> str:
        ruta_base = None
        for atajo, path_fisico in self.rutas_atajo.items():
            if atajo in texto:
                ruta_base = Path(path_fisico)
                break

        patron_nombre = r"(?:llamado|carpeta|destino)\s+([a-zA-Z0-9_ñáéíóú]+)"
        match = re.search(patron_nombre, texto)
        if match and ruta_base:
            destino_final = ruta_base / match.group(1).strip()
        elif ruta_base:
            destino_final = ruta_base
        else:
            return "🔍 Dime en qué ubicación (Escritorio, Descargas, Documentos) deseas establecer el destino."

        try:
            destino_final.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return f"❌ No pude crear/verificar la carpeta de destino: {e}"

        try:
            alias = destino_final.name
            ok = None
            if getattr(self.modelo_org, 'gestor', None):
                ok = self.modelo_org.gestor.agregar_directorio_destino(str(destino_final), alias)
            elif hasattr(self.modelo_org, 'agregar_directorio_destino'):
                ok = self.modelo_org.agregar_directorio_destino(str(destino_final), alias)
            if ok == 'integrity_error':
                return f"❌ El alias o la ruta ya existen para: {destino_final}"
            if ok:
                try:
                    app_signals.stats_changed.emit()
                except Exception:
                    pass
                return f"🎯 Destino listo. Los archivos se enviarán a: {destino_final}"
            return f"❌ No se pudo registrar destino en BD: {destino_final}"
        except Exception as e:
            return f"❌ Error registrando destino en BD: {e}"

    def _ia_configurar_regla(self, texto: str) -> str:
        # Captura extensiones en la frase
        patron_ext = r"\b\.?([a-zA-Z0-9]{2,5})\b"
        extensiones_detectadas = re.findall(patron_ext, texto)
        palabras_bloqueadas = set(["para", "crea", "una", "tipo", "con", "los", "las", "por", "regla", "archivos"]) 
        extensiones_limpias = [e.lower().lstrip('.') for e in extensiones_detectadas if e.lower() not in palabras_bloqueadas]
        # Deduplicar conservando orden
        seen = set(); extensiones_unicas = []
        for e in extensiones_limpias:
            if e not in seen and len(e) >= 2:
                seen.add(e); extensiones_unicas.append(e)

        if not extensiones_unicas:
            return "🔍 No logré identificar las extensiones en tu frase. Di por ejemplo: 'regla para pdf y docx'."

        cadena_extensiones = ",".join(extensiones_unicas)
        return f"📝 He preparado una regla multi-extensión para: [{cadena_extensiones}]. ¿A qué carpeta de destino deseas vincularla?"


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

        # Eliminar regla: 'eliminar regla .pdf'
        m_elim = re.search(r'(?:eliminar|quitar)\s+regla\s+\.?([A-Za-z0-9]+)', texto, re.IGNORECASE)
        if m_elim:
            ext = m_elim.group(1).strip().lower()
            if not ext.startswith('.'):
                ext = f'.{ext}'
            try:
                ok = False
                if getattr(self.modelo_org, 'gestor', None):
                    ok = self.modelo_org.gestor.eliminar_regla(ext)
                if ok:
                    try:
                        self.actualizar_reglas_en_memoria()
                    except Exception:
                        pass
                    try:
                        app_signals.stats_changed.emit()
                    except Exception:
                        pass
                    return f"✅ Regla eliminada: {ext}"
                return f"❌ No se encontró o no fue posible eliminar la regla {ext}."
            except Exception as e:
                return f"❌ Error al eliminar regla: {e}"

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