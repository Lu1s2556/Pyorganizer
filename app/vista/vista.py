
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, 
                               QScrollArea, QLineEdit, QApplication, QGraphicsDropShadowEffect,
                               QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont

from app.services import get_total_movidos, get_total_reglas
from app.signals import app_signals
from app.core.motor_organizador import MotorOrganizadorCore, HiloOrganizador

# Importaciones de controladores y sub-vistas modulares
from app.controlador.controlador_asistente import AsistenteVigiData
from app.vista.vista_reglas import VistaReglasOrganizacion
from app.vista.vista_configuracion import VistaConfiguracionGlobal 

class TarjetaMetrica(QFrame):
    """Componente para las tarjetas de estadísticas superiores"""
    def __init__(self, titulo, valor, color, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background: #181818; border-radius: 10px; padding: 15px;")
        l = QVBoxLayout(self)
        t = QLabel(titulo); t.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold;"); t.setAlignment(Qt.AlignCenter)
        self.valor_label = QLabel(valor); self.valor_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold; margin: 5px 0;"); self.valor_label.setAlignment(Qt.AlignCenter)
        l.addWidget(t); l.addWidget(self.valor_label)

    def actualizar_valor(self, valor):
        self.valor_label.setText(valor)


class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.asistente = AsistenteVigiData()
        self.escaneos_ejecutados = 0
        self.ultimo_escaneo = None
        
        # === PASO 4: CONTROL DE EXCLUSIÓN MUTUA / CONCURRENCIA ===
        self.escaneo_en_progreso = False
        self.chat_expandido = True 
        
        self.setWindowTitle("PyOrganizer - Panel de Control")
        self.resize(1200, 800)
        try:
            self.showMaximized()
        except Exception:
            pass
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

        # Conectar señal global para refrescar estadísticas cuando cambien
        try:
            app_signals.stats_changed.connect(self.refrescar_panel_resumen)
        except Exception:
            pass

        # Refrescar inmediatamente las estadísticas reales al iniciar
        try:
            self.refrescar_panel_resumen()
        except Exception:
            pass

        # Mensaje de bienvenida automático
        try:
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel("<b>Sistema:</b> Hola, ¿cómo te puedo ayudar?", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel("<b>Sistema:</b> Escribe /ayuda si no sabes qué comando usar.", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
        except Exception:
            pass

        # Iniciar Watchdog nativo en tiempo real
        try:
            from app.controlador.watcher_thread import WatcherThread
            self.watchdog = WatcherThread(self.asistente.modelo_org.db_path)
            try:
                self.watchdog._worker.move_result.connect(self._on_move_result)
            except Exception:
                pass
            try:
                self.watchdog._worker.file_ready.connect(self.asistente.procesar_archivo_nuevo)
            except Exception:
                pass
            self.watchdog.start()
        except Exception:
            pass

        # === PASO 3 y 4: PROGRAMACIÓN DEL QTIMER GLOBAL DE ALTA FRECUENCIA (20 SEG) ===
        try:
            # Cambiado a 60s cooldown para reducir carga en sistemas modestos
            self.timer_escaneo_20s = QTimer(self)
            self.timer_escaneo_20s.timeout.connect(self.iniciar_escaneo)
            self.timer_escaneo_20s.start(60000)  # 60000 ms = 60 segundos
        except Exception as e:
            print(f"Error al inicializar el temporizador global: {e}")

        # === PASO 1: ARRANQUE Y ACTIVACIÓN AUTOMÁTICA AL INICIAR LA UI ===
        QTimer.singleShot(2000, self.iniciar_escaneo)

    def init_sidebar(self):
        """Barra lateral izquierda adaptada según el plan corporativo global"""
        sidebar = QFrame(); sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #121212; border-right: 1px solid #222;")
        l = QVBoxLayout(sidebar)
        
        logo = QLabel("📁 PyOrganizer"); logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin: 25px;")
        l.addWidget(logo)

        # Estilo unificado de botones de la barra lateral
        estilo_btn = "QPushButton { background: #121212; color: white; text-align: left; padding: 12px; border: none; } QPushButton:hover { background: #eab308; color: white; }"

        # Botón 0: Panel Resumen (Activo por defecto)
        self.btn_resumen = QPushButton("   Panel Resumen")
        self.btn_resumen.setStyleSheet("background: #eab308; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;")
        self.btn_resumen.clicked.connect(lambda: self.cambiar_vista(0, self.btn_resumen))
        l.addWidget(self.btn_resumen)

        # Botón 1: CONFIGURACIÓN GLOBAL 
        self.btn_config_global = QPushButton("  Configuración Global")
        self.btn_config_global.setStyleSheet(estilo_btn)
        self.btn_config_global.clicked.connect(lambda: self.cambiar_vista(1, self.btn_config_global))
        l.addWidget(self.btn_config_global)
        
        # Botón 2: Reglas de organización
        self.btn_reglas = QPushButton("   Reglas")
        self.btn_reglas.setStyleSheet(estilo_btn)
        self.btn_reglas.clicked.connect(lambda: self.cambiar_vista(2, self.btn_reglas))
        l.addWidget(self.btn_reglas)

        l.addStretch()
        
        # === PLAN DE AJUSTE: BOTÓN MIGRADO E INICIALIZADO EN LA SIDEBAR GLOBAL ===
        self.btn_scan = QPushButton("ESCANEAR AHORA")
        self.btn_scan.setStyleSheet("QPushButton { background: #eab308; color: black; font-weight: bold; padding: 12px; border-radius: 5px; margin: 15px; } QPushButton:hover { background: #c79906; } QPushButton:disabled { background: #262626; color: #666666; }")
        self.btn_scan.clicked.connect(self.ejecutar_escaneo_asincrono)
        l.addWidget(self.btn_scan)

        self.main_layout.addWidget(sidebar)

    def init_content_views(self):
        """Asigna y empaqueta las secciones dentro del QStackedWidget derecho"""
        self.vista_dashboard = self.crear_panel_resumen_original()
        
        self.vista_configuracion = VistaConfiguracionGlobal(
            asistente=self.asistente,
            callback_regresar=lambda: self.cambiar_vista(0, self.btn_resumen)
        )
        
        self.vista_reglas_ia = VistaRules = VistaReglasOrganizacion(
            asistente=self.asistente, 
            callback_regresar=lambda: self.cambiar_vista(0, self.btn_resumen)
        )

        self.content_stack.addWidget(self.vista_dashboard)     # Índice 0
        self.content_stack.addWidget(self.vista_configuracion) # Índice 1
        self.content_stack.addWidget(self.vista_reglas_ia)     # Índice 2

        self.main_layout.addWidget(self.content_stack)

    def cambiar_vista(self, indice, boton_activo):
        """Efectúa la transición de la pantalla sin romper la persistencia del temporizador"""
        self.content_stack.setCurrentIndex(indice)
        
        estilo_base = "QPushButton { background: #121212; color: white; text-align: left; padding: 12px; border: none; } QPushButton:hover { background: #eab308; color: white; }"
        estilo_activo = "background: #eab308; color: white; text-align: left; padding: 12px; border-radius: 5px; font-weight: bold;"
        
        self.btn_resumen.setStyleSheet(estilo_base)
        self.btn_config_global.setStyleSheet(estilo_base)
        self.btn_reglas.setStyleSheet(estilo_base)
        
        boton_activo.setStyleSheet(estilo_activo)

    def crear_panel_resumen_original(self):
        """Estructura e interfaz del Panel de Control original"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)

        head = QVBoxLayout()
        tit = QLabel("Panel de Control"); tit.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        sub = QLabel("Motor de ordenamiento cíclico optimizado"); sub.setStyleSheet("color: #666; font-size: 14px;")
        head.addWidget(tit); head.addWidget(sub)
        layout.addLayout(head)

        grid = QGridLayout()
        try:
            db_path = self.asistente.modelo_org.db_path
            total_mov = f"{get_total_movidos(db_path):,}"
        except Exception:
            total_mov = "0"

        try:
            db_path = self.asistente.modelo_org.db_path
            total_reglas = f"{get_total_reglas(db_path):,}"
        except Exception:
            total_reglas = "0"

        self.card_archivos = TarjetaMetrica("ARCHIVOS PROCESADOS", total_mov, "white")
        self.card_reglas = TarjetaMetrica("REGLAS DEFINIDAS", total_reglas, "#eab308")
        self.card_escaneos = TarjetaMetrica("ESCANEOS EJECUTADOS", str(self.escaneos_ejecutados), "#22c55e")
        ultimo_texto = self.ultimo_escaneo.strftime("%Y-%m-%d %H:%M:%S") if self.ultimo_escaneo else "Nunca"
        self.card_ultimo = TarjetaMetrica("ÚLTIMO ESCANEO", ultimo_texto, "#eab308")

        grid.addWidget(self.card_archivos, 0, 0)
        grid.addWidget(self.card_reglas, 0, 1)
        grid.addWidget(self.card_escaneos, 0, 2)
        grid.addWidget(self.card_ultimo, 0, 3)
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
        act_l.addWidget(QLabel("Últimas Acciones", styleSheet="color:white; font-weight:bold;"))
        self.scroll_act = QScrollArea(); self.scroll_act.setWidgetResizable(True); self.scroll_act.setStyleSheet("border:none;")
        self.act_cont = QWidget(); self.act_list = QVBoxLayout(self.act_cont); self.act_list.addStretch()
        self.scroll_act.setWidget(self.act_cont)
        act_l.addWidget(self.scroll_act)
        center_h.addWidget(act_f, 1)
        
        layout.addLayout(center_h, 1)
        return content

    # === PASO 2 Y 4: MÉTODO PÚBLICO REUTILIZABLE CON EXCLUSIÓN MUTUA ===
    def iniciar_escaneo(self):
        """
        Lógica centralizada para desplegar el Hilo del motor. Protege el hilo contra
        ejecuciones simultáneas indeseadas del temporizador o clics manuales.
        """
        if self.escaneo_en_progreso:
            return  # Retorno silencioso si ya se encuentra trabajando

        self.escaneo_en_progreso = True
        
        # PASO 5: Actualización del estado visual en la UI
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("ESCANEANDO...")

        try:
            # Consumir la clase HiloOrganizador importada desde el motor core modificado
            motor = MotorOrganizadorCore(self.asistente.modelo_org.db_path)
            self.hilo_trabajo = HiloOrganizador(motor)
            
            # Conexión fluida de señales
            self.hilo_trabajo.progreso_senal.connect(self.registrar_accion_en_interfaz)
            self.hilo_trabajo.finalizado_senal.connect(self.finalizar_escaneo)
            
            # Lanzar proceso en segundo plano de alta velocidad
            self.hilo_trabajo.start()
        except Exception as e:
            self.registrar_accion_en_interfaz(f"❌ Error al lanzar motor: {e}")
            self.escaneo_en_progreso = False
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("ESCANEAR AHORA")

    def ejecutar_escaneo_asincrono(self):
        """Mapeo seguro vinculado al evento del botón manual de la Sidebar"""
        if self.escaneo_en_progreso:
            return
        self.iniciar_escaneo()

    # === PASO 5: RESTAURACIÓN Y REGISTRO VISUAL EN HISTORIAL ===
    def finalizar_escaneo(self, total_archivos):
        """Restablece los controles y refresca las métricas dinámicas (CRUD)"""
        self.escaneo_en_progreso = False
        self.escaneos_ejecutados += 1
        self.ultimo_escaneo = datetime.now()
        
        # Restaurar botón lateral
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("ESCANEAR AHORA")
        
        # Inyectar log de resumen en verde neón/amarillo dentro del historial
        lbl_resumen = QLabel(f"✨ Ciclo completado con éxito. Movidos: {total_archivos}")
        lbl_resumen.setStyleSheet("color: #eab308; font-weight: bold; font-size: 11px; padding: 4px; background: #1a1a1a; border-radius: 4px; margin: 2px 0;")
        self.act_list.insertWidget(self.act_list.count() - 1, lbl_resumen)
        self.scroll_act.verticalScrollBar().setValue(self.scroll_act.verticalScrollBar().maximum())
        
        # Actualizar las tarjetas numéricas del Dashboard
        self.refrescar_panel_resumen()

    def registrar_accion_en_interfaz(self, mensaje):
        """Muestra los logs en tiempo real de forma elegante"""
        lbl_accion = QLabel(mensaje)
        lbl_accion.setStyleSheet("color: #22c55e; font-size: 11px; padding: 2px; background: #121212; border-radius: 3px; margin: 2px 0;")
        self.act_list.insertWidget(self.act_list.count() - 1, lbl_accion)
        self.scroll_act.verticalScrollBar().setValue(self.scroll_act.verticalScrollBar().maximum())

    def _on_move_result(self, info: dict):
        """Slot que maneja resultados de movimiento emitidos por el watcher."""
        try:
            msg = f"👀 [Monitor] {info.get('message')} - {info.get('path')}"
            self.registrar_accion_en_interfaz(msg)
            try:
                app_signals.stats_changed.emit()
            except Exception:
                # Fallback a refrescar directamente si la señal falla
                self.refrescar_panel_resumen()
        except Exception:
            pass

    def refrescar_panel_resumen(self):
        """Actualiza las tarjetas superiores consultando `services.py`."""
        try:
            db_path = self.asistente.modelo_org.db_path
            total_mov = f"{get_total_movidos(db_path):,}"
            total_reglas = f"{get_total_reglas(db_path):,}"
            escaneos = str(self.escaneos_ejecutados)
            ultimo_texto = self.ultimo_escaneo.strftime("%Y-%m-%d %H:%M:%S") if self.ultimo_escaneo else "Nunca"
        except Exception:
            return

        try:
            self.card_archivos.actualizar_valor(total_mov)
            self.card_reglas.actualizar_valor(total_reglas)
            self.card_escaneos.actualizar_valor(escaneos)
            self.card_ultimo.actualizar_valor(ultimo_texto)
        except Exception:
            pass

    # === COMPONENTES SECUNDARIOS DEL CHAT DEL SISTEMA ===
    def init_chat_floating(self):
        """Inicializa la ventana de chat flotante original con capacidad de minimizar"""
        self.chat_win = QFrame(self)
        self.chat_win.setFixedSize(280, 380)
        self.chat_win.setStyleSheet("background: #1e1e1e; border-radius: 12px; border: 1px solid #eab308;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,200)); self.chat_win.setGraphicsEffect(shadow)

        self.chat_layout = QVBoxLayout(self.chat_win)
        self.chat_layout.setContentsMargins(0,0,0,0)

        self.btn_toggle = QPushButton("Mensajes del Sistema")
        self.btn_toggle.setFixedHeight(40)
        self.btn_toggle.setStyleSheet("QPushButton { background: #eab308; color: black; font-weight: bold; border-top-left-radius: 10px; border-top-right-radius: 10px; border: none; } QPushButton:hover { background: #c79906; }")
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
        if txt.lower() in ['/ayuda', 'ayuda']:
            self.mostrar_ayuda()
            self.chat_input.clear()
            return

        respuesta = self.asistente.procesar_peticion(txt)
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Tú:</b> {txt}", styleSheet="color: #888; font-size: 11px;"))

        if isinstance(respuesta, dict) and 'suggestions' in respuesta:
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Sistema:</b> {respuesta.get('message')}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
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
            self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Sistema:</b> {respuesta}", styleSheet="color: white; background: #222; padding: 8px; border-radius: 5px;"))
            self.suggestion_container.hide()

        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        self.chat_input.clear()

    def _usar_sugerencia(self, texto_sugerencia):
        self.chat_input.setText(texto_sugerencia)
        self.enviar_a_controlador()

    def mostrar_ayuda(self):
        try:
            alias_keys = list(self.asistente.rutas_atajo.keys())
        except Exception:
            alias_keys = ['escritorio', 'documentos', 'descargas']

        ejemplos = [
            f"Mueve <b>archivos</b> a <b>{alias_keys[1]}</b>",
            f"Crea una carpeta llamada <b>fotos</b> en <b>{alias_keys[0]}</b>",
            f"Mueve <b>pdf</b> a <b>{alias_keys[2]}</b>",
        ]
        alias_html = ''.join(f"<li>{a}</li>" for a in alias_keys[:6])

        html = f"<div style='color:#ddd; font-size:13px; line-height:1.4;'>"
        html += "<b>Comandos útiles</b><ul>"
        for e in ejemplos:
            html += f"<li>{e}</li>"
        html += "</ul>"
        html += "<b>Alias reconocidos</b><ul>" + alias_html + "</ul></div>"

        lbl = QLabel(html)
        lbl.setStyleSheet("color: white; background: #222; padding: 8px; border-radius: 5px;")
        lbl.setTextFormat(Qt.RichText)
        self.msg_l.insertWidget(self.msg_l.count()-1, QLabel(f"<b>Tú:</b> /ayuda", styleSheet="color: #888; font-size: 11px;"))
        self.msg_l.insertWidget(self.msg_l.count()-1, lbl)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())