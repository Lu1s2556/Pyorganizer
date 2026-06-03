import os
import shutil
import sqlite3
from pathlib import Path

class MotorOrganizadorCore:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conectar_db(self):
        return sqlite3.connect(str(self.db_path))

    def obtener_configuracion(self):
        """
        Extrae los orígenes, destinos y reglas organizadas por prioridad.
        Retorna estructuras de datos nativas (listas/dict) muy ligeras en memoria.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 1. Obtener carpetas de origen (monitoreadas)
        cursor.execute("SELECT ruta FROM directorios_origen")
        origenes = [Path(fila[0]) for fila in cursor.fetchall() if os.path.exists(fila[0])]

        # 2. Obtener mapas de carpetas destino (alias -> ruta_real)
        cursor.execute("SELECT nombre, ruta FROM directorios_destino")
        destinos = {fila[0].lower(): Path(fila[1]) for fila in cursor.fetchall()}

        # 3. Obtener reglas de organización activas ordenadas por prioridad de mayor a menor
        cursor.execute("""
            SELECT extension, carpeta_destino, prioridad 
            FROM reglas_organizacion 
            WHERE activa = 1 
            ORDER BY prioridad DESC
        """)
        reglas = []
        for fila in cursor.fetchall():
            ext = fila[0].strip().lower() if fila[0] else None
            reglas.append({
                "extension": ext,
                "destino_alias": fila[1].lower(),
                "prioridad": fila[2]
            })

        conn.close()
        return origenes, destinos, reglas

    def procesar_organizacion(self, callback_progreso=None):
        """
        Escanea los directorios de origen y mueve los archivos basándose en las reglas.
        Usa un generador liviano para no saturar la memoria RAM.
        """
        origenes, destinos, reglas = self.obtener_configuracion()
        archivos_movidos = 0

        if not origenes or not destinos:
            return 0

        for ruta_origen in origenes:
            # Iterar solo sobre los archivos directos del origen (evitamos recursividad masiva para cuidar la RAM)
            try:
                for entrada in os.scandir(ruta_origen):
                    if entrada.is_file():
                        archivo_path = Path(entrada.path)
                        ext_archivo = archivo_path.suffix.lower().replace(".", "")

                        # Buscar qué regla coincide (al estar ordenadas por prioridad, la primera que aplique gana)
                        for regla in reglas:
                            coincide_ext = (regla["extension"] == ext_archivo) or (regla["extension"] is None)
                            alias_dest = regla["destino_alias"]

                            if coincide_ext and alias_dest in destinos:
                                ruta_final_dir = destinos[alias_dest]
                                
                                # Asegurar que la carpeta de destino exista físicamente
                                os.makedirs(ruta_final_dir, exist_ok=True)
                                
                                ruta_final_archivo = ruta_final_dir / archivo_path.name

                                # Manejo de colisiones de nombres (si el archivo ya existe en el destino)
                                if ruta_final_archivo.exists():
                                    nombre_base = archivo_path.stem
                                    contador = 1
                                    while ruta_final_archivo.exists():
                                        ruta_final_archivo = ruta_final_dir / f"{nombre_base}_{contador}.{ext_archivo}"
                                        contador += 1

                                try:
                                    shutil.move(str(archivo_path), str(ruta_final_archivo))
                                    archivos_movidos += 1
                                    
                                    if callback_progreso:
                                        callback_progreso(f"Movido: {archivo_path.name} → {alias_dest}")
                                except Exception as e:
                                    if callback_progreso:
                                        callback_progreso(f"Error al mover {archivo_path.name}: {str(e)}")
                                
                                break # Rompe el ciclo de reglas, pasa al siguiente archivo
            except Exception as e:
                if callback_progreso:
                    callback_progreso(f"Error accediendo a {ruta_origen}: {str(e)}")

        return archivos_movidos