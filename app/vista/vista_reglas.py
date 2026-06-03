from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QFormLayout, 
                               QGroupBox, QComboBox, QSpinBox, QCheckBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Catálogo estático de extensiones categorizadas
EXT_CATALOG = {
    "Documentos": [".pdf", ".docx", ".doc", ".xls", ".xlsx", ".txt"],
    "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "Video": [".mp4", ".mkv", ".avi", ".mov"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Desarrollo": [".py", ".js", ".java", ".cpp", ".c", ".cs"],
}

class VistaReglasOrganizacion(QWidget):
    def __init__(self, asistente, callback_regresar, parent=None):
        super().__init__(parent)
        self.asistente = asistente
        self.callback_regresar = callback_regresar # Función para regresar al Dashboard
        
        self.init_ui()
        self.actualizar_selector_carpetas() # Cargar carpetas dinámicamente desde Fase 1

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # =========================================================================
        # CABECERA DE LA SECCIÓN (FASE 2)
        # =========================================================================
        head = QVBoxLayout()
        tit = QLabel("Fase 2: Gestor de Reglas por Carpeta"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel("Asigne extensiones, prioridades y estados de activación a sus carpetas de destino monitoreadas."); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit)
        head.addWidget(sub)
        layout_principal.addLayout(head)

        # Contenedores horizontales distribuidos
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        # Estilos compartidos de tu diseño
        estilo_frame = "background: #181818; border-radius: 10px; border: 1px solid #222; padding: 15px;"
        estilo_input = "background: #121212; color: white; padding: 8px; border: 1px solid #333; border-radius: 5px;"
        estilo_tabla = """
            QTableWidget { background-color: #121212; color: white; gridline-color: #222; border: none; border-radius: 5px; }
            QHeaderView::section { background-color: #181818; color: #aaaaaa; font-weight: bold; border: 1px solid #222; padding: 6px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #eab308; color: black; }
        """
        # Estilo específico para combo (hover amarillo tenue)
        estilo_combo = """
            QComboBox { background: #121212; color: white; padding: 6px; border: 1px solid #333; border-radius: 5px; }
            QComboBox:hover { border: 1px solid #eab308; background-color: #eab308; color: black; }
            QComboBox::drop-down:hover { background-color: #eab308; }
        """

        # =========================================================================
        # PANEL IZQUIERDO: CRUD Y PARÁMETROS DE LA REGLA
        # =========================================================================
        grupo_config = QGroupBox("Configurar Parámetros")
        grupo_config.setFixedWidth(400)
        grupo_config.setStyleSheet("""
            QGroupBox { color: white; font-weight: bold; border: 1px solid #222; border-radius: 10px; margin-top: 10px; padding: 15px; background: #121212; }
            QLabel { color: #aaaaaa; font-size: 13px; }
        """)
        layout_form = QFormLayout(grupo_config)
        layout_form.setSpacing(12)

        # Selector Dinámico de Carpeta Destino (Carga datos de la Fase 1)
        self.combo_carpetas = QComboBox()
        # Aplicar estilo de inputs y hover amarillo
        self.combo_carpetas.setStyleSheet(estilo_input + estilo_combo)
        # Al cambiar la carpeta seleccionada, se actualiza automáticamente la tabla de reglas
        self.combo_carpetas.currentTextChanged.connect(self.cargar_reglas_por_carpeta)

        self.input_nombre_regla = QLineEdit()
        self.input_nombre_regla.setPlaceholderText("Ej: Filtro de Videos")
        self.input_nombre_regla.setStyleSheet(estilo_input)

        # Combo de extensiones categorizadas (evita errores tipográficos)
        self.combo_extension = QComboBox()
        self.combo_extension.setStyleSheet(estilo_input + estilo_combo)
        self.combo_extension.setEditable(False)
        # Primera opción: cualquiera
        self.combo_extension.addItem("* (Cualquiera)", None)
        for cat, exts in EXT_CATALOG.items():
            # agregar un separador visual
            self.combo_extension.addItem(f"--- {cat} ---")
            idx = self.combo_extension.count() - 1
            self.combo_extension.model().item(idx).setEnabled(False)
            for ext in exts:
                display = f"{cat}: {ext}"
                self.combo_extension.addItem(display, ext)

        # prioridad removida en la nueva fase; mantenemos el campo oculto si se necesita
        self.spin_prioridad = QSpinBox()
        self.spin_prioridad.setRange(0, 100)
        self.spin_prioridad.setValue(0)
        self.spin_prioridad.setVisible(False)

        self.check_activa = QCheckBox(" Regla Activa / Habilitada")
        self.check_activa.setChecked(True)
        self.check_activa.setStyleSheet("color: #aaaaaa; font-size: 13px; padding-top: 5px;")

        layout_form.addRow("Carpeta Objetivo:", self.combo_carpetas)
        layout_form.addRow("Nombre de Regla:", self.input_nombre_regla)
        layout_form.addRow("Extensión Permitida:", self.combo_extension)
        layout_form.addRow("", self.spin_prioridad)
        layout_form.addRow("", self.check_activa)

        # Botón Agregar Regla (Estilo Amarillo)
        btn_agregar_regla = QPushButton("AGREGAR REGLA")
        btn_agregar_regla.setStyleSheet("QPushButton { background: #eab308; color: white; font-weight: bold; padding: 12px; border-radius: 5px; border: none; margin-top: 5px; } QPushButton:hover { background: #c79906; }")
        btn_agregar_regla.clicked.connect(self.agregar_nueva_regla)
        layout_form.addRow("", btn_agregar_regla)

        split_layout.addWidget(grupo_config)

        # =========================================================================
        # PANEL DERECHO: LISTA Y ELIMINACIÓN DE REGLAS ACTIVAS
        # =========================================================================
        frame_tabla = QFrame()
        frame_tabla.setStyleSheet(estilo_frame)
        layout_tabla = QVBoxLayout(frame_tabla)

        lbl_tabla_tit = QLabel("📋 Reglas Asociadas a esta Carpeta"); lbl_tabla_tit.setStyleSheet("color: white; font-weight: bold; font-size: 15px; margin-bottom: 5px;")
        layout_tabla.addWidget(lbl_tabla_tit)

        # Tabla de visualización del CRUD
        self.tabla_reglas = QTableWidget()
        self.tabla_reglas.setColumnCount(4)
        self.tabla_reglas.setHorizontalHeaderLabels(["ID", "Nombre", "Extensión", "Estado"])
        # Mejoras de legibilidad
        fuente_tabla = QFont("Segoe UI", 11)
        self.tabla_reglas.setFont(fuente_tabla)
        self.tabla_reglas.setAlternatingRowColors(True)
        self.tabla_reglas.setShowGrid(False)
        self.tabla_reglas.setWordWrap(False)
        self.tabla_reglas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_reglas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_reglas.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed)
        # Señal para manejar cambios en celdas (persistir UPDATE)
        self.tabla_reglas.itemChanged.connect(self._on_regla_item_changed)
        self.tabla_reglas.setStyleSheet(estilo_tabla)
        layout_tabla.addWidget(self.tabla_reglas)

        # Botón Eliminar Regla (Estilo Rojo)
        btn_eliminar_regla = QPushButton("ELIMINAR REGLA SELECCIONADA")
        btn_eliminar_regla.setStyleSheet("QPushButton { background: #ef4444; color: white; font-weight: bold; padding: 12px; border-radius: 5px; border: none; } QPushButton:hover { background: #dc2626; }")
        btn_eliminar_regla.clicked.connect(self.eliminar_regla_seleccionada)
        layout_tabla.addWidget(btn_eliminar_regla)

        split_layout.addWidget(frame_tabla, 1)
        layout_principal.addLayout(split_layout, 1)

        # Botón inferior de retorno
        btn_volver = QPushButton("← VOLVER AL PANEL RESUMEN")
        btn_volver.setFixedWidth(220)
        btn_volver.setStyleSheet("QPushButton { background: #222; color: #aaa; font-weight: bold; padding: 10px; border-radius: 5px; border: 1px solid #333; } QPushButton:hover { background: #333; color: white; }")
        btn_volver.clicked.connect(self.callback_regresar)
        layout_principal.addWidget(btn_volver)

    # =========================================================================
    # CONEXIÓN DIRECTA CON SQLITE (REGLAS DE ORGANIZACIÓN)
    # =========================================================================
    def conectar_db(self):
        import sqlite3
        conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
        cursor = conn.cursor()
        # Creamos la tabla con la estructura exacta de tu especificación de base de datos
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
        conn.commit()
        return conn, cursor

    def actualizar_selector_carpetas(self):
        """Lee las carpetas destino insertadas en la Fase 1 para poblar el ComboBox"""
        try:
            conn, cursor = self.conectar_db()
            # Asegurar existencia de tabla directorios_destino por seguridad
            cursor.execute("CREATE TABLE IF NOT EXISTS directorios_destino (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_alias TEXT, nombre TEXT, ruta TEXT NOT NULL UNIQUE)")
            # Intentar usar nombre_alias, si no existe (DB antigua), usar nombre
            try:
                cursor.execute("SELECT nombre_alias FROM directorios_destino ORDER BY nombre_alias ASC")
                carpetas = [fila[0] for fila in cursor.fetchall() if fila[0]]
                if not carpetas:
                    # intentar columna 'nombre'
                    cursor.execute("SELECT nombre FROM directorios_destino ORDER BY nombre ASC")
                    carpetas = [fila[0] for fila in cursor.fetchall() if fila[0]]
            except Exception:
                # Fallback: intentar seleccionar 'nombre'
                try:
                    cursor.execute("SELECT nombre FROM directorios_destino ORDER BY nombre ASC")
                    carpetas = [fila[0] for fila in cursor.fetchall()]
                except Exception:
                    carpetas = []
            conn.close()

            self.combo_carpetas.blockSignals(True)
            self.combo_carpetas.clear()
            if carpetas:
                self.combo_carpetas.addItems(carpetas)
            else:
                self.combo_carpetas.addItem("sin carpetas configuradas")
            self.combo_carpetas.blockSignals(False)
            
            self.cargar_reglas_por_carpeta()
        except Exception as e:
            print(f"Error al poblar selector de carpetas: {e}")

    def cargar_reglas_por_carpeta(self):
        """Hace un SELECT filtrando por la carpeta seleccionada en el ComboBox"""
        carpeta_actual = self.combo_carpetas.currentText()
        if not carpeta_actual or carpeta_actual == "sin carpetas configuradas":
            self.tabla_reglas.setRowCount(0)
            return

        try:
            conn, cursor = self.conectar_db()
            cursor.execute("""
                SELECT id, nombre, extension, activa 
                FROM reglas_organizacion 
                WHERE carpeta_destino = ? 
                ORDER BY fecha_creacion DESC
            """, (carpeta_actual,))
            filas = cursor.fetchall()
            conn.close()

            self.tabla_reglas.setRowCount(0)
            for idx, fila in enumerate(filas):
                self.tabla_reglas.insertRow(idx)
                ext_val = fila[2] if fila[2] else "* (Cualquiera)"
                estado_val = "🟢 Activa" if fila[3] == 1 else "🔴 Inactiva"

                self.tabla_reglas.setItem(idx, 0, QTableWidgetItem(str(fila[0])))
                item_nombre = QTableWidgetItem(str(fila[1]))
                item_nombre.setFlags(item_nombre.flags() | Qt.ItemIsEditable)
                self.tabla_reglas.setItem(idx, 1, item_nombre)

                item_ext = QTableWidgetItem(str(ext_val))
                item_ext.setFlags(item_ext.flags() | Qt.ItemIsEditable)
                self.tabla_reglas.setItem(idx, 2, item_ext)

                item_estado = QTableWidgetItem(str(estado_val))
                item_estado.setFlags(item_estado.flags() | Qt.ItemIsEditable)
                self.tabla_reglas.setItem(idx, 3, item_estado)
        except Exception as e:
            print(f"Error al mapear reglas de carpeta: {e}")

    def agregar_nueva_regla(self):
        """Ejecuta el INSERT en la tabla reglas_organizacion"""
        carpeta = self.combo_carpetas.currentText()
        nombre = self.input_nombre_regla.text().strip()
        # Obtener extensión seleccionada desde el combo (userData)
        ext_data = self.combo_extension.currentData()
        extension = ext_data.strip().lower().replace(".", "") if ext_data else None
        prioridad = self.spin_prioridad.value()
        activa = 1 if self.check_activa.isChecked() else 0

        if not carpeta or carpeta == "sin carpetas configuradas":
            QMessageBox.warning(self, "Falta Destino", "Primero debe agregar una carpeta destino en la Configuración Global (Fase 1).")
            return
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "Por favor, asigne un nombre identificatorio a la regla.")
            return

        try:
            conn, cursor = self.conectar_db()
            cursor.execute("""
                INSERT INTO reglas_organizacion (nombre, extension, carpeta_destino, activa)
                VALUES (?, ?, ?, ?)
            """, (nombre, extension if extension else None, carpeta, activa))
            conn.commit()
            conn.close()

            # Limpiar entradas del formulario
            self.input_nombre_regla.clear()
            try:
                self.combo_extension.setCurrentIndex(0)
            except Exception:
                pass
            self.spin_prioridad.setValue(0)
            
            # Recargar vista de la tabla
            self.cargar_reglas_por_carpeta()
        except Exception as e:
            QMessageBox.critical(self, "Error de Inserción", f"No se pudo guardar la regla: {e}")

    def eliminar_regla_seleccionada(self):
        """Ejecuta el DELETE en la tabla usando el ID único del registro"""
        fila_seleccionada = self.tabla_reglas.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, elija una regla de la tabla derecha para proceder a su eliminación.")
            return

        id_regla = self.tabla_reglas.item(fila_seleccionada, 0).text()
        nombre_regla = self.tabla_reglas.item(fila_seleccionada, 1).text()

        try:
            conn, cursor = self.conectar_db()
            cursor.execute("DELETE FROM reglas_organizacion WHERE id = ?", (id_regla,))
            conn.commit()
            conn.close()

            self.cargar_reglas_por_carpeta()
            QMessageBox.information(self, "Eliminado", f"La regla '{nombre_regla}' fue removida del sistema.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Eliminación", f"No se pudo eliminar la regla: {e}")

    def showEvent(self, event):
        """Cada vez que la vista se muestra en pantalla, refresca el combo por si se agregaron nuevos destinos en Fase 1"""
        self.actualizar_selector_carpetas()
        super().showEvent(event)

    # ------------------------------------------------------------------
    # Manejo de edición en la tabla
    # ------------------------------------------------------------------
    def _on_regla_item_changed(self, item):
        # Evitar reaccionar mientras rellenamos la tabla
        if getattr(self, "_populating_table", False):
            return

        row = item.row()
        col = item.column()
        id_item = self.tabla_reglas.item(row, 0)
        if not id_item:
            return
        id_regla = id_item.text()

        # Mapear columna a campo DB
        campo = None
        valor = item.text()
        if col == 1:
            campo = 'nombre'
        elif col == 2:
            campo = 'extension'
            # normalizar: permitir '*' o texto vacío -> NULL
            if valor.strip() in ("* (Cualquiera)", "*"):
                valor = None
            else:
                valor = valor.strip().lstrip('.')
        elif col == 3:
            campo = 'activa'
            valor = 1 if 'Activa' in valor else 0

        if campo is None:
            return

        try:
            conn, cursor = self.conectar_db()
            if valor is None:
                cursor.execute(f"UPDATE reglas_organizacion SET {campo} = NULL WHERE id = ?", (id_regla,))
            else:
                cursor.execute(f"UPDATE reglas_organizacion SET {campo} = ? WHERE id = ?", (valor, id_regla))
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error al actualizar", f"No se pudo actualizar la regla: {e}")