import os
import threading
import time
import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package is importable when running script directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.watcher_worker import WatcherWorker


def simulate_download(target_dir: Path, final_name: str, write_time: float = 3.0):
    tmp_name = final_name + '.crdownload'
    tmp_path = target_dir / tmp_name
    final_path = target_dir / final_name

    def writer():
        with open(tmp_path, 'wb') as f:
            # write in chunks to simulate ongoing download
            for i in range(5):
                f.write(b'x' * 1024 * 100)
                f.flush()
                time.sleep(write_time / 5)
        # rename to final
        os.rename(tmp_path, final_path)

    t = threading.Thread(target=writer, daemon=True)
    t.start()
    return final_path


def main():
    base = Path.home() / 'Downloads'
    base.mkdir(parents=True, exist_ok=True)

    # Prepare watcher
    worker = WatcherWorker(watch_root=str(base))
    # Set DB path to project's organizer DB
    db_path = Path(__file__).resolve().parent.parent / 'app' / 'recursos' / 'organizador.db'
    worker.set_db_path(str(db_path))

    # Hook simple print when file_ready
    worker.file_ready.connect(lambda p: print(f"FILE READY: {p}"))

    # Simulate a download that becomes ready after a few seconds
    target = simulate_download(base, 'test_download.txt', write_time=4.0)

    # Directly call internal wait (emulates handler detection)
    print("Simulando detección...")
    worker._wait_and_emit(str(target))

    print("Listo.")


if __name__ == '__main__':
    main()
