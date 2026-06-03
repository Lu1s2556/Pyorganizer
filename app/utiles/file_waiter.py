import os
import time
import errno
from typing import Optional


def wait_for_file_ready(path: str, timeout: Optional[int] = None, poll_interval: float = 1.0) -> bool:
    start = time.time()
    last_exc = None

    while True:
        try:
            with open(path, 'a'):
                pass
            try:
                os.rename(path, path)
            except OSError:
                pass
            return True
        except PermissionError as e:
            last_exc = e
        except FileNotFoundError:
            last_exc = None
        except OSError as e:
            if getattr(e, 'errno', None) in (errno.EACCES, 32):
                last_exc = e
            else:
                raise

        if timeout is not None and (time.time() - start) > timeout:
            return False

        time.sleep(poll_interval)


def safe_move(src: str, dst: str, conflict_suffix: str = "(%d)") -> str:
    import shutil

    base_dst = dst
    name, ext = os.path.splitext(base_dst)
    i = 1
    while True:
        try:
            return shutil.move(src, base_dst)
        except shutil.Error:
            base_dst = f"{name}{conflict_suffix % i}{ext}"
            i += 1
