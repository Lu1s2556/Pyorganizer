import sys
import os
import re
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QSizePolicy, QGraphicsDropShadowEffect, QLineEdit)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor

# =================================================================
# 🧠 LÓGICA DEL ASISTENTE (CEREBRO)
# =================================================================
class AsistenteVigiData:
    def __init__(self):
        self.rutas_base = {
            "documentos": str(Path.home() / "Documents"),
            "fotos": str(Path.home() / "Pictures"),
            "descargas": str(Path.home() / "Downloads"),
            "escritorio": str(Path.home() / "Desktop")
        }
        self.contexto = {"paso": "inicio", "accion": None, "objetivo": None, "nuevo_nombre": None, "ruta_destino": None}

    def procesar_mensaje(self, entrada):
        entrada = entrada.lower().strip()
        
        if self.contexto["paso"] == "inicio":
            # Borrar
            if any(x in entrada for x in ["borra", "elimina"]):
                match = re.search(r"(?:borra|elimina)\s+([\w\s\.]+)", entrada)
                if match:
                    self.contexto.update({"objetivo": match.group(1).strip(), "accion": "borrar", "paso": "preguntar_ruta"})
                    return f"¿En qué ubicación está '{self.contexto['objetivo']}'?"
            # Renombrar
            if "renombra" in entrada or "cambia el nombre" in entrada:
                match = re.search(r"nombre\s+de\s+([\w\s\.]+)\s+a\s+([\w\s\.]+)", entrada)
                if match:
                    self.contexto.update({"objetivo": match.group(1).strip(), "nuevo_nombre": match.group(2).strip(), "accion": "renombrar", "paso": "preguntar_ruta"})
                    return f"¿En qué carpeta está '{self.contexto['objetivo']}'?"
            # Crear Carpeta
            if "crear" in entrada or "carpeta" in entrada:
                match_c = re.search(r"carpeta\s+([\w\s]+)", entrada)
                self.contexto.update({"objetivo": match_c.group(1).strip().title() if match_c else "Nueva", "accion": "crear", "paso": "preguntar_ruta"})
                return f"¿Donde creo '{self.contexto['objetivo']}'?"

            return "Hola, soy VigiData. ¿Qué archivos o carpetas gestionamos?"

        elif self.contexto["paso"] == "preguntar_ruta":
            ruta_final = self.rutas_base.get(entrada) or (entrada if os.path.exists(entrada) else None)
            if not ruta_final: return "Ruta no válida. Dime: Escritorio, Documentos o Descargas."
            self.contexto["ruta_destino"] = ruta_final
            return self.ejecutar_accion()

    def ejecutar_accion(self):
        destino = Path(self.contexto["ruta_destino"])
        obj, accion = self.contexto["objetivo"], self.contexto["accion"]
        try:
            target = destino / obj
            if accion == "crear":
                target.mkdir(parents=True, exist_ok=True)
                res = f"✅ Carpeta '{obj}' creada en {entrada}."
            elif accion == "borrar":
                if target.is_file(): os.remove(target)
                else: shutil.rmtree(target)
                res = f"🗑️ '{obj}' eliminado."
            elif accion == "renombrar":
                nuevo = destino / self.contexto["nuevo_nombre"]
                os.rename(target, nuevo)
                res = f"📝 Renombrado a '{nuevo.name}'."
            self.contexto = {"paso": "inicio", "accion": None, "objetivo": None, "nuevo_nombre": None, "ruta_destino": None}
            return res
        except Exception as e: return f"❌ Error: {str(e)}"

