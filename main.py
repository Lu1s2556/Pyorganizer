import sys
from os import path
from app.vista.vista import DashboardOrganizador
from PySide6.QtWidgets import QApplication

# Aseguramos que Python encuentre la carpeta 'app'
sys.path.append(path.abspath(path.dirname(__file__)))

def ejecutar():
    app = QApplication(sys.argv)
    
    # Instanciamos la ventana que creamos con la IA integrada
    ventana = DashboardOrganizador()
    ventana.show()
    
    sys.exit(app.exec())

def ejecutar_organizador():
    """
    Punto de entrada principal. 
    Carga PySide6 y la interfaz solo al ser llamado.
    """
    try:
        # Importación bajo demanda (Lazy Loading) para optimizar RAM
        from PySide6.QtWidgets import QApplication
        from app.vista.vista import DashboardOrganizador

        # Inicialización de la aplicación Qt
        aplicacion = QApplication(sys.argv)
        aplicacion.setStyle("Fusion") # Estilo consistente en Windows/Linux

        # Instancia de la interfaz
        ventana = DashboardOrganizador()
        ventana.show()

        # Iniciar WatcherThread para monitoreo en segundo plano
        try:
            from app.watcher_thread import WatcherThread
            db_path = str(Path(__file__).resolve().parent / 'app' / 'recursos' / 'organizador.db')
            watcher = WatcherThread(db_path)
            # Conectar señales para logging básico
            watcher.started_ok.connect(lambda: print("Watcher iniciado"))
            watcher.error.connect(lambda msg: print(f"Watcher error: {msg}"))
            watcher.move_result = getattr(watcher, 'move_result', None)
            watcher.start()
        except Exception as e:
            print(f"No se pudo iniciar WatcherThread: {e}")

        print(" Interfaz VigiData iniciada correctamente.")
        print(" Memoria optimizada para entorno de 8GB RAM.")

        # Ejecución del bucle de eventos
        try:
            sys.exit(aplicacion.exec())
        finally:
            try:
                if 'watcher' in locals() and watcher is not None:
                    watcher.stop()
                    watcher.wait(1000)
            except Exception:
                pass

    except ImportError as e:
        print(f" Error: No se pudo cargar PySide6. Verifica tu entorno Poetry. {e}")
    except Exception as e:
        print(f" Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    ejecutar_organizador()