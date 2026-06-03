import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, 
                               QScrollArea, QLineEdit, QApplication, QGraphicsDropShadowEffect,
                               QStackedWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtCore import QThread, Signal
from app.core.motor_organizador import MotorOrganizadorCore
# Importaciones de controladores y sub-vistas modulares
from app.controlador.controlador_asistente import AsistenteVigiData
from app.vista.vista_reglas import VistaReglasOrganizacion
from app.vista.vista_configuracion import VistaConfiguracionGlobal # Fase 1 Importada

class TarjetaMetrica(QFrame):
    """Componente para las tarjetas de estadísticas superiores"""
    def __init__(self, titulo, valor, color, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background: #181818; border-radius: 10px; padding: 15px;")
        l = QVBoxLayout(self)
        t = QLabel(titulo); t.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold;"); t.setAlignment(Qt.AlignCenter)
        v = QLabel(valor); v.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold; margin: 5px 0;"); v.setAlignment(Qt.AlignCenter)
        l.addWidget(t); l.addWidget(v)

class HiloOrganizador(QThread):
    """Hilo secundario de alta eficiencia para ejecutar el motor sin congelar la UI"""
    progreso_senal = Signal(str)
    finalizado_senal = Signal(int)

    def __init__(self, motor):
        super().__init__()
        self.motor = motor

    def run(self):
        # Ejecuta el escaneo pesado en segundo plano
        total = self.motor.procesar_organizacion(callback_progreso=self.progreso_senal.emit)
        self.finalizado_senal.emit(total)

class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.asistente = AsistenteVigiData() 
        # Conectar señal de estadísticas del asistente
        try:
            self.asistente.actualizar_estadisticas.connect(self.handle_actualizar_estadisticas)
        except Exception:
            pass
        
        # Variable de estado para el chat flotante
        self.chat_expandido = True 
        
        self.setWindowTitle("PyOrganizer - Panel de Control")
        self.resize(1200, 800)
        self.setStyleSheet("QMainWindow { background-color: #0c0c0c; }")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QHBoxLayout(self.central)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # Contenedor Multi-vista para alternar los paneles derechos
        self.content_stack = QStackedWidget()

        self.init_sidebar()
        self.init_content_views() 
        self.init_chat_floating()

    def init_sidebar(self):
        """Barra lateral izquierda adaptada para incluir la Fase 1"""
        sidebar = QFrame(); sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #121212; border-right: 1px solid #222;")
        l = QVBoxLayout(sidebar)
        
        logo = QLabel("📁 Pyorganizer"); logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin: 25px;")
        l.addWidget(logo)

        # Estilo unificado de botones de la barra lateral
        estilo_btn = "QPushButton { background: #121212; color: white; text-align: left; padding: 12px; border: none; } QPushButton:hover { background: #eab308; color: white; }"

        # Botón 0: Panel Resumen (Activo por defecto)
        self.btn_resumen = QPushButton("  Panel Resumen")
        self.btn_resumen.setStyleSheet("background: #eab308; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;")
        self.btn_resumen.clicked.connect(lambda: self.cambiar_vista(0, self.btn_resumen))
        l.addWidget(self.btn_resumen)

        # Botón 1: CONFIGURACIÓN GLOBAL (Fase 1 asignada al Índice 1)
        self.btn_config_global = QPushButton(" Configuración Global")
        self.btn_config_global.setStyleSheet(estilo_btn)
        self.btn_config_global.clicked.connect(lambda: self.cambiar_vista(1, self.btn_config_global))
        l.addWidget(self.btn_config_global)
        
        # Botón 2: Reglas de IA (Avanzado asignado al Índice 2)
        self.btn_reglas = QPushButton("  Reglas de IA")
        self.btn_reglas.setStyleSheet(estilo_btn)
        self.btn_reglas.clicked.connect(lambda: self.cambiar_vista(2, self.btn_reglas))
        l.addWidget(self.btn_reglas)

        l.addStretch()
        
        btn_scan = QPushButton("ESCANEAR AHORA")
        btn_scan.setStyleSheet("QPushButton { background: #121212; color: white; font-weight: bold; padding: 15px; border-radius: 5px; margin: 10px; } QPushButton:hover { background: #22c55e; color: white; }")
        btn_scan.clicked.connect(self.ejecutar_escaneo_asincrono)
        l.addWidget(btn_scan)
        self.main_layout.addWidget(sidebar)

    def init_content_views(self):
        """Asigna y empaqueta las secciones dentro del QStackedWidget derecho"""
        # PANTALLA 0: Tu vista original del Dashboard
        self.vista_dashboard = self.crear_panel_resumen_original()
        
        # PANTALLA 1: NUEVA Fase 1 (Configuración Global de Orígenes/Destinos)
        self.vista_configuracion = VistaConfiguracionGlobal(
            asistente=self.asistente,
            callback_regresar=lambda: self.cambiar_vista(0, self.btn_resumen)
        )
        
        # PANTALLA 2: Interfaz de reglas organizativas detalladas
        self.vista_reglas_ia = VistaReglasOrganizacion(
            asistente=self.asistente, 
            callback_regresar=lambda: self.cambiar_vista(0, self.btn_resumen)
        )

        # Agregamos los componentes al stack secuencial
        self.content_stack.addWidget(self.vista_dashboard)     # Índice 0
        self.content_stack.addWidget(self.vista_configuracion) # Índice 1
        self.content_stack.addWidget(self.vista_reglas_ia)     # Índice 2

        self.main_layout.addWidget(self.content_stack)

    def cambiar_vista(self, indice, boton_activo):
        """Efectúa la transición de la pantalla y actualiza el botón seleccionado en la barra lateral"""
        self.content_stack.setCurrentIndex(indice)
        
        estilo_base = "QPushButton { background: #121212; color: white; text-align: left; padding: 12px; border: none; } QPushButton:hover { background: #eab308; color: white; }"
        estilo_activo = "background: #eab308; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;"
        
        # Reseteamos estilos de los botones de navegación activos
        self.btn_resumen.setStyleSheet(estilo_base)
        self.btn_config_global.setStyleSheet(estilo_base)
        self.btn_reglas.setStyleSheet(estilo_base)
        
        boton_activo.setStyleSheet(estilo_activo)

    def crear_panel_resumen_original(self):
        """Estructura e interfaz del Panel de Control original (Métricas, Gráfico e Historial)"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)

        head = QVBoxLayout()
        tit = QLabel("Panel de Control"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel(""); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit); head.addWidget(sub)
        layout.addLayout(head)

        grid = QGridLayout()
        grid.addWidget(TarjetaMetrica("ARCHIVOS PROCESADOS", "1,250", "white"), 0, 0)
        grid.addWidget(TarjetaMetrica("CATEGORÍAS IA", "12", "#eab308"), 0, 1)
        grid.addWidget(TarjetaMetrica("PRECISIÓN NLP", "96.4%", "#22c55e"), 0, 2)
        grid.addWidget(TarjetaMetrica("ESPACIO LIBERADO", "14.2 GB", "#eab308"), 0, 3)
        layout.addLayout(grid)

        center_h = QHBoxLayout()
        
        chart_f = QFrame(); chart_f.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222;")
        chart_l = QVBoxLayout(chart_f)
        chart_l.addWidget(QLabel("Distribución de Archivos por Categoría", styleSheet="color:white; font-weight:bold;"))
        mock_pie = QLabel("GRÁFICO DE DISTRIBUCIÓN"); mock_pie.setAlignment(Qt.AlignCenter); mock_pie.setStyleSheet("color: #333;")
        chart_l.addWidget(mock_pie)
        center_h.addWidget(chart_f, 2)

        act_f = QFrame(); act_f.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222;")
        act_l = QVBoxLayout(act_f)
        act_l.addWidget(QLabel("Últimas Acciones Inteligentes", styleSheet="color:white; font-weight:bold;"))
        self.scroll_act = QScrollArea(); self.scroll_act.setWidgetResizable(True); self.scroll_act.setStyleSheet("border:none;")
        self.act_cont = QWidget(); self.act_list = QVBoxLayout(self.act_cont); self.act_list.addStretch()
        self.scroll_act.setWidget(self.act_cont)
        act_l.addWidget(self.scroll_act)
        center_h.addWidget(act_f, 1)
        
        layout.addLayout(center_h, 1)
        return content

    def init_chat_floating(self):
        """Inicializa la ventana de chat flotante original con capacidad de minimizar"""
        self.chat_win = QFrame(self)
        self.chat_win.setFixedSize(280, 380)
        self.chat_win.setStyleSheet("background: #1e1e1e; border-radius: 12px; border: 1px solid #eab308;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,200)); self.chat_win.setGraphicsEffect(shadow)

        self.chat_layout = QVBoxLayout(self.chat_win)
        self.chat_layout.setContentsMargins(0,0,0,0)

        self.btn_toggle = QPushButton("🤖 Asistente PyOrganizer")
        self.btn_toggle.setFixedHeight(40)
        self.btn_toggle.setStyleSheet("QPushButton { background: #eab308; color: white; font-weight: bold; border-top-left-radius: 10px; border-top-right-radius: 10px; border: none; } QPushButton:hover { background: #d4a017; }")
        self.btn_toggle.clicked.connect(self.toggle_chat)
        self.chat_layout.addWidget(self.btn_toggle)

        self.chat_body = QWidget()
        self.body_layout = QVBoxLayout(self.chat_body)
        
        self.chat_display = QScrollArea(); self.chat_display.setWidgetResizable(True); self.chat_display.setStyleSheet("border:none;")
        self.msg_cont = QWidget(); self.msg_l = QVBoxLayout(self.msg_cont); self.msg_l.addStretch()
        self.chat_display.setWidget(self.msg_cont)
        self.body_layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("Escribe un comando..."); self.chat_input.setStyleSheet("background: #121212; color: white; padding: 10px; border-radius: 5px; border: 1px solid #333;")
        self.chat_input.returnPressed.connect(self.enviar_a_controlador)
        self.body_layout.addWidget(self.chat_input)

        self.chat_layout.addWidget(self.chat_body)

        # Contenedor para botones de sugerencia (cuando la IA no entiende)
        self.suggestion_container = QWidget()
        self.suggestion_layout = QHBoxLayout(self.suggestion_container)
        self.suggestion_layout.setContentsMargins(8,4,8,4)
        self.suggestion_container.hide()
        self.chat_layout.addWidget(self.suggestion_container)

    def toggle_chat(self):
        if self.chat_expandido:
            self.chat_body.hide()
            self.chat_win.setFixedHeight(40)
            self.chat_expandido = False
        else:
            self.chat_body.show()
            self.chat_win.setFixedHeight(380)
            self.chat_expandido = True
        self.actualizar_posicion_chat()

    def actualizar_posicion_chat(self):
        x = self.width() - self.chat_win.width() - 20
        y = self.height() - self.chat_win.height() - 20
        self.chat_win.move(x, y)

    def resizeEvent(self, event):
        self.actualizar_posicion_chat()
        super().resizeEvent(event)

    def enviar_a_controlador(self):
        txt = self.chat_input.text().strip()
        if not txt: return
        respuesta = self.asistente.procesar_peticion(txt)

        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Tú:</b> {txt}", styleSheet="color: #888; font-size: 11px;"))

        # Si la respuesta es un dict con sugerencias, mostrar botones
        if isinstance(respuesta, dict) and 'suggestions' in respuesta:
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>IA:</b> {respuesta.get('message')}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
            # Limpiar contenedor de sugerencias y poblar
            for i in reversed(range(self.suggestion_layout.count())):
                w = self.suggestion_layout.itemAt(i).widget()
                if w: w.setParent(None)

            for sug in respuesta.get('suggestions', []):
                btn = QPushButton(sug)
                btn.setStyleSheet("QPushButton{background:#2b2b2b;color:white;padding:6px;border-radius:6px;} QPushButton:hover{background:#3b3b3b}")
                btn.clicked.connect(lambda _, s=sug: self._usar_sugerencia(s))
                self.suggestion_layout.addWidget(btn)

            self.suggestion_container.show()
        else:
            # Normal string response: insertar como mensaje simple
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>IA:</b> {respuesta}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
            # ocultar sugerencias si existían
            self.suggestion_container.hide()

        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        self.chat_input.clear()

    def _usar_sugerencia(self, texto_sugerencia):
        """Rellena la entrada con la sugerencia y la envía automáticamente"""
        self.chat_input.setText(texto_sugerencia)
        self.enviar_a_controlador()

    def handle_actualizar_estadisticas(self, info: dict):
        """Recibe dicts desde `AsistenteVigiData.actualizar_estadisticas` y actualiza la interfaz."""
        # Registrar acción ligera en el historial y actualizar tarjetas si es necesario
        tipo = info.get('accion', 'accion')
        if tipo == 'crear':
            nombre = info.get('nombre', '')
            destino = info.get('destino', '')
            lbl = QLabel(f"➔ Carpeta creada: {nombre} → {Path(destino).name}")
        elif tipo == 'mover':
            cantidad = info.get('cantidad', 0)
            origen = info.get('origen', '')
            destino = info.get('destino', '')
            lbl = QLabel(f"➔ Movimiento inteligente: {cantidad} archivos → {Path(destino).name}")
        else:
            lbl = QLabel(f"➔ {tipo}: {info}")

        lbl.setStyleSheet("color: #22c55e; font-size: 11px; padding: 2px; background: #121212; border-radius: 3px; margin: 2px 0;")
        self.act_list.insertWidget(self.act_list.count() - 1, lbl)
        self.scroll_act.verticalScrollBar().setValue(self.scroll_act.verticalScrollBar().maximum())

    def ejecutar_escaneo_asincrono(self):
        """Prepara e inicia el hilo secundario del Core"""
        # Deshabilitamos temporalmente el botón para evitar doble ejecución masiva
        self.sender().setEnabled(False)
        self.sender().setText("ESCANEANDO...")

        # Instanciamos el Core pasándole la ruta de la base de datos del modelo
        motor = MotorOrganizadorCore(self.asistente.modelo_org.db_path)
        
        self.hilo_trabajo = HiloOrganizador(motor)
        # Conectamos las señales del hilo a la interfaz o historial
        self.hilo_trabajo.progreso_senal.connect(self.registrar_accion_en_interfaz)
        self.hilo_trabajo.finalizado_senal.connect(lambda total: self.finalizar_escaneo(total, self.sender()))
        
        # Iniciar hilo
        self.hilo_trabajo.start()

    def registrar_accion_en_interfaz(self, mensaje):
        """Agrega los movimientos en tiempo real en tu contenedor de Últimas Acciones Inteligentes"""
        lbl_accion = QLabel(mensaje)
        lbl_accion.setStyleSheet("color: #22c55e; font-size: 11px; padding: 2px; background: #121212; border-radius: 3px; margin: 2px 0;")
        # Insertar arriba del espaciador stretch del historial
        self.act_list.insertWidget(self.act_list.count() - 1, lbl_accion)
        self.scroll_act.verticalScrollBar().setValue(self.scroll_act.verticalScrollBar().maximum())

    def finalizar_escaneo(self, total_archivos, boton_escanear):
        """Restablece el botón y muestra el resumen del proceso"""
        boton_escanear.setEnabled(True)
        boton_escanear.setText("ESCANEAR AHORA")
        
        # Registrar resumen en la sección de historial
        lbl_resumen = QLabel(f"➔ Escaneo Completo. Archivos ordenados: {total_archivos}")
        lbl_resumen.setStyleSheet("color: white; font-weight: bold; font-size: 12px; padding: 5px; background: #222; border-radius: 4px; margin: 5px 0;")
        self.act_list.insertWidget(self.act_list.count() - 1, lbl_resumen)
        
        # Mostrar alerta nativa ligera
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Proceso Concluido", f"El motor ha finalizado el ordenamiento.\nArchivos movidos con éxito: {total_archivos}")