# =================================================================
# 🎨 INTERFAZ (COMO LA FOTO)
# =================================================================
class TarjetaMetrica(QFrame):
    def __init__(self, titulo, valor, color, sub, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background: #181818; border-radius: 10px; padding: 15px;")
        l = QVBoxLayout(self)
        t = QLabel(titulo); t.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold;")
        v = QLabel(valor); v.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold; margin: 5px 0;")
        s = QLabel(sub); s.setStyleSheet("color: #555555; font-size: 10px;")
        l.addWidget(t); l.addWidget(v); l.addWidget(s)

class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.asistente = AsistenteVigiData()
        self.setWindowTitle("VigiData - Organizador Inteligente")
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
        
        logo = QLabel("📁 VigiData"); logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin: 25px;")
        l.addWidget(logo)

        # Botones (Igual que la foto)
        btn_active = QPushButton("  Panel Resumen"); btn_active.setStyleSheet("background: #3467eb; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;")
        l.addWidget(btn_active)
        for text in ["Reglas de IA", "Historial"]:
            b = QPushButton(f"  {text}"); b.setStyleSheet("color: #888; text-align: left; padding: 12px; border: none;")
            l.addWidget(b)
        
        l.addStretch()
        
        btn_scan = QPushButton("⚡ ESCANEAR AHORA"); btn_scan.setStyleSheet("background: #28a745; color: white; font-weight: bold; padding: 15px; border-radius: 5px; margin: 10px;")
        l.addWidget(btn_scan)
        self.main_layout.addWidget(sidebar)

    def init_content(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        head = QVBoxLayout()
        tit = QLabel("Panel de Control"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel("Bienvenido al organizador inteligente optimizado."); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit); head.addWidget(sub)
        layout.addLayout(head)

        # Métricas (Fila superior)
        grid = QGridLayout()
        grid.addWidget(TarjetaMetrica("ARCHIVOS PROCESADOS", "1,250", "white", "Actualizado"), 0, 0)
        grid.addWidget(TarjetaMetrica("CATEGORÍAS IA", "12", "#a855f7", "Actualizado"), 0, 1)
        grid.addWidget(TarjetaMetrica("PRECISIÓN NLP", "96.4%", "#22c55e", "Actualizado"), 0, 2)
        grid.addWidget(TarjetaMetrica("ESPACIO LIBERADO", "14.2 GB", "#eab308", "Actualizado"), 0, 3)
        layout.addLayout(grid)

        # Centro (Gráfico y Lista)
        center_h = QHBoxLayout()
        
        # Gráfico (Mockup como en la foto)
        chart_f = QFrame(); chart_f.setStyleSheet("background: #181818; border-radius: 10px; border: 1px solid #222;")
        chart_l = QVBoxLayout(chart_f)
        chart_l.addWidget(QLabel("Distribución de Archivos por Categoría", styleSheet="color:white; font-weight:bold;"))
        mock_pie = QLabel("MOCKUP DE GRÁFICO TIPO PIE\n(Usa PyQtGraph aquí)"); mock_pie.setAlignment(Qt.AlignCenter); mock_pie.setStyleSheet("color: #333; border: 2px dashed #222; margin: 20px;")
        chart_l.addWidget(mock_pie)
        center_h.addWidget(chart_f, 2)

        # Lista Actividad (Derecha)
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
        # Ventana de Chat Flotante (Abajo Izquierda)
        self.chat_win = QFrame(self)
        self.chat_win.setFixedSize(280, 380)
        self.chat_win.setStyleSheet("background: #1e1e1e; border-radius: 12px; border: 1px solid #3467eb;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,200)); self.chat_win.setGraphicsEffect(shadow)

        l = QVBoxLayout(self.chat_win)
        header = QLabel("🤖 Asistente VigiData"); header.setStyleSheet("background: #3467eb; color: white; padding: 10px; font-weight: bold; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        l.addWidget(header)

        self.chat_display = QScrollArea(); self.chat_display.setWidgetResizable(True); self.chat_display.setStyleSheet("border:none;")
        self.msg_cont = QWidget(); self.msg_l = QVBoxLayout(self.msg_cont); self.msg_l.addStretch()
        self.chat_display.setWidget(self.msg_cont)
        l.addWidget(self.chat_display)

        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("Escribe un comando..."); self.chat_input.setStyleSheet("background: #121212; color: white; padding: 10px; border-radius: 5px; border: 1px solid #333;")
        self.chat_input.returnPressed.connect(self.hablar)
        l.addWidget(self.chat_input)

    def resizeEvent(self, event):
        # Mantener el chat abajo a la izquierda del área de contenido
        self.chat_win.move(250, self.height() - 400)
        super().resizeEvent(event)

    def hablar(self):
        txt = self.chat_input.text()
        if not txt: return
        resp = self.asistente.procesar_mensaje(txt)
        
        # Burbujas en el chat
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Tú:</b> {txt}", styleSheet="color: #888; font-size: 11px;"))
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>IA:</b> {resp}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
        
        # Agregar al historial de la derecha
        item = QFrame(); item.setStyleSheet("background: #222; margin-bottom: 2px; padding: 5px; border-radius: 4px;")
        il = QHBoxLayout(item); il.addWidget(QLabel(f"⚙️ {resp}", styleSheet="color: #ccc; font-size: 10px;"))
        self.act_list.insertWidget(0, item)
        
        self.chat_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DashboardOrganizador()
    win.show()
    sys.exit(app.exec())