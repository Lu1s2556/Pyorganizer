import os
import time
import errno
from typing import Optional


def wait_for_file_ready(path: str, timeout: Optional[int] = None, poll_interval: float = 1.0) -> bool:
    """Espera hasta que el archivo esté liberado por el sistema y sea accesible para operaciones.

    Estrategia:
    - Reintenta abrir el archivo en modo append ('a') para comprobar si está bloqueado.
    - Alternativamente intenta renombrar el archivo a sí mismo si la apertura falla.
    - Devuelve True cuando el archivo parece listo, False si expira el timeout.

    Args:
        path: Ruta al archivo a comprobar.
        timeout: Segundos máximos a esperar (None = infinito).
        poll_interval: Segundos entre intentos.
    """
    start = time.time()
    last_exc = None

    while True:
        try:
            # Intento rápido: abrir en modo append y cerrar
            with open(path, 'a'):
                pass
            # Intentar renombrarlo a sí mismo para detectar locks más estrictos
            try:
                os.rename(path, path)
            except OSError:
                # Algunos sistemas no permiten renombrar igual, ignoramos
                pass
            return True
        except PermissionError as e:
            last_exc = e
        except FileNotFoundError:
            # Si el archivo desapareció, consideramos que no está listo
            last_exc = None
        except OSError as e:
            # En Windows puede salir con errno 13 (permission) o 32 (sharing violation)
            if getattr(e, 'errno', None) in (errno.EACCES, 32):
                last_exc = e
            else:
                # Otros errores los propagamos
                raise

        if timeout is not None and (time.time() - start) > timeout:
            return False

        time.sleep(poll_interval)


def safe_move(src: str, dst: str, conflict_suffix: str = "(%d)") -> str:
    """Mover archivo `src` a `dst` asegurando no sobrescribir. Devuelve la ruta final.

    Nota: usa shutil.move en quien llame después de usar `wait_for_file_ready`.
    """
    import shutil

    base_dst = dst
    name, ext = os.path.splitext(base_dst)
    i = 1
    while True:
        try:
            return shutil.move(src, base_dst)
        except shutil.Error:
            # problema al mover, intentar con sufijo
            base_dst = f"{name}{conflict_suffix % i}{ext}"
            i += 1
