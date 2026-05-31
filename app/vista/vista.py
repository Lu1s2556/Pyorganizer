import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QLabel, QLineEdit, 
                               QFormLayout, QGroupBox, QComboBox, QTextEdit)
from PySide6.QtCore import Qt
from app.controlador.controlador_asistente import AsistenteVigiData

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PY.Organizer - Panel Inteligente")
        self.resize(900, 550)
        
        # Instanciación directa del Controlador (MVC)
        self.controlador = AsistenteVigiData()
        
        self.init_ui()

    def init_ui(self):
        # Contenedor Base Central de la Aplicación
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # =========================================================================
        # PANEL LATERAL IZQUIERDO (MENÚ DE NAVEGACIÓN)
        # =========================================================================
        panel_lateral = QWidget()
        panel_lateral.setStyleSheet("background-color: #2c3e50; min-width: 180px; max-width: 180px;")
        layout_lateral = QVBoxLayout(panel_lateral)
        layout_lateral.setContentsMargins(10, 20, 10, 20)

        lbl_logo = QLabel("PY.Organizer")
        lbl_logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 25px; font-family: sans-serif;")
        lbl_logo.setAlignment(Qt.AlignCenter)
        layout_lateral.addWidget(lbl_logo)

        self.btn_dashboard = QPushButton("📊 Dashboard")
        self.btn_reglas_ia = QPushButton("⚙️ Reglas IA")
        
        estilo_botones = """
            QPushButton { 
                color: white; background-color: transparent; text-align: left; 
                padding: 10px; border-radius: 4px; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background-color: #34495e; }
        """
        self.btn_dashboard.setStyleSheet(estilo_botones)
        self.btn_reglas_ia.setStyleSheet(estilo_botones)

        layout_lateral.addWidget(self.btn_dashboard)
        layout_lateral.addWidget(self.btn_reglas_ia)
        layout_lateral.addStretch() # Empujar todo al tope superior
        
        layout_principal.addWidget(panel_lateral)

        # =========================================================================
        # CONTENEDOR MULTIVISTA DERECHO (QStackedWidget)
        # =========================================================================
        self.vistas_apiladas = QStackedWidget()
        self.vistas_apiladas.setStyleSheet("background-color: #f8f9fa;")

        # Construcción dinámica de pantallas individuales
        self.vista_dashboard = self.crear_vista_dashboard()
        self.vista_reglas_ia = self.crear_vista_reglas_ia()

        self.vistas_apiladas.addWidget(self.vista_dashboard) # Índice de pila: 0
        self.vistas_apiladas.addWidget(self.vista_reglas_ia) # Índice de pila: 1

        layout_principal.addWidget(self.vistas_apiladas)

        # Enrutamiento de clics laterales para conmutar las pantallas del StackedWidget
        self.btn_dashboard.clicked.connect(lambda: self.vistas_apiladas.setCurrentIndex(0))
        self.btn_reglas_ia.clicked.connect(lambda: self.vistas_apiladas.setCurrentIndex(1))

    def crear_vista_dashboard(self):
        """Genera la vista principal que contiene el Chat Conversacional de Inteligencia Artificial"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_tit = QLabel("📊 Panel de Control y Asistente")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_tit)

        # Pantalla de Chat Flotante Conversacional
        self.pantalla_chat = QTextEdit()
        self.pantalla_chat.setReadOnly(True)
        self.pantalla_chat.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 5px; font-size: 13px; padding: 5px;")
        self.pantalla_chat.append("🤖 <b>VigiData:</b> ¡Hola! ¿Qué archivos deseas organizar hoy? Puedes decirme por ejemplo: <i>'mueve el archivo tarea.docx a la carpeta unellez en el escritorio'</i>")
        layout.addWidget(self.pantalla_chat)

        # Entrada de Texto de Comandos
        layout_input = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Escribe un comando aquí y presiona Enter...")
        self.chat_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")
        self.chat_input.returnPressed.connect(self.enviar_a_controlador) # Enviar al pulsar Enter

        btn_enviar = QPushButton("Enviar")
        btn_enviar.setStyleSheet("background-color: #2c3e50; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_enviar.clicked.connect(self.enviar_a_controlador)

        layout_input.addWidget(self.chat_input)
        layout_input.addWidget(btn_enviar)
        layout.addLayout(layout_input)

        return widget

    def crear_vista_reglas_ia(self):
        """Nueva Vista avanzada: Permite al usuario dar reglas y parámetros restrictivos a cada carpeta"""
        widget = QWidget()
        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        lbl_titulo = QLabel("⚙️ Gobernanza de Carpetas y Reglas Organizativas")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout_principal.addWidget(lbl_titulo)
        
        lbl_desc = QLabel("Asigna qué tipos de archivos o palabras clave tiene permitido almacenar cada carpeta de tu dispositivo.")
        lbl_desc.setStyleSheet("font-size: 12px; color: #7f8c8d; margin-bottom: 15px;")
        layout_principal.addWidget(lbl_desc)

        grupo_config = QGroupBox("Establecer Parámetros de Almacenamiento")
        layout_form = QFormLayout(grupo_config)

        # Listado de carpetas que reconoce nuestro asistente
        self.combo_carpetas = QComboBox()
        opciones = ["universidad", "mis proyectos", "respaldos", "documentos", "fotos"]
        self.combo_carpetas.addItems(opciones)
        self.combo_carpetas.setStyleSheet("padding: 5px; font-size: 13px;")
        
        self.input_ext_permitidas = QLineEdit()
        self.input_ext_permitidas.setPlaceholderText("Ej: pdf, docx, xlsx (dejar vacío para aceptar todas)")
        self.input_ext_permitidas.setStyleSheet("padding: 5px;")
        
        self.input_palabras_clave = QLineEdit()
        self.input_palabras_clave.setPlaceholderText("Ej: tarea, examen, unellez (dejar vacío para aceptar cualquiera)")
        self.input_palabras_clave.setStyleSheet("padding: 5px;")

        layout_form.addRow("Seleccionar Carpeta:", self.combo_carpetas)
        layout_form.addRow("Extensiones Permitidas:", self.input_ext_permitidas)
        layout_form.addRow("Filtro por Palabras Clave:", self.input_palabras_clave)
        layout_principal.addWidget(grupo_config)

        # Sincronización dinámica: Al cambiar la carpeta del menú desplegable se cargan sus reglas asociadas
        self.combo_carpetas.currentTextChanged.connect(self.cargar_regla_seleccionada)

        btn_guardar_regla = QPushButton("💾 Guardar Regla Organizativa")
        btn_guardar_regla.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; font-weight: bold; 
                padding: 10px; border-radius: 5px; font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_guardar_regla.clicked.connect(self.guardar_regla_carpeta)
        layout_principal.addWidget(btn_guardar_regla)

        layout_principal.addStretch()
        
        self.cargar_regla_seleccionada() # Carga inicial obligatoria
        return widget

    def cargar_regla_seleccionada(self):
        """Lee en caliente las reglas vigentes de la carpeta seleccionada y las pinta en pantalla"""
        carpeta_actual = self.combo_carpetas.currentText().lower()
        reglas_actuales = self.controlador.reglas_carpetas.get(carpeta_actual)

        if reglas_actuales:
            self.input_ext_permitidas.setText(", ".join(reglas_actuales["extensiones"]))
            self.input_palabras_clave.setText(", ".join(reglas_actuales["palabras"]))
        else:
            self.input_ext_permitidas.clear()
            self.input_palabras_clave.clear()

    def guardar_regla_carpeta(self):
        """Guarda permanentemente las restricciones en la Base de Datos a través del Modelo"""
        carpeta_objetivo = self.combo_carpetas.currentText().lower()
        extensiones = self.input_ext_permitidas.text().strip()
        palabras = self.input_palabras_clave.text().strip()

        exito = self.controlador.modelo_org.guardar_o_actualizar_regla(carpeta_objetivo, extensiones, palabras)
        
        if exito:
            self.controlador.actualizar_reglas_en_memoria() # Actualizar la caché del cerebro de la IA
            self.pantalla_chat.append(f"ℹ️ <b>Sistema:</b> Regla de almacenamiento guardada para la carpeta <u>{carpeta_objetivo}</u>.")
            self.vistas_apiladas.setCurrentIndex(0) # Redirige automáticamente al chat principal

    def enviar_a_controlador(self):
        """Conecta el flujo del Chat directamente con las predicciones del Controlador"""
        texto_usuario = self.chat_input.text().strip()
        if not texto_usuario:
            return

        self.pantalla_chat.append(f"<br><b>Tú:</b> {texto_usuario}")
        self.chat_input.clear()

        # Llamada al método procesador del Controlador (MVC)
        respuesta_ia = self.controlador.procesar_peticion(texto_usuario)
        self.pantalla_chat.append(f"🤖 <b>VigiData:</b> {respuesta_ia}")