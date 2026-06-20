import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QFormLayout, 
                               QComboBox, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QApplication, 
                               QAbstractItemView, QCheckBox, QScrollArea)
from PySide6.QtGui import QFont, QColor, QCursor
from PySide6.QtCore import Qt
import os
from app.signals import app_signals

# =============================================================================
# HOJA DE ESTILO MAESTRA (QSS) - Diseño Moderno, Transparente y Amarillo
# =============================================================================
QSS_MODERNO = """
    /* Fondo principal translúcido */
    QWidget#VistaPrincipal {
        background-color: rgba(20, 20, 22, 150);
    }

    QLabel {
        color: #e5e7eb;
        font-family: 'Segoe UI', sans-serif;
        background: transparent;
    }

    /* Paneles con efecto Glassmorphism */
    QFrame#PanelGlass {
        background-color: rgba(35, 35, 40, 180);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 30);
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
        border: 2px solid #fbbf24;
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
        background-color: #eab308;
        border: 1px solid #eab308;
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
        background-color: rgba(239, 68, 68, 40);
        color: #ef4444;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid rgba(239, 68, 68, 100);
    }
    QPushButton#BtnPeligro:hover {
        background-color: rgba(239, 68, 68, 255);
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
        background-color: rgba(234, 179, 8, 30);
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

    /* Barra de desplazamiento */
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
        background: #eab308;
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
        self.callback_regresar = callback_regresar if callback_regresar else lambda: print("Regresando...")
        
        self.setStyleSheet(QSS_MODERNO)
        
        # 1. Inicializamos la UI general
        self.init_ui()
        
        # 2. Inicializamos el chat asistente (Flotante)
        self.inicializar_chat_asistente()
        
        # 3. Cargar datos
        try:
            self.actualizar_selector_carpetas()
            self.agregar_mensaje_sistema("Estoy listo para ayudarte a crear o modificar reglas de organización.")
        except Exception:
            # Fallback para vista de prueba si no hay base de datos
            self._cargar_datos_prueba()

        # Conectar señal para refrescar destinos cuando cambian
        try:
            app_signals.destinos_changed.connect(self.actualizar_selector_carpetas)
        except Exception:
            pass

        # Refrescar lista de reglas cuando el asistente crea/elimina una
        try:
            from app.signals import app_signals as _sigs
            _sigs.stats_changed.connect(self._refrescar_por_senal)
        except Exception:
            pass

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)

        # =========================================================================
        # CABECERA
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

        # Contenedores centrales
        split_layout = QHBoxLayout()
        split_layout.setSpacing(30)

        # =========================================================================
        # PANEL IZQUIERDO: CONFIGURACIÓN
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

        self.combo_carpetas = QComboBox()
        self.combo_carpetas.addItem("Seleccione carpeta...")
        self.combo_carpetas.currentTextChanged.connect(self.cargar_reglas_por_carpeta)

        self.input_nombre_regla = QLineEdit()
        self.input_nombre_regla.setPlaceholderText("Ej: Filtro de Documentos")

        self.container_ext = QVBoxLayout()
        self.input_extensiones = QLineEdit()
        self.input_extensiones.setPlaceholderText("pdf, docx, txt (separadas por comas)")
        lbl_tip_ext = QLabel("💡 Tip: Escriba '*' para incluir todos los archivos.")
        lbl_tip_ext.setStyleSheet("color: #666; font-size: 11px; margin-top: 4px; padding-left: 2px;")
        self.container_ext.addWidget(self.input_extensiones)
        self.container_ext.addWidget(lbl_tip_ext)
        self.container_ext.setSpacing(0)

        self.container_keywords = QVBoxLayout()
        self.input_palabras_clave = QLineEdit()
        self.input_palabras_clave.setPlaceholderText("factura, proyecto, tarea")
        lbl_tip_keywords = QLabel("💡 Tip: Separe palabras clave o términos de nombre con comas.")
        lbl_tip_keywords.setStyleSheet("color: #666; font-size: 11px; margin-top: 4px; padding-left: 2px;")
        self.container_keywords.addWidget(self.input_palabras_clave)
        self.container_keywords.addWidget(lbl_tip_keywords)
        self.container_keywords.setSpacing(0)

        self.check_activa = QCheckBox("Habilitar regla inmediatamente")
        self.check_activa.setChecked(True)

        lbl_car = QLabel("Carpeta:"); lbl_car.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_car, self.combo_carpetas)
        lbl_nom = QLabel("Nombre:"); lbl_nom.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_nom, self.input_nombre_regla)
        lbl_ext = QLabel("Extensiones:"); lbl_ext.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_ext, self.container_ext)
        lbl_keywords = QLabel("Palabras clave/Nombre:"); lbl_keywords.setStyleSheet("color: #888; font-weight: bold;")
        layout_form.addRow(lbl_keywords, self.container_keywords)
        layout_form.addRow("", self.check_activa)

        layout_form_container.addLayout(layout_form)
        layout_form_container.addStretch()

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
        
        self.lbl_count = QLabel("(0 reglas)")
        self.lbl_count.setStyleSheet("color: #666; font-size: 14px; margin-left: 8px; background: transparent;")
        
        head_tabla.addWidget(lbl_tabla_tit)
        head_tabla.addWidget(self.lbl_count)
        head_tabla.addStretch()
        layout_tabla_v.addLayout(head_tabla)

        self.tabla_reglas = QTableWidget()
        self.tabla_reglas.setColumnCount(5)
        self.tabla_reglas.setHorizontalHeaderLabels(["ID", "Nombre de Regla", "Extensiones", "Palabras clave", "Estado"])
        self.tabla_reglas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_reglas.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_reglas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_reglas.setShowGrid(False)
        self.tabla_reglas.verticalHeader().setVisible(False)
        
        header = self.tabla_reglas.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout_tabla_v.addWidget(self.tabla_reglas)

        self.btn_eliminar_regla = QPushButton("ELIMINAR REGLA SELECCIONADA")
        self.btn_eliminar_regla.setObjectName("BtnPeligro")
        self.btn_eliminar_regla.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar_regla.clicked.connect(self.eliminar_regla_seleccionada)
        layout_tabla_v.addWidget(self.btn_eliminar_regla)

        split_layout.addWidget(self.panel_tabla)
        layout_principal.addLayout(split_layout)

        # =========================================================================
        # BOTÓN INFERIOR (Volver y Chat Burbuja)
        # =========================================================================
        layout_inferior = QHBoxLayout()
        layout_inferior.setContentsMargins(0, 10, 0, 0)
        
        # Botón Volver
        self.btn_volver = QPushButton("← Volver al Panel Resumen")
        self.btn_volver.setObjectName("BtnSecundario")
        self.btn_volver.setFixedWidth(240)
        self.btn_volver.setFixedHeight(45)
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.clicked.connect(self.callback_regresar)
        layout_inferior.addWidget(self.btn_volver, alignment=Qt.AlignBottom | Qt.AlignLeft)

        layout_inferior.addStretch()

        # Botón estilo "Burbuja" para abrir el chat
        self.btn_abrir_chat = QPushButton("💬 Asistente")
        self.btn_abrir_chat.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_abrir_chat.setFixedSize(140, 45)
        self.btn_abrir_chat.setStyleSheet("""
            QPushButton {
                background-color: rgba(24, 24, 27, 0.95); 
                color: #eab308; font-weight: bold; font-size: 14px;
                border-radius: 22px; 
                border: 1px solid rgba(234, 179, 8, 0.5);
            }
            QPushButton:hover {
                background-color: rgba(234, 179, 8, 0.15);
                border: 1px solid #eab308;
            }
        """)
        self.btn_abrir_chat.clicked.connect(self.mostrar_chat)
        layout_inferior.addWidget(self.btn_abrir_chat, alignment=Qt.AlignBottom | Qt.AlignRight)
        
        layout_principal.addLayout(layout_inferior)

    # =========================================================================
    # LÓGICA DEL ASISTENTE VIRTUAL (FLOTANTE OVERLAY)
    # =========================================================================
    def inicializar_chat_asistente(self):
        self.widget_chat = QFrame(self)
        self.widget_chat.setFixedSize(360, 320)
        self.widget_chat.setStyleSheet("""
            QFrame#chat_principal {
                background-color: rgba(24, 24, 27, 0.98); 
                border-radius: 12px; 
                border: 1px solid rgba(234, 179, 8, 0.5);
            }
        """)
        self.widget_chat.setObjectName("chat_principal")
        self.widget_chat.hide() 

        distribucion_chat = QVBoxLayout(self.widget_chat)
        distribucion_chat.setContentsMargins(0,0,0,0)
        distribucion_chat.setSpacing(0)

        # Cabecera Chat
        marco_cabecera = QFrame()
        marco_cabecera.setStyleSheet("background-color: rgba(234, 179, 8, 0.15); border-top-left-radius: 12px; border-top-right-radius: 12px; border: none; border-bottom: 1px solid rgba(234, 179, 8, 0.2);")
        distribucion_cabecera = QHBoxLayout(marco_cabecera)
        distribucion_cabecera.setContentsMargins(15, 8, 15, 8)
        
        titulo_cabecera = QLabel("💬 Asistente de Reglas")
        titulo_cabecera.setStyleSheet("color: #eab308; font-weight: 700; font-size: 13px; background: transparent; border: none;")
        
        btn_cerrar_chat = QPushButton("✖")
        btn_cerrar_chat.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cerrar_chat.setFixedSize(24, 24)
        btn_cerrar_chat.setStyleSheet("""
            QPushButton { background: transparent; color: #a1a1aa; font-weight: bold; border: none; font-size: 14px; }
            QPushButton:hover { color: #ef4444; }
        """)
        btn_cerrar_chat.clicked.connect(self.ocultar_chat)

        distribucion_cabecera.addWidget(titulo_cabecera)
        distribucion_cabecera.addStretch()
        distribucion_cabecera.addWidget(btn_cerrar_chat)
        distribucion_chat.addWidget(marco_cabecera)

        # Cuerpo del Chat
        cuerpo_chat = QWidget()
        cuerpo_chat.setStyleSheet("background: transparent; border: none;")
        distribucion_cuerpo = QVBoxLayout(cuerpo_chat)
        distribucion_cuerpo.setContentsMargins(10, 10, 10, 10)
        distribucion_cuerpo.setSpacing(10)
        
        self.area_mensajes = QScrollArea()
        self.area_mensajes.setWidgetResizable(True)
        self.area_mensajes.setStyleSheet("border: none; background: transparent;")
        self.area_mensajes.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.area_mensajes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.contenedor_mensajes = QWidget()
        self.contenedor_mensajes.setStyleSheet("background: transparent;")
        self.lista_mensajes = QVBoxLayout(self.contenedor_mensajes)
        self.lista_mensajes.setContentsMargins(0,0,0,0)
        self.lista_mensajes.setSpacing(8)
        self.lista_mensajes.addStretch()
        self.area_mensajes.setWidget(self.contenedor_mensajes)
        distribucion_cuerpo.addWidget(self.area_mensajes)

        # Entrada de Texto Chat
        self.entrada_texto_chat = QLineEdit()
        self.entrada_texto_chat.setPlaceholderText("Escribe un comando o duda...")
        self.entrada_texto_chat.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.4); 
                color: #ffffff; padding: 10px; 
                border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLineEdit:focus { border: 1px solid #eab308; }
        """)
        self.entrada_texto_chat.setFixedHeight(38)
        self.entrada_texto_chat.returnPressed.connect(self.enviar_comando_chat)
        distribucion_cuerpo.addWidget(self.entrada_texto_chat)

        distribucion_chat.addWidget(cuerpo_chat)

    def posicionar_chat_flotante(self):
        if hasattr(self, 'widget_chat'):
            margen_x = 40
            margen_y = 40
            pos_x = self.width() - self.widget_chat.width() - margen_x
            pos_y = self.height() - self.widget_chat.height() - margen_y
            self.widget_chat.move(pos_x, pos_y)

    def mostrar_chat(self):
        self.posicionar_chat_flotante()
        self.widget_chat.raise_()
        self.widget_chat.show()
        self.btn_abrir_chat.hide()
        self.entrada_texto_chat.setFocus()

    def ocultar_chat(self):
        self.widget_chat.hide()
        self.btn_abrir_chat.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'widget_chat') and self.widget_chat.isVisible():
            self.posicionar_chat_flotante()

    def agregar_mensaje_sistema(self, texto):
        etiqueta = QLabel(f"<b>Sistema:</b> {texto}")
        etiqueta.setStyleSheet("color: #e4e4e7; background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 6px; font-size: 11px;")
        etiqueta.setWordWrap(True)
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta)
        self.area_mensajes.verticalScrollBar().setValue(self.area_mensajes.verticalScrollBar().maximum())

    def enviar_comando_chat(self):
        texto = self.entrada_texto_chat.text().strip()
        if not texto: return
        
        etiqueta_usuario = QLabel(f"<b>Tú:</b> {texto}")
        etiqueta_usuario.setStyleSheet("color: #a1a1aa; font-size: 11px; padding: 4px;")
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta_usuario)

        if self.asistente:
            respuesta = self.asistente.procesar_peticion(texto)
            if isinstance(respuesta, dict) and 'message' in respuesta:
                self.agregar_mensaje_sistema(respuesta.get('message'))
            else:
                self.agregar_mensaje_sistema(str(respuesta))
        else:
            self.agregar_mensaje_sistema("El asistente no está conectado en modo prueba.")

        self.entrada_texto_chat.clear()
        self.area_mensajes.verticalScrollBar().setValue(self.area_mensajes.verticalScrollBar().maximum())
        
        # Al igual que en la config, refrescamos las listas tras una posible orden del asistente
        self.actualizar_selector_carpetas()
        self.cargar_reglas_por_carpeta()

    # =========================================================================
    # LÓGICA BASE DE DATOS Y REGLAS
    # =========================================================================
    def conectar_db(self):
        import sqlite3
        from pathlib import Path
        # Forzar el uso de la BD central
        db_path = Path(__file__).resolve().parent.parent / 'recursos' / 'organizador.db'
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        return conn, cursor

    def actualizar_selector_carpetas(self):
        if not self.asistente: return
        self.combo_carpetas.blockSignals(True)
        self.combo_carpetas.clear()
        self.combo_carpetas.addItem("Seleccione carpeta...")
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT nombre_alias, ruta FROM directorios_destino ORDER BY nombre_alias ASC")
            filas = cursor.fetchall()
            conn.close()

            carpetas = []
            for nombre_alias, ruta in filas:
                try:
                    if ruta and os.path.exists(ruta):
                        carpetas.append(nombre_alias)
                except Exception:
                    # si no podemos verificar la ruta, aún añadimos el alias
                    carpetas.append(nombre_alias)

            if carpetas:
                self.combo_carpetas.addItems(carpetas)
                self.input_nombre_regla.setEnabled(True)
            else:
                self.input_nombre_regla.setPlaceholderText("Primero agregue carpetas en Fase 1")
                self.input_nombre_regla.setEnabled(False)
        except Exception as e:
            print(f"Error base datos: {e}")
        self.combo_carpetas.blockSignals(False)
        self.cargar_reglas_por_carpeta()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            # Forzar actualización dinámica cada vez que la vista se muestra
            self.actualizar_selector_carpetas()
        except Exception:
            pass

    def _refrescar_por_senal(self):
        """Refresca selector de carpetas y lista de reglas al recibir stats_changed."""
        try:
            self.actualizar_selector_carpetas()
        except Exception:
            pass

    def cargar_reglas_por_carpeta(self):
        carpeta_actual = self.combo_carpetas.currentText()
        if not carpeta_actual or carpeta_actual == "Seleccione carpeta..." or not self.asistente:
            self.tabla_reglas.setRowCount(0)
            self.lbl_count.setText("(0 reglas)")
            return

        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT id, nombre, extension, palabras_clave, activa FROM reglas_organizacion WHERE carpeta_destino = ? ORDER BY id DESC", (carpeta_actual,))
            filas = cursor.fetchall()
            conn.close()

            self.tabla_reglas.setRowCount(0)
            self.lbl_count.setText(f"({len(filas)} reglas)")
            for idx, fila in enumerate(filas):
                self.tabla_reglas.insertRow(idx)
                
                # ID
                item_id = QTableWidgetItem(str(fila[0]))
                item_id.setTextAlignment(Qt.AlignCenter)
                item_id.setForeground(QColor("#666"))
                self.tabla_reglas.setItem(idx, 0, item_id)
                
                # Nombre
                self.tabla_reglas.setItem(idx, 1, QTableWidgetItem(str(fila[1])))
                
                # Extensión
                ext_val = fila[2] if fila[2] else "* (Cualquiera)"
                item_ext = QTableWidgetItem(ext_val)
                if ext_val == "* (Cualquiera)":
                    item_ext.setForeground(QColor("#888"))
                else:
                    item_ext.setForeground(QColor("#fbbf24"))
                self.tabla_reglas.setItem(idx, 2, item_ext)
                
                # Palabras clave / Nombre
                palabras_val = fila[3] if fila[3] else "-"
                item_palabras = QTableWidgetItem(str(palabras_val))
                item_palabras.setForeground(QColor("#e5e7eb"))
                self.tabla_reglas.setItem(idx, 3, item_palabras)
                
                # Estado
                txt_estado = "🟢 Activa" if fila[4] == 1 else "⚪ Inactiva"
                item_estado = QTableWidgetItem(txt_estado)
                if fila[4] == 0: item_estado.setForeground(QColor("#888"))
                self.tabla_reglas.setItem(idx, 4, item_estado)
                
                self.tabla_reglas.setRowHeight(idx, 45)
        except Exception as e:
            print(f"Error al cargar reglas: {e}")

    def agregar_nueva_regla(self):
        carpeta = self.combo_carpetas.currentText()
        nombre = self.input_nombre_regla.text().strip()
        ext_raw = self.input_extensiones.text().strip()
        palabras_raw = self.input_palabras_clave.text().strip()
        activa = 1 if self.check_activa.isChecked() else 0

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

        if ext_raw != "*":
            lista_ext = [e.strip().lstrip('.').lower() for e in ext_raw.split(',') if e.strip()]
            # Guardar en tabla separada para compatibilidad con nueva estructura
            ext_serializada = ",".join(lista_ext)
        else:
            ext_serializada = None
        palabras_serializadas = None
        if palabras_raw:
            palabras_serializadas = ",".join([p.strip().lower() for p in palabras_raw.split(',') if p.strip()])

        if not self.asistente:
            self._mostrar_alerta("Modo Prueba", f"Regla '{nombre}' añadida virtualmente.")
            self._limpiar_formulario()
            return

        try:
            conn, cursor = self.conectar_db()
            cursor.execute("INSERT INTO reglas_organizacion (nombre, extension, palabras_clave, carpeta_destino, activa) VALUES (?, ?, ?, ?, ?)", 
                           (nombre, ext_serializada, palabras_serializadas, carpeta, activa))
            
            # Obtener el ID de la regla recién insertada
            regla_id = cursor.lastrowid
            
            # Guardar también en la nueva tabla regla_extensiones para compatibilidad
            if ext_raw and ext_raw != "*":
                for ext in lista_ext:
                    ext_normalizada = f".{ext}" if not ext.startswith(".") else ext
                    cursor.execute("INSERT INTO regla_extensiones (regla_id, extension) VALUES (?, ?)", (regla_id, ext_normalizada))
                    
            conn.commit()
            conn.close()
            
            self._limpiar_formulario()
            self.cargar_reglas_por_carpeta() 
            
            # Notificar que se actualizaron los stats/reglas si es posible
            try:
                from app.signals import app_signals
                app_signals.stats_changed.emit()
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def eliminar_regla_seleccionada(self):
        fila_sel = self.tabla_reglas.currentRow()
        if fila_sel < 0:
            self._mostrar_alerta("Selección requerida", "Elija una regla de la tabla para eliminar.")
            return
        
        id_regla = self.tabla_reglas.item(fila_sel, 0).text()
        nombre_regla = self.tabla_reglas.item(fila_sel, 1).text()

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"¿Está seguro de eliminar la regla '{nombre_regla}'?")
        msg.setInformativeText("Esta acción no se puede deshacer.")
        btn_si = msg.addButton("Eliminar", QMessageBox.YesRole)
        msg.addButton("Cancelar", QMessageBox.NoRole)
        msg.setStyleSheet(QSS_MODERNO + "QPushButton { padding: 8px 20px; min-width: 80px; }")
        msg.exec_()

        if msg.clickedButton() == btn_si:
            if not self.asistente: return
            try:
                conn, cursor = self.conectar_db()
                cursor.execute("DELETE FROM reglas_organizacion WHERE id = ?", (id_regla,))
                conn.commit()
                conn.close()
                self.cargar_reglas_por_carpeta()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def _limpiar_formulario(self):
        self.input_nombre_regla.clear()
        self.input_extensiones.clear()
        self.input_palabras_clave.clear()
        self.check_activa.setChecked(True)
        self.input_nombre_regla.setFocus()

    def _mostrar_alerta(self, titulo, texto):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        msg.setStyleSheet(QSS_MODERNO + "QPushButton { padding: 8px 20px; }")
        msg.exec_()

    def _cargar_datos_prueba(self):
        self.combo_carpetas.addItems(["unellez", "trabajo_final"])
        self.tabla_reglas.setRowCount(0)
        self.lbl_count.setText("(1 regla demo)")
        self.tabla_reglas.insertRow(0)
        self.tabla_reglas.setItem(0, 0, QTableWidgetItem("1"))
        self.tabla_reglas.setItem(0, 1, QTableWidgetItem("Demo"))
        self.tabla_reglas.setItem(0, 2, QTableWidgetItem("pdf"))
        self.tabla_reglas.setItem(0, 3, QTableWidgetItem("🟢 Activa"))

# Bloque de prueba (solo se ejecuta si corres este archivo directamente)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = QWidget()
    window.setWindowTitle("PyOrganizer - Reglas con Chat")
    window.resize(1280, 800)
    window.setAttribute(Qt.WA_TranslucentBackground) 
    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(0,0,0,0)
    vista = VistaReglasOrganizacion()
    main_layout.addWidget(vista)
    window.show()
    sys.exit(app.exec_())