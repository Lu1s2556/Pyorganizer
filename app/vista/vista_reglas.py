import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QFormLayout, 
                               QComboBox, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QApplication, QAbstractItemView, QCheckBox)
from PySide6.QtGui import QFont, QColor, QIcon, QAction
from PySide6.QtCore import Qt, QSize

# =============================================================================
# HOJA DE ESTILO MAESTRA (QSS) - Diseño Moderno, Transparente y Amarillo
# =============================================================================
QSS_MODERNO = """
    /* Fondo principal translúcido */
    QWidget#VistaPrincipal {
        background-color: rgba(20, 20, 22, 150); /* Muy transparente para ver el escritorio */
    }

    QLabel {
        color: #e5e7eb;
        font-family: 'Segoe UI', sans-serif;
        background: transparent;
    }

    /* Paneles con efecto Glassmorphism */
    QFrame#PanelGlass {
        background-color: rgba(35, 35, 40, 180); /* Fondo panel semitransparente */
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 30); /* Borde sutil brillante */
        padding: 10px;
    }

    /* Entradas de texto modernas y ComboBox */
    QLineEdit, QComboBox {
        background-color: rgba(15, 15, 18, 200);
        color: white;
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 8px;
        padding: 10px 15px;
        font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #fbbf24; /* Amarillo Oro al enfocar */
        background-color: rgba(15, 15, 18, 255);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 1px solid rgba(255, 255, 255, 20);
    }

    /* Checkbox personalizado amarillo */
    QCheckBox {
        color: #aaaaaa;
        spacing: 8px;
        background: transparent;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid #444;
        background-color: #1a1a1c;
    }
    QCheckBox::indicator:unchecked:hover {
        border: 1px solid #fbbf24;
    }
    QCheckBox::indicator:checked {
        background-color: #eab308; /* Amarillo */
        border: 1px solid #eab308;
        /* Aquí iría un icono de check blanco si tuvieras el recurso */
    }

    /* Botones Modernos */
    QPushButton#BtnPrimario {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #eab308, stop:1 #fbbf24);
        color: #000;
        font-weight: bold;
        font-size: 13px;
        border-radius: 8px;
        padding: 12px;
        border: none;
    }
    QPushButton#BtnPrimario:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ca9606, stop:1 #eab308);
    }
    QPushButton#BtnPrimario:pressed {
        background: #ca9606;
    }

    QPushButton#BtnPeligro {
        background-color: rgba(239, 68, 68, 40); /* Rojo transparente */
        color: #ef4444;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid rgba(239, 68, 68, 100);
    }
    QPushButton#BtnPeligro:hover {
        background-color: rgba(239, 68, 68, 255); /* Rojo sólido */
        color: white;
    }

    QPushButton#BtnSecundario {
        background-color: transparent;
        color: #9ca3af;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px;
    }
    QPushButton#BtnSecundario:hover {
        background-color: rgba(255, 255, 255, 10);
        color: white;
        border: 1px solid #666;
    }

    /* Tabla Estilo Moderno y Transparente */
    QTableWidget {
        background-color: transparent;
        color: #e5e7eb;
        gridline-color: rgba(255, 255, 255, 10);
        border: none;
        outline: 0;
    }
    QTableWidget::item {
        padding: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 10);
    }
    QTableWidget::item:selected {
        background-color: rgba(234, 179, 8, 30); /* Amarillo muy suave */
        color: #fbbf24;
        font-weight: bold;
    }
    QHeaderView::section {
        background-color: transparent;
        color: #888;
        padding: 8px;
        border: none;
        border-bottom: 2px solid rgba(255, 255, 255, 20);
        font-weight: bold;
        font-size: 12px;
    }

    /* Barra de desplazamiento (Scrollbar) delgada y moderna */
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 30);
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #eab308; /* Amarillo al hover */
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

class VistaReglasOrganizacion(QWidget):
    def __init__(self, asistente=None, callback_regresar=None, parent=None):
        super().__init__(parent)
        self.setObjectName("VistaPrincipal")
        self.asistente = asistente
        # Callback dummy si no se provee, para poder probar la clase sola
        self.callback_regresar = callback_regresar if callback_regresar else lambda: print("Regresando...")
        
        # Aplicar el QSS globalmente a este widget y sus hijos
        self.setStyleSheet(QSS_MODERNO)
        
        self.init_ui()
        # Mock para pruebas, descomentar si usas la base de datos real
        # self.actualizar_selector_carpetas() 
        self._cargar_datos_prueba() # Eliminar esto en producción

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)

        # =========================================================================
        # CABECERA (Header)
        # =========================================================================
        head_layout = QHBoxLayout()
        
        icon_frame = QLabel("📁"); icon_frame.setStyleSheet("font-size: 35px; background: transparent;")
        head_layout.addWidget(icon_frame)

        info_head = QVBoxLayout()
        tit = QLabel("Gestor de Reglas por Carpeta")
        tit.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background: transparent;")
        sub = QLabel("Fase 2: Automatice la organización de sus archivos monitoreados.")
        sub.setStyleSheet("color: #9ca3af; font-size: 15px; background: transparent;")
        info_head.addWidget(tit)
        info_head.addWidget(sub)
        
        head_layout.addLayout(info_head)
        head_layout.addStretch()
        
        layout_principal.addLayout(head_layout)

        # Contenedores centrales (Split)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(30)

        # =========================================================================
        # PANEL IZQUIERDO: CONFIGURACIÓN (Formulario)
        # =========================================================================
        self.panel_config = QFrame()
        self.panel_config.setObjectName("PanelGlass")
        self.panel_config.setFixedWidth(380)
        
        layout_form_container = QVBoxLayout(self.panel_config)
        layout_form_container.setContentsMargins(15, 15, 15, 15)

        lbl_minititulo = QLabel("CREAR NUEVA REGLA")
        lbl_minititulo.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 12px; letter-spacing: 1px; margin-bottom: 10px;")
        layout_form_container.addWidget(lbl_minititulo)

        layout_form = QFormLayout()
        layout_form.setSpacing(15)
        layout_form.setLabelAlignment(Qt.AlignLeft)

        # 1. Carpeta Objetivo
        self.combo_carpetas = QComboBox()
        self.combo_carpetas.addItem("Seleccione carpeta...")

        # 2. Nombre
        self.input_nombre_regla = QLineEdit()
        self.input_nombre_regla.setPlaceholderText("Ej: Filtro de Documentos")

        # 3. Extensiones (CAMBIO CLAVE PARA RAM: QLineEdit en lugar de QListWidget)
        self.container_ext = QVBoxLayout()
        self.input_extensiones = QLineEdit()
        self.input_extensiones.setPlaceholderText("pdf, docx, txt (separadas por comas)")
        
        lbl_tip_ext = QLabel("💡 Tip: Escriba '*' para incluir todos los archivos.")
        lbl_tip_ext.setStyleSheet("color: #666; font-size: 11px; margin-top: 4px; padding-left: 2px;")
        
        self.container_ext.addWidget(self.input_extensiones)
        self.container_ext.addWidget(lbl_tip_ext)
        self.container_ext.setSpacing(0)

        # 4. Estado Activo
        self.check_activa = QCheckBox("Habilitar regla inmediatamente")
        self.check_activa.setChecked(True)

        # Añadir filas al formulario
        lbl_car = QLabel("Carpeta:"); lbl_car.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_car, self.combo_carpetas)
        
        lbl_nom = QLabel("Nombre:"); lbl_nom.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_nom, self.input_nombre_regla)
        
        lbl_ext = QLabel("Extensiones:"); lbl_ext.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_ext, self.container_ext)
        
        layout_form.addRow("", self.check_activa)

        layout_form_container.addLayout(layout_form)
        layout_form_container.addStretch()

        # Botón Agregar Regla (Estilo Amarillo Primario)
        self.btn_agregar_regla = QPushButton("AGREGAR REGLA")
        self.btn_agregar_regla.setObjectName("BtnPrimario")
        self.btn_agregar_regla.setCursor(Qt.PointingHandCursor)
        self.btn_agregar_regla.clicked.connect(self.agregar_nueva_regla)
        layout_form_container.addWidget(self.btn_agregar_regla)

        split_layout.addWidget(self.panel_config)

        # =========================================================================
        # PANEL DERECHO: VISUALIZACIÓN (Tabla)
        # =========================================================================
        self.panel_tabla = QFrame()
        self.panel_tabla.setObjectName("PanelGlass")
        
        layout_tabla_v = QVBoxLayout(self.panel_tabla)
        layout_tabla_v.setContentsMargins(10, 15, 10, 10)

        head_tabla = QHBoxLayout()
        lbl_tabla_tit = QLabel("Reglas Existentes")
        lbl_tabla_tit.setStyleSheet("color: white; font-weight: bold; font-size: 18px; background: transparent;")
        
        self.lbl_count = QLabel("(3 reglas)")
        self.lbl_count.setStyleSheet("color: #666; font-size: 14px; margin-left: 8px; background: transparent;")
        
        head_tabla.addWidget(lbl_tabla_tit)
        head_tabla.addWidget(self.lbl_count)
        head_tabla.addStretch()
        
        # Input de búsqueda rápida en tabla (Toque moderno extra)
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar regla...")
        self.input_busqueda.setFixedWidth(200)
        self.input_busqueda.setStyleSheet("padding: 6px 10px; font-size: 12px; border-radius: 6px;")
        head_tabla.addWidget(self.input_busqueda)

        layout_tabla_v.addLayout(head_tabla)

        # Tabla de visualización (Sin bordes, transparente)
        self.tabla_reglas = QTableWidget()
        self.tabla_reglas.setColumnCount(4)
        self.tabla_reglas.setHorizontalHeaderLabels(["ID", "Nombre de Regla", "Extensiones", "Estado"])
        
        # Configuraciones de comportamiento de la tabla
        self.tabla_reglas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_reglas.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_reglas.setEditTriggers(QAbstractItemView.NoEditTriggers) # No editar directo en tabla para diseño limpio
        self.tabla_reglas.setShowGrid(False)
        self.tabla_reglas.verticalHeader().setVisible(False)
        
        # Ajuste de columnas
        header = self.tabla_reglas.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID pequeño
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Nombre ancho
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Ext medio
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Estado medio

        layout_tabla_v.addWidget(self.tabla_reglas)

        # Botón Eliminar Regla (Estilo Peligro Rojo Transparente)
        self.btn_eliminar_regla = QPushButton("ELIMINAR REGLA SELECCIONADA")
        self.btn_eliminar_regla.setObjectName("BtnPeligro")
        self.btn_eliminar_regla.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar_regla.clicked.connect(self.eliminar_regla_seleccionada)
        layout_tabla_v.addWidget(self.btn_eliminar_regla)

        split_layout.addWidget(self.panel_tabla)
        
        # Añadir split central al layout principal
        layout_principal.addLayout(split_layout)

        # =========================================================================
        # BOTÓN INFERIOR (Volver)
        # =========================================================================
        footer_layout = QHBoxLayout()
        self.btn_volver = QPushButton("← Volver al Panel Resumen")
        self.btn_volver.setObjectName("BtnSecundario")
        self.btn_volver.setFixedWidth(220)
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.clicked.connect(self.callback_regresar)
        
        footer_layout.addWidget(self.btn_volver)
        footer_layout.addStretch()
        
        layout_principal.addLayout(footer_layout)

    # =========================================================================
    # LÓGICA (Adaptada para RAM y Nuevo Diseño)
    # =========================================================================
    
    def _cargar_datos_prueba(self):
        """Datos Mock para visualizar el diseño sin DB real"""
        # Poblar combo
        carpetas = ["unellez", "trabajo_final", "descargas_temp"]
        self.combo_carpetas.addItems(carpetas)
        
        # Poblar Tabla
        datos = [
            ("9", "programacion", "txt,jpeg,java", True),
            ("8", "cualquiera", "* (Cualquiera)", True),
            ("7", "documentos_pdf", "pdf", False),
        ]
        self._llenar_tabla(datos)

    def _llenar_tabla(self, filas):
        """Método genérico para llenar la tabla con estilo moderno"""
        self.tabla_reglas.setRowCount(0)
        self.lbl_count.setText(f"({len(filas)} reglas)")
        
        for idx, fila in enumerate(filas):
            self.tabla_reglas.insertRow(idx)
            id_regla, nombre, ext, activa = fila
            
            # ID (Centrado y gris)
            item_id = QTableWidgetItem(str(id_regla))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setForeground(QColor("#666"))
            self.tabla_reglas.setItem(idx, 0, item_id)
            
            # Nombre (Blanco)
            self.tabla_reglas.setItem(idx, 1, QTableWidgetItem(str(nombre)))
            
            # Extensiones (Toque amarillo suave si no es '*')
            item_ext = QTableWidgetItem(str(ext))
            if ext == "* (Cualquiera)":
                item_ext.setForeground(QColor("#888"))
            else:
                item_ext.setForeground(QColor("#fbbf24")) # Amarillo Oro
            self.tabla_reglas.setItem(idx, 2, item_ext)
            
            # Estado (Badge visual moderno)
            txt_estado = "🟢 Activa" if activa else "⚪ Inactiva"
            item_estado = QTableWidgetItem(txt_estado)
            if not activa:
                item_estado.setForeground(QColor("#888"))
            self.tabla_reglas.setItem(idx, 3, item_estado)
            
            # Setear alto de fila para que respire el diseño
            self.tabla_reglas.setRowHeight(idx, 45)

    def conectar_db(self):
        """Mismo método de conexión, asegurando CASCADE delete"""
        if not self.asistente: return None, None
        import sqlite3
        conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
        conn.execute("PRAGMA foreign_keys = ON") # Importante para borrar en cascada
        cursor = conn.cursor()
        # Estructura simplificada (asumiendo que las extensiones se guardan serializadas en 'extension')
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
        """Lógica real de carga de carpetas"""
        if not self.asistente: return
        self.combo_carpetas.blockSignals(True)
        self.combo_carpetas.clear()
        self.combo_carpetas.addItem("Seleccione carpeta...")
        
        try:
            conn, cursor = self.conectar_db()
            # Asumimos tabla 'directorios_destino' de Fase 1
            cursor.execute("SELECT nombre_alias FROM directorios_destino ORDER BY nombre_alias ASC")
            carpetas = [fila[0] for fila in cursor.fetchall() if fila[0]]
            conn.close()
            
            if carpetas:
                self.combo_carpetas.addItems(carpetas)
            else:
                self.input_nombre_regla.setPlaceholderText("Primero agregue carpetas en Fase 1")
                self.input_nombre_regla.setEnabled(False)
        except Exception as e:
            print(f"Error base datos: {e}")
        self.combo_carpetas.blockSignals(False)

    def agregar_nueva_regla(self):
        """INSERT optimizado (RAM friendly)"""
        carpeta = self.combo_carpetas.currentText()
        nombre = self.input_nombre_regla.text().strip()
        
        # Procesar extensiones desde QLineEdit (Mucho más ligero que leer QListWidget)
        ext_raw = self.input_extensiones.text().strip()
        activa = 1 if self.check_activa.isChecked() else 0

        # Validaciones básicas
        if self.combo_carpetas.currentIndex() == 0:
            self._mostrar_alerta("Falta Destino", "Seleccione una carpeta objetivo.")
            return
        if not nombre:
            self._mostrar_alerta("Campo Requerido", "Asigne un nombre a la regla.")
            self.input_nombre_regla.setFocus()
            return
        if not ext_raw:
            self._mostrar_alerta("Campo Requerido", "Escriba al menos una extensión o '*'.")
            self.input_extensiones.setFocus()
            return

        # Normalizar extensiones: limpiar espacios, quitar puntos extra
        if ext_raw != "*":
            lista_ext = [e.strip().lstrip('.').lower() for e in ext_raw.split(',') if e.strip()]
            ext_serializada = ",".join(lista_ext)
        else:
            ext_serializada = None # NULL en DB significa 'Cualquiera'

        # Intento de guardado mock/real
        if not self.asistente:
            print(f"MOCK INSERT: {nombre}, Ext: {ext_serializada}, Carpeta: {carpeta}, Activa: {activa}")
            # Añadir visualmente a la prueba
            current_rows = self.tabla_reglas.rowCount()
            self.tabla_reglas.insertRow(0)
            self.tabla_reglas.setItem(0,0, QTableWidgetItem("NUEVO"))
            self.tabla_reglas.setItem(0,1, QTableWidgetItem(nombre))
            self.tabla_reglas.setItem(0,2, QTableWidgetItem(ext_serializada if ext_serializada else "* (Cualquiera)"))
            self.tabla_reglas.setItem(0,3, QTableWidgetItem("🟢 Activa" if activa else "⚪ Inactiva"))
            self.tabla_reglas.setRowHeight(0, 45)
            self._limpiar_formulario()
            return

        # Lógica Real SQL
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("""
                INSERT INTO reglas_organizacion (nombre, extension, carpeta_destino, activa)
                VALUES (?, ?, ?, ?)
            """, (nombre, ext_serializada, carpeta, activa))
            conn.commit()
            conn.close()
            
            self._limpiar_formulario()
            # Recargar tabla (necesitas implementar cargar_reglas_por_carpeta similar al original)
            # self.cargar_reglas_por_carpeta() 
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def eliminar_regla_seleccionada(self):
        fila_sel = self.tabla_reglas.currentRow()
        if fila_sel < 0:
            self._mostrar_alerta("Selección requerida", "Elija una regla de la tabla para eliminar.")
            return
        
        id_regla = self.tabla_reglas.item(fila_sel, 0).text()
        nombre_regla = self.tabla_reglas.item(fila_sel, 1).text()

        # Custom MessageBox con estilo
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"¿Está seguro de eliminar la regla '{nombre_regla}'?")
        msg.setInformativeText("Esta acción no se puede deshacer.")
        btn_si = msg.addButton("Eliminar", QMessageBox.YesRole)
        msg.addButton("Cancelar", QMessageBox.NoRole)
        
        # Aplicar estilo al msgbox (toque amarillo al botón default)
        msg.setStyleSheet(QSS_MODERNO + "QPushButton { padding: 8px 20px; min-width: 80px; }")
        
        msg.exec_()

        if msg.clickedButton() == btn_si:
            if not self.asistente:
                print(f"MOCK DELETE: ID {id_regla}")
                self.tabla_reglas.removeRow(fila_sel)
                return

            try:
                conn, cursor = self.conectar_db()
                cursor.execute("DELETE FROM reglas_organizacion WHERE id = ?", (id_regla,))
                conn.commit()
                conn.close()
                # self.cargar_reglas_por_carpeta() # Recargar real
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def _limpiar_formulario(self):
        self.input_nombre_regla.clear()
        self.input_extensiones.clear()
        self.check_activa.setChecked(True)
        self.input_nombre_regla.setFocus()

    def _mostrar_alerta(self, titulo, texto):
        """MessageBox estilizado rápido"""
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet(QSS_MODERNO + "QPushButton { padding: 8px 20px; }")
        msg.exec_()

# =============================================================================
# EJEMPLO DE EJECUCIÓN (Para probar el diseño inmediatamente)
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configuración de tipografía global para mejor renderizado
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Crear contenedor principal para simular la ventana de la App con transparencia
    window = QWidget()
    window.setWindowTitle("PyOrganizer - Panel de Control Moderno")
    window.resize(1280, 800)
    
    # --- CLAVE PARA LA TRANSPARENCIA ---
    window.setAttribute(Qt.WA_TranslucentBackground) # Fondo de ventana transparente
    # window.setWindowFlags(Qt.FramelessWindowHint) # Opcional: quitar bordes de Windows
    
    # Fondo falso detrás (para simular el escritorio si no usas Frameless)
    # window.setStyleSheet("background-color: #111;") 

    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(0,0,0,0)

    # Instanciar la vista
    vista = VistaReglasOrganizacion()
    main_layout.addWidget(vista)

    window.show()
    sys.exit(app.exec_())