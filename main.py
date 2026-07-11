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
        from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
        from PySide6.QtGui import QIcon
        from app.vista.vista import DashboardOrganizador
        import sqlite3
        from pathlib import Path

        # Inicialización de la aplicación Qt
        aplicacion = QApplication(sys.argv)
        aplicacion.setStyle("Fusion") # Estilo consistente en Windows/Linux
        
        # Evitar que se cierre al ocultar la ventana
        aplicacion.setQuitOnLastWindowClosed(False)

        # Configurar icono global
        ruta_base = Path(__file__).resolve().parent
        icon_path = str(ruta_base / 'logo.ico')
        if Path(icon_path).exists():
            app_icon = QIcon(icon_path)
            aplicacion.setWindowIcon(app_icon)
        else:
            app_icon = QIcon()

        # Instancia de la interfaz
        ventana = DashboardOrganizador()
        
        # Configurar System Tray (icono en la bandeja)
        tray = QSystemTrayIcon(app_icon, aplicacion)
        menu = QMenu()
        abrir_action = menu.addAction("Abrir Panel")
        abrir_action.triggered.connect(lambda: (ventana.show(), ventana.activateWindow()))
        salir_action = menu.addAction("Salir por completo")
        salir_action.triggered.connect(aplicacion.quit)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda r: (ventana.show(), ventana.activateWindow()) if r == QSystemTrayIcon.DoubleClick else None)
        tray.show()

        # Determinar si hay configuración previa para iniciar en segundo plano
        db_path_str = str(ruta_base / 'app' / 'recursos' / 'organizador.db')
        iniciar_oculto = False
        if Path(db_path_str).exists():
            try:
                with sqlite3.connect(db_path_str) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM carpetas_monitoreadas")
                    if cur.fetchone()[0] > 0:
                        iniciar_oculto = True
            except Exception:
                pass

        if not iniciar_oculto:
            ventana.show()
        else:
            tray.showMessage("PyOrganizer VigiData", "Iniciado en segundo plano. Doble clic para abrir.", QSystemTrayIcon.Information, 3000)

        # Iniciar WatcherThread para monitoreo en segundo plano
        try:
            from app.controlador.watcher_thread import WatcherThread
            watcher = WatcherThread(db_path_str)
            watcher.started_ok.connect(lambda: print("Watcher iniciado"))
            watcher.error.connect(lambda msg: print(f"Watcher error: {msg}"))
            watcher.start()
        except Exception as e:
            print(f"No se pudo iniciar WatcherThread: {e}")

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