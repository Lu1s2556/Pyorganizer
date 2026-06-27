from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QScrollArea, QComboBox)
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt
from app.signals import app_signals
from pathlib import Path
import sqlite3

class VistaConfiguracionGlobal(QWidget):
    def __init__(self, asistente, callback_regresar, parent=None):
        super().__init__(parent)
        self.asistente = asistente
        self.callback_regresar = callback_regresar 
        
        # Inicializamos la UI y el chat flotante
        self.inicializar_chat_asistente()
        self.init_ui()
        
        self.cargar_origenes()
        self.cargar_destinos()
        
        try:
            self.agregar_mensaje_sistema("Estoy aquí por si necesitas ayuda configurando.")
        except Exception:
            pass
            
        try:
            app_signals.destinos_changed.connect(self.cargar_destinos)
            app_signals.origenes_changed.connect(self.cargar_origenes)
        except Exception:
            pass

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)

        # ==========================================
        # CABECERA
        # ==========================================
        head = QVBoxLayout()
        tit = QLabel("Configuración Global de Directorios")
        tit.setStyleSheet("color: white; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;")
        sub = QLabel("Fase 1: Gestione los flujos de entrada (Orígenes) y las carpetas de clasificación (Destinos).")
        sub.setStyleSheet("color: #a1a1aa; font-size: 14px;")
        head.addWidget(tit)
        head.addWidget(sub)
        layout_principal.addLayout(head)

        # ==========================================
        # ESTILOS OPTIMIZADOS
        # ==========================================
        estilo_frame = "background-color: rgba(24, 24, 27, 0.6); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px;"
        estilo_tabla = """
            QTableWidget { background-color: rgba(0, 0, 0, 0.2); color: white; gridline-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; }
            QHeaderView::section { background-color: rgba(255, 255, 255, 0.05); color: #a1a1aa; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.02); }
            QTableWidget::item:selected { background-color: rgba(234, 179, 8, 0.2); color: #eab308; font-weight: bold; }
        """
        estilo_input = "background-color: rgba(0, 0, 0, 0.3); color: white; padding: 12px; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px;"
        estilo_btn_amarillo = "QPushButton { background: #eab308; color: #000; font-weight: bold; padding: 10px 15px; border-radius: 6px; border: none; } QPushButton:hover { background: #facc15; }"
        estilo_btn_rojo = "QPushButton { background: rgba(239, 68, 68, 0.15); color: #ef4444; font-weight: bold; padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3); } QPushButton:hover { background: rgba(239, 68, 68, 0.25); }"

        columnas_layout = QHBoxLayout()
        columnas_layout.setSpacing(25)

        # ==========================================
        # COLUMNA IZQUIERDA: ORÍGENES
        # ==========================================
        frame_origen = QFrame()
        frame_origen.setStyleSheet(estilo_frame)
        layout_origen = QVBoxLayout(frame_origen)
        layout_origen.setSpacing(15)
        
        lbl_orig_tit = QLabel("📥 Carpetas de Origen (Monitoreadas)")
        lbl_orig_tit.setStyleSheet("color: white; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        layout_origen.addWidget(lbl_orig_tit)

        origen_input_layout = QHBoxLayout()
        self.input_ruta_origen = QLineEdit()
        self.input_ruta_origen.setPlaceholderText("Seleccione o pegue una ruta...")
        self.input_ruta_origen.setStyleSheet(estilo_input)
        btn_buscar_origen = QPushButton("📂")
        btn_buscar_origen.setStyleSheet("background: rgba(255,255,255,0.1); color: white; border: none; padding: 10px; border-radius: 8px;")
        btn_buscar_origen.clicked.connect(lambda: self.seleccionar_directorio(self.input_ruta_origen))
        origen_input_layout.addWidget(self.input_ruta_origen)
        origen_input_layout.addWidget(btn_buscar_origen)
        layout_origen.addLayout(origen_input_layout)

        origen_btn_layout = QHBoxLayout()
        btn_add_origen = QPushButton("Agregar Origen")
        btn_add_origen.setStyleSheet(estilo_btn_amarillo)
        btn_add_origen.clicked.connect(self.agregar_origen)
        btn_del_origen = QPushButton("Eliminar Seleccionados")
        btn_del_origen.setStyleSheet(estilo_btn_rojo)
        btn_del_origen.clicked.connect(self.eliminar_origen)
        origen_btn_layout.addWidget(btn_add_origen)
        origen_btn_layout.addWidget(btn_del_origen)
        layout_origen.addLayout(origen_btn_layout)

        self.tabla_origenes = QTableWidget()
        self.tabla_origenes.setColumnCount(3)
        self.tabla_origenes.setHorizontalHeaderLabels(["", "ID", "Ruta de Entrada"])
        self.tabla_origenes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_origenes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_origenes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_origenes.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_origenes.setFont(QFont("Segoe UI", 10))
        self.tabla_origenes.setShowGrid(False)
        self.tabla_origenes.setWordWrap(False)
        self.tabla_origenes.setStyleSheet(estilo_tabla)
        layout_origen.addWidget(self.tabla_origenes)

        columnas_layout.addWidget(frame_origen)

        # ==========================================
        # COLUMNA DERECHA: DESTINOS
        # ==========================================
        frame_destino = QFrame()
        frame_destino.setStyleSheet(estilo_frame)
        layout_destino = QVBoxLayout(frame_destino)
        layout_destino.setSpacing(15)

        lbl_dest_tit = QLabel("📤 Carpetas de Destino (Clasificación)")
        lbl_dest_tit.setStyleSheet("color: white; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        layout_destino.addWidget(lbl_dest_tit)

        destino_inputs = QVBoxLayout()
        self.input_alias_destino = QLineEdit()
        self.input_alias_destino.setPlaceholderText("Nombre/Alias de la carpeta (ej: universidad)")
        self.input_alias_destino.setStyleSheet(estilo_input)
        destino_inputs.addWidget(self.input_alias_destino)

        destino_ruta_layout = QHBoxLayout()
        self.input_ruta_destino = QLineEdit()
        self.input_ruta_destino.setPlaceholderText("Ruta del directorio destino...")
        self.input_ruta_destino.setStyleSheet(estilo_input)
        btn_buscar_destino = QPushButton("📂")
        btn_buscar_destino.setStyleSheet("background: rgba(255,255,255,0.1); color: white; border: none; padding: 10px; border-radius: 8px;")
        btn_buscar_destino.clicked.connect(lambda: self.seleccionar_directorio(self.input_ruta_destino))
        destino_ruta_layout.addWidget(self.input_ruta_destino)
        destino_ruta_layout.addWidget(btn_buscar_destino)
        destino_inputs.addLayout(destino_ruta_layout)
        layout_destino.addLayout(destino_inputs)

        destino_btn_layout = QHBoxLayout()
        btn_add_destino = QPushButton("Agregar Destino")
        btn_add_destino.setStyleSheet(estilo_btn_amarillo)
        btn_add_destino.clicked.connect(self.agregar_destino)
        btn_del_destino = QPushButton("Eliminar Selección")
        btn_del_destino.setStyleSheet(estilo_btn_rojo)
        btn_del_destino.clicked.connect(self.eliminar_destino)
        destino_btn_layout.addWidget(btn_add_destino)
        destino_btn_layout.addWidget(btn_del_destino)
        layout_destino.addLayout(destino_btn_layout)

        self.tabla_destinos = QTableWidget()
        self.tabla_destinos.setColumnCount(3)
        self.tabla_destinos.setHorizontalHeaderLabels(["ID", "Alias", "Ruta de Salida"])
        self.tabla_destinos.setFont(QFont("Segoe UI", 10))
        self.tabla_destinos.setShowGrid(False)
        self.tabla_destinos.setWordWrap(False)
        self.tabla_destinos.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_destinos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_destinos.setStyleSheet(estilo_tabla)
        layout_destino.addWidget(self.tabla_destinos)

        columnas_layout.addWidget(frame_destino)
        layout_principal.addLayout(columnas_layout, 1)

        # ==========================================
        # ZONA INFERIOR: BOTÓN VOLVER Y BOTÓN BURBUJA
        # ==========================================
        layout_inferior = QHBoxLayout()
        layout_inferior.setContentsMargins(0, 10, 0, 0)
        
        # 1. Botón Volver
        btn_volver = QPushButton("← VOLVER AL PANEL RESUMEN")
        btn_volver.setFixedWidth(240)
        btn_volver.setFixedHeight(45)
        btn_volver.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.05); color: #a1a1aa; font-weight: bold; padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); } 
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); color: white; }
        """)
        btn_volver.clicked.connect(self.callback_regresar)
        layout_inferior.addWidget(btn_volver, alignment=Qt.AlignBottom | Qt.AlignLeft)

        layout_inferior.addStretch()

        # 2. Botón estilo "Burbuja" para abrir el chat
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
        
        # Agregamos solo el botón burbuja al layout. El widget del chat flotará por encima.
        layout_inferior.addWidget(self.btn_abrir_chat, alignment=Qt.AlignBottom | Qt.AlignRight)
        
        layout_principal.addLayout(layout_inferior)

    # ==========================================
    # LÓGICA DEL ASISTENTE VIRTUAL (FLOTANTE OVERLAY)
    # ==========================================
    def inicializar_chat_asistente(self):
        """Crea la ventana del chat como un elemento libre que flota sobre la interfaz"""
        # IMPORTANTE: Se pasa 'self' como parent, pero NO se añade a ningún layout.
        # Esto permite que se dibuje por encima de todo.
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
        self.widget_chat.hide() # Oculto por defecto

        distribucion_chat = QVBoxLayout(self.widget_chat)
        distribucion_chat.setContentsMargins(0,0,0,0)
        distribucion_chat.setSpacing(0)

        # Cabecera con Botón de Cierre
        marco_cabecera = QFrame()
        marco_cabecera.setStyleSheet("background-color: rgba(234, 179, 8, 0.15); border-top-left-radius: 12px; border-top-right-radius: 12px; border: none; border-bottom: 1px solid rgba(234, 179, 8, 0.2);")
        distribucion_cabecera = QHBoxLayout(marco_cabecera)
        distribucion_cabecera.setContentsMargins(15, 8, 15, 8)
        
        titulo_cabecera = QLabel("💬 Asistente de Configuración")
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

        # Cuerpo del Chat (Mensajes)
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

        # Entrada de Texto
        self.entrada_texto_chat = QLineEdit()
        self.entrada_texto_chat.setPlaceholderText("Escribe un comando...")
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
        """Calcula las coordenadas para anclar el chat a la esquina inferior derecha"""
        if hasattr(self, 'widget_chat'):
            margen_x = 40
            margen_y = 40
            # Posición X: ancho de la ventana - ancho del chat - margen
            pos_x = self.width() - self.widget_chat.width() - margen_x
            # Posición Y: alto de la ventana - alto del chat - margen
            pos_y = self.height() - self.widget_chat.height() - margen_y
            
            self.widget_chat.move(pos_x, pos_y)

    def mostrar_chat(self):
        """Muestra el chat, lo posiciona y lo trae al frente (Z-Index)"""
        self.posicionar_chat_flotante()
        self.widget_chat.raise_()  # Traer por encima de todos los demás elementos
        self.widget_chat.show()
        self.btn_abrir_chat.hide()
        self.entrada_texto_chat.setFocus()

    def ocultar_chat(self):
        """Cierra el chat y vuelve a mostrar el botón burbuja"""
        self.widget_chat.hide()
        self.btn_abrir_chat.show()

    def resizeEvent(self, event):
        """Evento de ventana: mantiene el chat anclado si el usuario cambia el tamaño del programa"""
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

        respuesta = self.asistente.procesar_peticion(texto)

        if isinstance(respuesta, dict) and 'message' in respuesta:
            self.agregar_mensaje_sistema(respuesta.get('message'))
        else:
            self.agregar_mensaje_sistema(str(respuesta))

        self.entrada_texto_chat.clear()
        self.area_mensajes.verticalScrollBar().setValue(self.area_mensajes.verticalScrollBar().maximum())
        
        self.cargar_origenes()
        self.cargar_destinos()

    # ==========================================
    # UTILIDADES DE DIRECTORIO
    # ==========================================
    def seleccionar_directorio(self, campo_texto):
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if ruta: campo_texto.setText(ruta)

    # ==========================================
    # LÓGICA DE BASE DE DATOS (SQLITE)
    # ==========================================
    def conectar_db(self):
        import sqlite3
        conn = sqlite3.connect(str(self.asistente.modelo_org.db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS carpetas_monitoreadas (id INTEGER PRIMARY KEY AUTOINCREMENT, ruta TEXT NOT NULL UNIQUE, nombre_alias TEXT, activa BOOLEAN DEFAULT 1, fecha_agregada DATETIME DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS directorios_destino (id INTEGER PRIMARY KEY AUTOINCREMENT, ruta TEXT NOT NULL UNIQUE, nombre_alias TEXT)")
        conn.commit()
        return conn, cursor

    def cargar_origenes(self):
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT id, ruta FROM carpetas_monitoreadas WHERE activa = 1")
            filas = cursor.fetchall()
            conn.close()
            
            nuevos_ids = [str(f[0]) for f in filas]
            ids_actuales = [self.tabla_origenes.item(i, 1).text() for i in range(self.tabla_origenes.rowCount()) if self.tabla_origenes.item(i, 1)]
            if nuevos_ids == ids_actuales:
                return
            
            self.tabla_origenes.setRowCount(0)
            for idx, fila in enumerate(filas):
                self.tabla_origenes.insertRow(idx)
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Unchecked)
                self.tabla_origenes.setItem(idx, 0, checkbox)

                id_item = QTableWidgetItem(str(fila[0]))
                id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tabla_origenes.setItem(idx, 1, id_item)

                ruta_item = QTableWidgetItem(str(fila[1]))
                ruta_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tabla_origenes.setItem(idx, 2, ruta_item)
        except Exception: pass

    def agregar_origen(self):
        ruta = self.input_ruta_origen.text().strip()
        if not ruta: return
        alias = Path(ruta).name
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("INSERT INTO carpetas_monitoreadas (ruta, nombre_alias, activa) VALUES (?, ?, 1)", (ruta, alias))
            conn.commit(); conn.close()
            self.input_ruta_origen.clear(); self.cargar_origenes()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Carpeta ya monitorizada", "La carpeta seleccionada ya está siendo monitoreada.")
        except Exception:
            pass

    def eliminar_origen(self):
        ids_seleccionados = []
        for fila in range(self.tabla_origenes.rowCount()):
            check_item = self.tabla_origenes.item(fila, 0)
            if not check_item or check_item.checkState() != Qt.Checked:
                continue

            id_item = self.tabla_origenes.item(fila, 1)
            if id_item and id_item.text().isdigit():
                ids_seleccionados.append(int(id_item.text()))

        if not ids_seleccionados:
            return

        try:
            if getattr(self.asistente.modelo_org, 'gestor', None):
                self.asistente.modelo_org.gestor.eliminar_carpetas_monitoreadas(ids_seleccionados)
            else:
                conn, cursor = self.conectar_db()
                placeholders = ",".join(["?"] * len(ids_seleccionados))
                cursor.execute(f"DELETE FROM carpetas_monitoreadas WHERE id IN ({placeholders})", ids_seleccionados)
                conn.commit(); conn.close()
            self.cargar_origenes()
        except Exception:
            pass

    def cargar_destinos(self):
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("SELECT id, nombre_alias, ruta FROM directorios_destino")
            filas = cursor.fetchall()
            conn.close()
            
            nuevos_ids = [str(f[0]) for f in filas]
            ids_actuales = [self.tabla_destinos.item(i, 0).text() for i in range(self.tabla_destinos.rowCount()) if self.tabla_destinos.item(i, 0)]
            if nuevos_ids == ids_actuales:
                return
                
            self.tabla_destinos.setRowCount(0)
            for idx, fila in enumerate(filas):
                self.tabla_destinos.insertRow(idx)
                self.tabla_destinos.setItem(idx, 0, QTableWidgetItem(str(fila[0])))
                self.tabla_destinos.setItem(idx, 1, QTableWidgetItem(str(fila[1] or '')))
                self.tabla_destinos.setItem(idx, 2, QTableWidgetItem(str(fila[2])))
        except Exception: pass

    def agregar_destino(self):
        nombre = self.input_alias_destino.text().strip()
        ruta = self.input_ruta_destino.text().strip()
        if not ruta: return
        if not nombre:
            nombre = Path(ruta).name
        nombre = nombre.lower()
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("INSERT INTO directorios_destino (ruta, nombre_alias) VALUES (?, ?)", (ruta, nombre))
            conn.commit(); conn.close()
            self.input_alias_destino.clear(); self.input_ruta_destino.clear(); self.cargar_destinos()
            try:
                app_signals.destinos_changed.emit()
            except Exception:
                pass
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Destino existente", "El alias o la ruta ya existen en los destinos configurados.")
        except Exception:
            pass

    def eliminar_destino(self):
        fila = self.tabla_destinos.currentRow()
        if fila < 0: return
        try:
            conn, cursor = self.conectar_db()
            cursor.execute("DELETE FROM directorios_destino WHERE id = ?", (self.tabla_destinos.item(fila, 0).text(),))
            conn.commit(); conn.close()
            self.cargar_destinos()
            try:
                app_signals.destinos_changed.emit()
            except Exception:
                pass
        except Exception:
            pass