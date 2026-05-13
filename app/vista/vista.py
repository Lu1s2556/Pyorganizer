import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QLineEdit, QApplication, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from app.controlador.controlador_asistente import AsistenteVigiData

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

class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.asistente = AsistenteVigiData() 
        
        # Variable de estado para el chat
        self.chat_expandido = True 
        
        self.setWindowTitle("PyOrganizer - Panel de Control")
        self.resize(1200, 800)
        self.setStyleSheet("QMainWindow { background-color: #0c0c0c; }")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QHBoxLayout(self.central)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        self.init_sidebar()
        self.init_content()
        self.init_chat_floating()

    def init_sidebar(self):
        sidebar = QFrame(); sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #121212; border-right: 1px solid #222;")
        l = QVBoxLayout(sidebar)
        
        logo = QLabel("📁 Pyorganizer"); logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin: 25px;")
        l.addWidget(logo)

        btn_active = QPushButton("  Panel Resumen")
        btn_active.setStyleSheet("background: #eab308; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;")
        l.addWidget(btn_active)
        
        for text in ["Reglas de IA", "Historial"]:
            b = QPushButton(f"  {text}")
            b.setStyleSheet("QPushButton { background: #121212; color: #white; text-align: left; padding: 12px; border: none; } QPushButton:hover { background: #eab308; color: white; }")
            l.addWidget(b)
        
        l.addStretch()
        
        btn_scan = QPushButton("ESCANEAR AHORA")
        btn_scan.setStyleSheet("QPushButton { background: #121212; color: white; font-weight: bold; padding: 15px; border-radius: 5px; margin: 10px; } QPushButton:hover { background: #22c55e; color: white; }")
        l.addWidget(btn_scan)
        self.main_layout.addWidget(sidebar)

    def init_content(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        head = QVBoxLayout()
        tit = QLabel("Panel de Control"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;"); tit.setAlignment(Qt.AlignCenter)
        sub = QLabel(""); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit); head.addWidget(sub)
        layout.addLayout(head)

        # Métricas (Basadas en la interfaz real)
        grid = QGridLayout()
        grid.addWidget(TarjetaMetrica("ARCHIVOS PROCESADOS", "1,250", "white"), 0, 0)
        grid.addWidget(TarjetaMetrica("CATEGORÍAS IA", "12", "#eab308"), 0, 1)
        grid.addWidget(TarjetaMetrica("PRECISIÓN NLP", "96.4%", "#22c55e"), 0, 2)
        grid.addWidget(TarjetaMetrica("ESPACIO LIBERADO", "14.2 GB", "#eab308"), 0, 3)
        layout.addLayout(grid)

        # Área Central
        center_h = QHBoxLayout()
        chart_f = QFrame(); chart_f.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222;")
        chart_l = QVBoxLayout(chart_f)
        chart_l.addWidget(QLabel("Distribución de Archivos por Categoría", styleSheet="color:white; font-weight:bold;"))
        mock_pie = QLabel("GRÁFICO DE DISTRIBUCIÓN"); mock_pie.setAlignment(Qt.AlignCenter); mock_pie.setStyleSheet("color: #333;")
        chart_l.addWidget(mock_pie)
        center_h.addWidget(chart_f, 2)

        # Historial de Acciones (Derecha)
        act_f = QFrame(); act_f.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222;")
        act_l = QVBoxLayout(act_f)
        act_l.addWidget(QLabel("Últimas Acciones Inteligentes", styleSheet="color:white; font-weight:bold;"))
        self.scroll_act = QScrollArea(); self.scroll_act.setWidgetResizable(True); self.scroll_act.setStyleSheet("border:none;")
        self.act_cont = QWidget(); self.act_list = QVBoxLayout(self.act_cont); self.act_list.addStretch()
        self.scroll_act.setWidget(self.act_cont)
        act_l.addWidget(self.scroll_act)
        center_h.addWidget(act_f, 1)
        
        layout.addLayout(center_h, 1)
        self.main_layout.addWidget(content)

    def init_chat_floating(self):
        """Inicializa la ventana de chat con capacidad de minimizar"""
        self.chat_win = QFrame(self)
        self.chat_win.setFixedSize(280, 380)
        self.chat_win.setStyleSheet("background: #1e1e1e; border-radius: 12px; border: 1px solid #eab308;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,200)); self.chat_win.setGraphicsEffect(shadow)

        self.chat_layout = QVBoxLayout(self.chat_win)
        self.chat_layout.setContentsMargins(0,0,0,0) # Ajuste para que el botón cubra todo el ancho

        # BOTÓN DE CABECERA (Para minimizar/maximizar)
        self.btn_toggle = QPushButton("🤖 Asistente PyOrganizer")
        self.btn_toggle.setFixedHeight(40)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background: #eab308; 
                color: white; 
                font-weight: bold; 
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px;
                border: none;
            }
            QPushButton:hover { background: #d4a017; }
        """)
        self.btn_toggle.clicked.connect(self.toggle_chat)
        self.chat_layout.addWidget(self.btn_toggle)

        # CONTENEDOR DE CUERPO (Lo que se oculta)
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

    def toggle_chat(self):
        """Lógica para minimizar y maximizar el chat"""
        if self.chat_expandido:
            # Minimizar
            self.chat_body.hide()
            self.chat_win.setFixedHeight(40)
            self.chat_expandido = False
        else:
            # Maximizar
            self.chat_body.show()
            self.chat_win.setFixedHeight(380)
            self.chat_expandido = True
        
        # Reposicionar después de cambiar el tamaño
        self.actualizar_posicion_chat()

    def actualizar_posicion_chat(self):
        """Mantiene el chat en la esquina inferior derecha"""
        x = self.width() - self.chat_win.width() - 20
        y = self.height() - self.chat_win.height() - 20
        self.chat_win.move(x, y)

    def resizeEvent(self, event):
        self.actualizar_posicion_chat()
        super().resizeEvent(event)

    def enviar_a_controlador(self):
        """Mantiene la lógica de envío pero limpia el input"""
        txt = self.chat_input.text()
        if not txt: return
        
        respuesta = self.asistente.procesar_peticion(txt)
        
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Tú:</b> {txt}", styleSheet="color: #888; font-size: 11px;"))
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>IA:</b> {respuesta}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
        
        # Desplazar al final automáticamente
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        
        self.chat_input.clear()