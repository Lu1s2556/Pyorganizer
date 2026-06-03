from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt

class VistaConfiguracionGlobal(QWidget):
    def __init__(self, asistente, callback_regresar, parent=None):
        super().__init__(parent)
        self.asistente = asistente
        self.callback_regresar = callback_regresar # Método para alternar al panel resumen
        
        self.init_ui()
        self.cargar_origenes()
        self.cargar_destinos()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # =========================================================================
        # CABECERA
        # =========================================================================
        head = QVBoxLayout()
        tit = QLabel("Configuración Global de Directorios"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel("Fase 1: Gestione los flujos de entrada (Orígenes) y las carpetas de clasificación (Destinos)."); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit)
        head.addWidget(sub)
        layout_principal.addLayout(head)

        # Estilo unificado para los contenedores oscuros
        estilo_frame = "background: #181818; border-radius: 10px; border: 1px solid #222; padding: 15px;"
        estilo_tabla = """
            QTableWidget { background-color: #121212; color: white; gridline-color: #222; border: none; border-radius: 5px; }
            QHeaderView::section { background-color: #181818; color: #aaaaaa; font-weight: bold; border: 1px solid #222; padding: 6px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #eab308; color: black; }
        """
        estilo_input = "background: #121212; color: white; padding: 8px; border: 1px solid #333; border-radius: 5px;"
        estilo_btn_amarillo = "QPushButton { background: #eab308; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; border: none; } QPushButton:hover { background: #d4a017; }"
        estilo_btn_rojo = "QPushButton { background: #ef4444; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; border: none; } QPushButton:hover { background: #dc2626; }"

        # Secciones divididas en dos columnas (Orígenes a la izquierda, Destinos a la derecha)
        columnas_layout = QHBoxLayout()
        columnas_layout.setSpacing(20)

        # =========================================================================
        # COLUMNA IZQUIERDA: GESTIÓN DE ORÍGENES (MONITOREO)
        # =========================================================================
        frame_origen = QFrame()
        frame_origen.setStyleSheet(estilo_frame)
        layout_origen = QVBoxLayout(frame_origen)
        
        lbl_orig_tit = QLabel("📥 Carpetas de Origen (Monitoreadas)"); lbl_orig_tit.setStyleSheet("color: white; font-weight: bold; font-size: 15px; margin-bottom: 5px;")
        layout_origen.addWidget(lbl_orig_tit)

        # Input y selector de ruta de Origen
        origen_input_layout = QHBoxLayout()
        self.input_ruta_origen = QLineEdit()
        self.input_ruta_origen.setPlaceholderText("Seleccione o pegue una ruta...")
        self.input_ruta_origen.setStyleSheet(estilo_input)
        btn_buscar_origen = QPushButton("📂")
        btn_buscar_origen.setStyleSheet("background: #222; color: white; border: 1px solid #333; padding: 6px; border-radius: 5px;")
        btn_buscar_origen.clicked.connect(lambda: self.seleccionar_directorio(self.input_ruta_origen))
        origen_input_layout.addWidget(self.input_ruta_origen)
        origen_input_layout.addWidget(btn_buscar_origen)
        layout_origen.addLayout(origen_input_layout)

        # Botones de Acción para Origen
        origen_btn_layout = QHBoxLayout()
        btn_add_origen = QPushButton("Agregar Origen")
        btn_add_origen.setStyleSheet(estilo_btn_amarillo)
        btn_add_origen.clicked.connect(self.agregar_origen)
        btn_del_origen = QPushButton("Eliminar Seleccionado")
        btn_del_origen.setStyleSheet(estilo_btn_rojo)
        btn_del_origen.clicked.connect(self.eliminar_origen)
        origen_btn_layout.addWidget(btn_add_origen)
        origen_btn_layout.addWidget(btn_del_origen)
        layout_origen.addLayout(origen_btn_layout)

        # Tabla de Orígenes
        self.tabla_origenes = QTableWidget()
        self.tabla_origenes.setColumnCount(2)
        self.tabla_origenes.setHorizontalHeaderLabels(["ID", "Ruta de Entrada"])
        self.tabla_origenes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_origenes.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_origenes.setStyleSheet(estilo_tabla)
        layout_origen.addWidget(self.tabla_origenes)

        columnas_layout.addWidget(frame_origen)

        # =========================================================================
        # COLUMNA DERECHA: GESTIÓN DE DESTINOS (CLASIFICACIÓN)
        # =========================================================================
        frame_destino = QFrame()
        frame_destino.setStyleSheet(estilo_frame)
        layout_destino = QVBoxLayout(frame_destino)

        lbl_dest_tit = QLabel("📤 Carpetas de Destino (Clasificación)"); lbl_dest_tit.setStyleSheet("color: white; font-weight: bold; font-size: 15px; margin-bottom: 5px;")
        layout_destino.addWidget(lbl_dest_tit)

        # Inputs de Nombre Alias y Ruta Destino
        destino_inputs = QVBoxLayout()
        self.input_alias_destino = QLineEdit()
        self.input_alias_destino.setPlaceholderText("Nombre/Alias de la carpeta (ej: universidad, fotos)")
        self.input_alias_destino.setStyleSheet(estilo_input)
        destino_inputs.addWidget(self.input_alias_destino)

        destino_ruta_layout = QHBoxLayout()
        self.input_ruta_destino = QLineEdit()
        self.input_ruta_destino.setPlaceholderText("Ruta del directorio destino...")
        self.input_ruta_destino.setStyleSheet(estilo_input)
        btn_buscar_destino = QPushButton("📂")
        btn_buscar_destino.setStyleSheet("background: #222; color: white; border: 1px solid #333; padding: 6px; border-radius: 5px;")
        btn_buscar_destino.clicked.connect(lambda: self.seleccionar_directorio(self.input_ruta_destino))
        destino_ruta_layout.addWidget(self.input_ruta_destino)
        destino_ruta_layout.addWidget(btn_buscar_destino)
        destino_inputs.addLayout(destino_ruta_layout)
        layout_destino.addLayout(destino_inputs)

        # Botones de Acción para Destino
        destino_btn_layout = QHBoxLayout()
        btn_add_destino = QPushButton("Agregar Destino")
        btn_add_destino.setStyleSheet(estilo_btn_amarillo)
        btn_add_destino.clicked.connect(self.agregar_destino)
        btn_del_destino = QPushButton("Eliminar Seleccionado")
        btn_del_destino.setStyleSheet(estilo_btn_rojo)
        btn_del_destino.clicked.connect(self.eliminar_destino)
        destino_btn_layout.addWidget(btn_add_destino)
        destino_btn_layout.addWidget(btn_del_destino)
        layout_destino.addLayout(destino_btn_layout)

        # Tabla de Destinos
        self.tabla_destinos = QTableWidget()
        self.tabla_destinos.setColumnCount(3)
        self.tabla_destinos.setHorizontalHeaderLabels(["ID", "Alias / Nombre", "Ruta de Salida"])
        self.tabla_destinos.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_destinos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_destinos.setStyleSheet(estilo_tabla)
        layout_destino.addWidget(self.tabla_destinos)

        columnas_layout.addWidget(frame_destino)
        layout_principal.addLayout(columnas_layout, 1)

        # Botón inferior de retorno
        btn_volver = QPushButton("← VOLVER AL PANEL RESUMEN")
        btn_volver.setFixedWidth(220)
        btn_volver.setStyleSheet("QPushButton { background: #222; color: #aaa; font-weight: bold; padding: 10px; border-radius: 5px; border: 1px solid #333; } QPushButton:hover { background: #333; color: white; }")
        btn_volver.clicked.connect(self.callback_regresar)
        layout_principal.addWidget(btn_volver)

    def seleccionar_directorio(self, campo_texto):
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if ruta:
            campo_texto.setText(ruta)

    # =========================================================================
    # LÓGICA DE BASE DE DATOS DIRECTA / SINCRONIZACIÓN (SQLITE)
    # =========================================================================
    def conectar_db(self):
        import sqlite3
        conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
        cursor = conn.cursor()
        # Verificar la existencia de las tablas asociadas a la Fase 1
        # Usamos 'carpetas_monitoreadas' para mantener compatibilidad con el motor/watcher
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carpetas_monitoreadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL UNIQUE,
                nombre_alias TEXT,
                activa BOOLEAN DEFAULT 1,
                fecha_agregada DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directorios_destino (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL UNIQUE,
                nombre_alias TEXT
            )
        """)
        conn.commit()
        return conn, cursor

    def cargar_origenes(self):
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT id, ruta FROM carpetas_monitoreadas WHERE activa = 1")
            filas = cursor.fetchall()
            conn.close()

            self.tabla_origenes.setRowCount(0)
            for idx, fila in enumerate(filas):
                self.tabla_origenes.insertRow(idx)
                self.tabla_origenes.setItem(idx, 0, QTableWidgetItem(str(fila[0])))
                self.tabla_origenes.setItem(idx, 1, QTableWidgetItem(str(fila[1])))
        except Exception as e:
            print(f"Error al cargar orígenes: {e}")

    def agregar_origen(self):
        ruta = self.input_ruta_origen.text().strip()
        if not ruta:
            QMessageBox.warning(self, "Error", "Debe especificar una ruta válida.")
            return
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("INSERT OR IGNORE INTO carpetas_monitoreadas (ruta, nombre_alias, activa) VALUES (?, ?, 1)", (ruta, None))
            conn.commit()
            conn.close()
            self.input_ruta_origen.clear()
            self.cargar_origenes()
        except Exception as e:
            QMessageBox.critical(self, "Error de SQLite", f"La ruta ya existe o es inválida: {e}")

    def eliminar_origen(self):
        fila_seleccionada = self.tabla_origenes.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Selección Requerida", "Seleccione un registro de la tabla origen para eliminar.")
            return
        id_registro = self.tabla_origenes.item(fila_seleccionada, 0).text()
        try:
            conn, cursor = self.conectar_db()
            # En lugar de borrar, marcamos como inactiva por seguridad
            cursor.execute("UPDATE carpetas_monitoreadas SET activa = 0 WHERE id = ?", (id_registro,))
            conn.commit()
            conn.close()
            self.cargar_origenes()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro: {e}")

    def cargar_destinos(self):
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT id, nombre_alias, ruta FROM directorios_destino")
            filas = cursor.fetchall()
            conn.close()

            self.tabla_destinos.setRowCount(0)
            for idx, fila in enumerate(filas):
                self.tabla_destinos.insertRow(idx)
                self.tabla_destinos.setItem(idx, 0, QTableWidgetItem(str(fila[0])))
                self.tabla_destinos.setItem(idx, 1, QTableWidgetItem(str(fila[1] or '')))
                self.tabla_destinos.setItem(idx, 2, QTableWidgetItem(str(fila[2])))
        except Exception as e:
            print(f"Error al cargar destinos: {e}")

    def agregar_destino(self):
        nombre = self.input_alias_destino.text().strip().lower()
        ruta = self.input_ruta_destino.text().strip()
        if not nombre or not ruta:
            QMessageBox.warning(self, "Error", "Debe completar tanto el nombre/alias como la ruta destino.")
            return
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("INSERT INTO directorios_destino (ruta, nombre_alias) VALUES (?, ?)", (ruta, nombre))
            conn.commit()
            conn.close()
            self.input_alias_destino.clear()
            self.input_ruta_destino.clear()
            self.cargar_destinos()
        except Exception as e:
            QMessageBox.critical(self, "Error de SQLite", f"El alias o la ruta ya se encuentran registrados: {e}")

    def eliminar_destino(self):
        fila_seleccionada = self.tabla_destinos.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Selección Requerida", "Seleccione un registro de la tabla destino para eliminar.")
            return
        id_registro = self.tabla_destinos.item(fila_seleccionada, 0).text()
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("DELETE FROM directorios_destino WHERE id = ?", (id_registro,))
            conn.commit()
            conn.close()
            self.cargar_destinos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro: {e}")