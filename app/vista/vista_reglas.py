from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QFormLayout, 
                               QGroupBox, QComboBox, QSpinBox, QCheckBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt

class VistaReglasOrganizacion(QWidget):
    def __init__(self, asistente, callback_regresar, parent=None):
        super().__init__(parent)
        self.asistente = asistente
        self.callback_regresar = callback_regresar # Función para volver al Dashboard
        
        self.init_ui()
        self.cargar_reglas_en_tabla()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # =========================================================================
        # CABECERA DE LA SECCIÓN
        # =========================================================================
        head = QVBoxLayout()
        tit = QLabel("Reglas de Organización"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel("Configura directrices avanzadas con prioridades y extensiones para el ordenamiento automatizado."); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit)
        head.addWidget(sub)
        layout_principal.addLayout(head)

        # Zona Central Dividida en Formulario (Izquierda) y Tabla de Reglas Existentes (Derecha)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        # =========================================================================
        # FORMULARIO DE REGISTRO (IZQUIERDA)
        # =========================================================================
        grupo_config = QGroupBox("Nueva Regla Normativa")
        grupo_config.setFixedWidth(380)
        grupo_config.setStyleSheet("""
            QGroupBox { color: white; font-weight: bold; border: 1px solid #222; border-radius: 10px; margin-top: 10px; padding: 15px; background: #121212; }
            QLabel { color: #aaaaaa; font-size: 13px; }
        """)
        layout_form = QFormLayout(grupo_config)
        layout_form.setSpacing(12)

        # Inputs del Formulario basados en la estructura SQL
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Planillas UNELLEZ")
        self.input_nombre.setStyleSheet("background: #181818; color: white; padding: 8px; border: 1px solid #333; border-radius: 5px;")

        self.input_extension = QLineEdit()
        self.input_extension.setPlaceholderText("Ej: pdf (o dejar vacío para cualquiera)")
        self.input_extension.setStyleSheet("background: #181818; color: white; padding: 8px; border: 1px solid #333; border-radius: 5px;")

        self.combo_destino = QComboBox()
        self.combo_destino.addItems(["universidad", "mis proyectos", "respaldos", "documentos", "fotos", "descargas"])
        self.combo_destino.setStyleSheet("background: #181818; color: white; padding: 8px; border: 1px solid #333; border-radius: 5px;")

        self.spin_prioridad = QSpinBox()
        self.spin_prioridad.setRange(0, 100)
        self.spin_prioridad.setValue(0)
        self.spin_prioridad.setStyleSheet("background: #181818; color: white; padding: 6px; border: 1px solid #333; border-radius: 5px;")

        self.check_activa = QCheckBox(" Regla Habilitada / Activa")
        self.check_activa.setChecked(True)
        self.check_activa.setStyleSheet("color: #aaaaaa; font-size: 13px; padding-top: 5px;")

        layout_form.addRow("Nombre Regla:", self.input_nombre)
        layout_form.addRow("Extensión:", self.input_extension)
        layout_form.addRow("Carpeta Destino:", self.combo_destino)
        layout_form.addRow("Prioridad Ord:", self.spin_prioridad)
        layout_form.addRow("", self.check_activa)

        # Botón Guardar (Estilo Amarillo de tu App)
        btn_guardar = QPushButton("GUARDAR REGLA")
        btn_guardar.setStyleSheet("""
            QPushButton { background: #eab308; color: white; font-weight: bold; padding: 12px; border-radius: 5px; border: none; margin-top: 10px; }
            QPushButton:hover { background: #d4a017; }
        """)
        btn_guardar.clicked.connect(self.guardar_regla)
        layout_form.addRow("", btn_guardar)
        
        split_layout.addWidget(grupo_config)

        # =========================================================================
        # TABLA DE VISUALIZACIÓN DE REGLAS (DERECHA)
        # =========================================================================
        tabla_frame = QFrame()
        tabla_frame.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222; padding: 10px;")
        tabla_layout = QVBoxLayout(tabla_frame)
        
        lbl_tabla_tit = QLabel("Reglas Activas en el Sistema"); lbl_tabla_tit.setStyleSheet("color: white; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        tabla_layout.addWidget(lbl_tabla_tit)

        self.tabla_reglas = QTableWidget()
        self.tabla_reglas.setColumnCount(5)
        self.tabla_reglas.setHorizontalHeaderLabels(["Nombre", "Ext", "Destino", "Prioridad", "Estado"])
        self.tabla_reglas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_reglas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_reglas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_reglas.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #222; border: none; border-radius: 5px; }
            QHeaderView::section { background-color: #181818; color: #aaaaaa; font-weight: bold; border: 1px solid #222; padding: 6px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #eab308; color: black; }
        """)
        tabla_layout.addWidget(self.tabla_reglas)
        
        split_layout.addWidget(tabla_frame, 1)
        layout_principal.addLayout(split_layout, 1)

        # Botón inferior para regresar de forma fluida
        btn_volver = QPushButton("← VOLVER AL PANEL RESUMEN")
        btn_volver.setFixedWidth(220)
        btn_volver.setStyleSheet("""
            QPushButton { background: #222; color: #aaa; font-weight: bold; padding: 10px; border-radius: 5px; border: 1px solid #333; }
            QPushButton:hover { background: #333; color: white; }
        """)
        btn_volver.clicked.connect(self.callback_regresar)
        layout_principal.addWidget(btn_volver)

    def guardar_regla(self):
        """Valida, procesa y manda la regla al Modelo/BD mediante el Controlador"""
        nombre = self.input_nombre.text().strip()
        extension = self.input_extension.text().strip().lower().replace(".", "")
        carpeta = self.combo_destino.currentText().lower()
        prioridad = self.spin_prioridad.value()
        activa = 1 if self.check_activa.isChecked() else 0

        if not nombre:
            QMessageBox.warning(self, "Campos Incompletos", "El campo 'Nombre Regla' es mandatorio.")
            return

        # Mandamos la petición al controlador/modelo.
        # NOTA: Asegúrate de añadir el método correspondiente en tu clase ModeloOrganizador para insertar esta estructura.
        try:
            conn = self.asistente.modelo_org._conectar() if hasattr(self.asistente.modelo_org, '_conectar') else None
            if not conn:
                import sqlite3
                conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reglas_organizacion (nombre, extension, carpeta_destino, prioridad, activa)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, extension if extension else None, carpeta, prioridad, activa))
            conn.commit()
            conn.close()
            
            # Limpiar entradas e informar al usuario
            self.input_nombre.clear()
            self.input_extension.clear()
            self.spin_prioridad.setValue(0)
            
            # Sincronizar UI
            self.cargar_reglas_en_tabla()
            if hasattr(self.asistente, 'actualizar_reglas_en_memoria'):
                self.asistente.actualizar_reglas_en_memoria()
                
            QMessageBox.information(self, "Éxito", f"Regla '{nombre}' guardada correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error de BD", f"No se pudo guardar la regla: {str(e)}")

    def cargar_reglas_en_tabla(self):
        """Consulta la base de datos y pinta las reglas guardadas en la tabla derecha"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
            cursor = conn.cursor()
            
            # Asegurar de que la tabla exista antes de consultar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reglas_organizacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    extension TEXT,
                    carpeta_destino TEXT NOT NULL,
                    prioridad INTEGER DEFAULT 0,
                    activa BOOLEAN DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            cursor.execute("SELECT nombre, extension, carpeta_destino, prioridad, activa FROM reglas_organizacion ORDER BY prioridad DESC")
            filas = cursor.fetchall()
            conn.close()

            self.tabla_reglas.setRowCount(0)
            for i, fila in enumerate(filas):
                self.tabla_reglas.insertRow(i)
                ext_val = fila[1] if fila[1] else "* (Todas)"
                estado_val = "🟢 Activa" if fila[4] == 1 else "🔴 Inactiva"
                
                self.tabla_reglas.setItem(i, 0, QTableWidgetItem(str(fila[0])))
                self.tabla_reglas.setItem(i, 1, QTableWidgetItem(str(ext_val)))
                self.tabla_reglas.setItem(i, 2, QTableWidgetItem(str(fila[2])))
                self.tabla_reglas.setItem(i, 3, QTableWidgetItem(str(fila[3])))
                self.tabla_reglas.setItem(i, 4, QTableWidgetItem(estado_val))
        except Exception as e:
            print(f"Error al cargar reglas en tabla: {e}")