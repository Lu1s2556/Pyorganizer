import sys
import os
import psutil
import weakref
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, 
                               QScrollArea, QLineEdit, QApplication,
                               QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QGuiApplication, QCursor
from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries, QPieSlice

from app.services import get_total_movidos, get_total_reglas
from app.signals import app_signals
from app.core.motor_organizador import MotorOrganizadorCore, HiloOrganizador

# Importaciones de controladores y sub-vistas modulares
from app.controlador.controlador_asistente import AsistenteVigiData
from app.vista.vista_reglas import VistaReglasOrganizacion
from app.vista.vista_configuracion import VistaConfiguracionGlobal 

from collections import deque

class TarjetaMetrica(QFrame):
    """Componente para las tarjetas de estadísticas superiores optimizado para bajo consumo"""
    def __init__(self, titulo, valor, color, parent=None):
        self._monitor_message_cache = deque(maxlen=500)  # Cache de mensajes para evitar duplicados en la interfaz
        super().__init__(parent)
        self.setMinimumHeight(120)
        # Transparencia ligera con RGBA para evitar consumo de RAM por sombras complejas
        # Borde lateral amarillo para un toque moderno de producción
        borde_izq = "border-left: 4px solid #eab308;" if color == "#eab308" else "border-left: 4px solid #333333;"
        if color == "white": borde_izq = "border-left: 4px solid #ffffff;"
        if color == "#22c55e": borde_izq = "border-left: 4px solid #22c55e;"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(24, 24, 24, 0.85); 
                border-radius: 8px; 
                {borde_izq}
            }}
        """)
        
        distribucion = QVBoxLayout(self)
        distribucion.setContentsMargins(20, 15, 20, 15)
        
        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setStyleSheet("color: #a3a3a3; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        etiqueta_titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        self.etiqueta_valor = QLabel(valor)
        self.etiqueta_valor.setStyleSheet(f"color: {color}; font-size: 34px; font-weight: 800; border: none; background: transparent;")
        self.etiqueta_valor.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        distribucion.addWidget(etiqueta_titulo)
        distribucion.addStretch()
        distribucion.addWidget(self.etiqueta_valor)

    def actualizar_valor(self, valor):
        self.etiqueta_valor.setText(valor)


class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.asistente = AsistenteVigiData()
        self.escaneos_ejecutados = 0
        self.ultimo_escaneo = None
        self._monitor_message_cache = set()
        
        # Control de concurrencia
        self.escaneo_en_progreso = False
        
        self.setWindowTitle("PyOrganizer - Panel de Control")
        self.resize(1200, 800)
        # Fondo oscuro principal
        self.setStyleSheet("QMainWindow { background-color: #09090b; }")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.distribucion_principal = QHBoxLayout(self.central)
        self.distribucion_principal.setContentsMargins(0,0,0,0)
        self.distribucion_principal.setSpacing(0)

        # Contenedor Multi-vista para alternar los paneles derechos
        self.pila_vistas = QStackedWidget()

        self.inicializar_barra_lateral()
        self.inicializar_chat_asistente()
        self.inicializar_vistas_contenido() 
        self._maximize_on_current_screen()

        # Conectar señal global para refrescar estadísticas
        try:
            app_signals.stats_changed.connect(self.refrescar_panel_resumen)
            self.refrescar_panel_resumen()
        except Exception:
            pass

        # Mensajes iniciales del sistema
        try:
            self.agregar_mensaje_sistema("Hola, ¿cómo te puedo ayudar?")
            self.agregar_mensaje_sistema("Escribe /ayuda si no sabes qué comando usar.")
        except Exception:
            pass

        # Iniciar Watchdog en diferido
        try:
            QTimer.singleShot(3000, self.iniciar_watchdog)
        except Exception:
            pass

        # Temporizador global de escaneo
        try:
            self.temporizador_escaneo = QTimer(self)
            self.temporizador_escaneo.timeout.connect(self.iniciar_escaneo)
            self.temporizador_escaneo.start(60000)
        except Exception:
            pass

        # Arranque automático al iniciar
        QTimer.singleShot(3000, self.iniciar_escaneo)

    MAX_ACCIONES_EN_MEMORIA = 200
    MAX_MENSAJES_EN_MEMORIA = 200

    def agregar_mensaje_sistema(self, texto):
        etiqueta = QLabel(f"<b>Sistema:</b> {texto}")
        etiqueta.setStyleSheet("color: #e4e4e7; background-color: rgba(39, 39, 42, 0.8); padding: 10px; border-radius: 6px;")
        etiqueta.setWordWrap(True)
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta)
        self._limpiar_entradas_mensajes()

    def _limpiar_entradas_acciones(self):
        try:
            while self.lista_acciones.count() > self.MAX_ACCIONES_EN_MEMORIA:
                item = self.lista_acciones.itemAt(0)
                if not item:
                    break
                widget = item.widget()
                if widget:
                    self.lista_acciones.removeWidget(widget)
                    widget.deleteLater()
                else:
                    self.lista_acciones.removeItem(item)
        except Exception:
            pass

    def _limpiar_entradas_mensajes(self):
        
        try:
            while self.lista_mensajes.count() > self.MAX_MENSAJES_EN_MEMORIA:
                item = self.lista_mensajes.itemAt(0)
                if not item:
                    break
                widget = item.widget()
                if widget:
                    self.lista_mensajes.removeWidget(widget)
                    widget.deleteLater()
                else:
                    self.lista_mensajes.removeItem(item)
        except Exception:
            pass

    def iniciar_watchdog(self):
        try:
            from app.controlador.watcher_thread import WatcherThread
            self.perro_guardian = WatcherThread(self.asistente.modelo_org.db_path)
            try:
                self.perro_guardian._worker.move_result.connect(self.al_mover_archivo)
            except Exception:
                pass
            try:
                self.perro_guardian._worker.file_ready.connect(self.asistente.procesar_archivo_nuevo)
            except Exception:
                pass
            self.perro_guardian.start()
        except Exception:
            pass

    def inicializar_barra_lateral(self):
        """Barra lateral izquierda con transparencia y acentos amarillos"""
        barra_lateral = QFrame()
        barra_lateral.setFixedWidth(260)
        barra_lateral.setStyleSheet("background-color: rgba(15, 15, 15, 0.95); border-right: 1px solid rgba(255, 255, 255, 0.05);")
        distribucion_lateral = QVBoxLayout(barra_lateral)
        distribucion_lateral.setContentsMargins(0, 0, 0, 0)
        
        # Logo y Título
        contenedor_logo = QWidget()
        distribucion_logo = QVBoxLayout(contenedor_logo)
        distribucion_logo.setContentsMargins(25, 35, 25, 25)
        etiqueta_logo = QLabel("📁 PyOrganizer")
        etiqueta_logo.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 800; border: none;")
        distribucion_logo.addWidget(etiqueta_logo)
        distribucion_lateral.addWidget(contenedor_logo)

        # Estilos de botones
        self.estilo_boton_base = """
            QPushButton { 
                background: transparent; color: #a3a3a3; text-align: left; 
                padding: 14px 25px; border: none; font-size: 13px; font-weight: 600;
            } 
            QPushButton:hover { 
                background: rgba(234, 179, 8, 0.1); color: #eab308; 
            }
        """
        self.estilo_boton_activo = """
            QPushButton { 
                background: rgba(234, 179, 8, 0.15); color: #eab308; 
                text-align: left; padding: 14px 25px; border: none; 
                border-left: 4px solid #eab308; font-size: 13px; font-weight: 700;
            }
        """

        # Botones de navegación
        self.boton_resumen = QPushButton("Panel Resumen")
        self.boton_resumen.setStyleSheet(self.estilo_boton_activo)
        self.boton_resumen.clicked.connect(lambda: self.cambiar_vista(0, self.boton_resumen))
        distribucion_lateral.addWidget(self.boton_resumen)

        self.boton_configuracion = QPushButton("Configuración Global")
        self.boton_configuracion.setStyleSheet(self.estilo_boton_base)
        self.boton_configuracion.clicked.connect(lambda: self.cambiar_vista(1, self.boton_configuracion))
        distribucion_lateral.addWidget(self.boton_configuracion)
        
        self.boton_reglas = QPushButton("Reglas de Organización")
        self.boton_reglas.setStyleSheet(self.estilo_boton_base)
        self.boton_reglas.clicked.connect(lambda: self.cambiar_vista(2, self.boton_reglas))
        distribucion_lateral.addWidget(self.boton_reglas)

        distribucion_lateral.addStretch()
        
        # Botón de Escaneo
        contenedor_escaneo = QWidget()
        distribucion_escaneo = QVBoxLayout(contenedor_escaneo)
        distribucion_escaneo.setContentsMargins(25, 25, 25, 30)
        self.boton_escanear = QPushButton("ESCANEAR AHORA")
        self.boton_escanear.setStyleSheet("""
            QPushButton { 
                background: #eab308; color: #000000; font-weight: 800; font-size: 12px;
                padding: 14px; border-radius: 6px; border: none;
            } 
            QPushButton:hover { background: #facc15; } 
            QPushButton:disabled { background: rgba(255,255,255,0.1); color: #555555; }
        """)
        self.boton_escanear.clicked.connect(self.ejecutar_escaneo_asincrono)
        distribucion_escaneo.addWidget(self.boton_escanear)
        distribucion_lateral.addWidget(contenedor_escaneo)

        self.distribucion_principal.addWidget(barra_lateral)

    def inicializar_vistas_contenido(self):
        """Asigna y empaqueta las secciones dentro del QStackedWidget"""
        self.vista_panel = self.crear_panel_resumen()
        
        self.vista_configuracion = VistaConfiguracionGlobal(
            asistente=self.asistente,
            callback_regresar=lambda: self.cambiar_vista(0, self.boton_resumen)
        )
        
        self.vista_reglas = VistaReglasOrganizacion(
            asistente=self.asistente, 
            callback_regresar=lambda: self.cambiar_vista(0, self.boton_resumen)
        )

        self.pila_vistas.addWidget(self.vista_panel)     
        self.pila_vistas.addWidget(self.vista_configuracion) 
        self.pila_vistas.addWidget(self.vista_reglas)     

        # Refrescar vistas cuando cambie la pestaña activa (p. ej. recargar carpetas destino)
        try:
            self.pila_vistas.currentChanged.connect(self._on_pila_vistas_changed)
        except Exception:
            pass

        self.distribucion_principal.addWidget(self.pila_vistas)

    def cambiar_vista(self, indice, boton_activo):
        self.pila_vistas.setCurrentIndex(indice)
        
        self.boton_resumen.setStyleSheet(self.estilo_boton_base)
        self.boton_configuracion.setStyleSheet(self.estilo_boton_base)
        self.boton_reglas.setStyleSheet(self.estilo_boton_base)
        
        boton_activo.setStyleSheet(self.estilo_boton_activo)

    def _on_pila_vistas_changed(self, index):
        try:
            # índice 2 corresponde a VistaReglasOrganizacion en la pila
            if index == 2 and hasattr(self, 'vista_reglas'):
                try:
                    self.vista_reglas.actualizar_selector_carpetas()
                except Exception:
                    pass
        except Exception:
            pass

    def crear_panel_resumen(self):
        """Estructura e interfaz del Panel de Control principal"""
        contenido = QWidget()
        distribucion = QVBoxLayout(contenido)
        distribucion.setContentsMargins(40, 40, 40, 40)
        distribucion.setSpacing(30)

        # Cabecera
        cabecera = QVBoxLayout()
        cabecera.setSpacing(5)
        titulo = QLabel("Panel de Control")
        titulo.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;")
        subtitulo = QLabel("Motor de ordenamiento cíclico optimizado")
        subtitulo.setStyleSheet("color: #a3a3a3; font-size: 14px;")
        cabecera.addWidget(titulo)
        cabecera.addWidget(subtitulo)
        distribucion.addLayout(cabecera)

        # Grid de Tarjetas (Métricas)
        cuadricula = QGridLayout()
        cuadricula.setSpacing(20)
        
        total_mov = "0"
        total_reglas = "0"
        try:
            ruta_bd = self.asistente.modelo_org.db_path
            total_mov = f"{get_total_movidos(ruta_bd):,}"
            total_reglas = f"{get_total_reglas(ruta_bd):,}"
        except Exception:
            pass

        self.tarjeta_archivos = TarjetaMetrica("ARCHIVOS PROCESADOS", total_mov, "#ffffff")
        self.tarjeta_reglas = TarjetaMetrica("REGLAS ACTIVAS", total_reglas, "#eab308")
        self.tarjeta_escaneos = TarjetaMetrica("ESCANEOS EJECUTADOS", str(self.escaneos_ejecutados), "#22c55e")
        # Mostrar solo la hora en formato 12H para el último escaneo
        texto_ultimo = self.ultimo_escaneo.strftime("%I:%M %p") if self.ultimo_escaneo else "Nunca"
        self.tarjeta_ultimo = TarjetaMetrica("ÚLTIMO ESCANEO", texto_ultimo, "#eab308")

        cuadricula.addWidget(self.tarjeta_archivos, 0, 0)
        cuadricula.addWidget(self.tarjeta_reglas, 0, 1)
        cuadricula.addWidget(self.tarjeta_escaneos, 0, 2)
        cuadricula.addWidget(self.tarjeta_ultimo, 0, 3)
        distribucion.addLayout(cuadricula)

        # Gráfico de barras QtCharts
        self.vista_grafico_stats = QChartView()
        self.vista_grafico_stats.setRenderHint(QPainter.Antialiasing)
        self.vista_grafico_stats.setStyleSheet("background: transparent; border: none;")

        # Panel de Estadísticas
        marco_estadisticas = QFrame()
        marco_estadisticas.setStyleSheet("background-color: rgba(24, 24, 24, 0.6); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);")
        distribucion_estadisticas = QVBoxLayout(marco_estadisticas)
        distribucion_estadisticas.setContentsMargins(20, 20, 20, 20)
        titulo_stats = QLabel("Estadísticas de Extensiones")
        titulo_stats.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 14px; background: transparent; border: none;")
        distribucion_estadisticas.addWidget(titulo_stats)
        distribucion_estadisticas.addWidget(self.vista_grafico_stats)
        
        self.etiqueta_tipos_grafico = QLabel("Sin datos")
        self.etiqueta_tipos_grafico.setStyleSheet("color: #71717a; font-size: 12px; background: transparent; border: none;")
        distribucion_estadisticas.addWidget(self.etiqueta_tipos_grafico)

        # Panel de Últimas Acciones
        marco_acciones = QFrame()
        marco_acciones.setStyleSheet("background-color: rgba(24, 24, 24, 0.6); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);")
        distribucion_acciones = QVBoxLayout(marco_acciones)
        distribucion_acciones.setContentsMargins(20, 20, 20, 20)
        titulo_acciones = QLabel("Registro de Actividad")
        titulo_acciones.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 14px; background: transparent; border: none;")
        distribucion_acciones.addWidget(titulo_acciones)
        
        self.scroll_acciones = QScrollArea()
        self.scroll_acciones.setWidgetResizable(True)
        self.scroll_acciones.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget { background: transparent; }")
        self.contenedor_acciones = QWidget()
        self.lista_acciones = QVBoxLayout(self.contenedor_acciones)
        self.lista_acciones.setContentsMargins(0, 10, 0, 0)
        self.lista_acciones.setSpacing(6)
        self.lista_acciones.addStretch()
        self.scroll_acciones.setWidget(self.contenedor_acciones)
        distribucion_acciones.addWidget(self.scroll_acciones)

        # Distribución Inferior: Chat Asistente (Integrado directamente) | Estadísticas | Acciones
        distribucion_inferior = QHBoxLayout()
        distribucion_inferior.setSpacing(25)
        
        # Ajuste: dar más espacio al chat y reducir el gráfico central para mejor legibilidad
        try:
            self.widget_asistente.setMinimumWidth(480)
        except Exception:
            pass
        try:
            marco_estadisticas.setMaximumWidth(360)
        except Exception:
            pass

        distribucion_inferior.addWidget(self.widget_asistente, 5)
        distribucion_inferior.addWidget(marco_estadisticas, 2)
        distribucion_inferior.addWidget(marco_acciones, 3)

        distribucion.addLayout(distribucion_inferior, 1)
        return contenido

    def iniciar_escaneo(self):
        """Lógica centralizada para desplegar el Hilo del motor organizador."""
        # Monitoreo de memoria previo al escaneo
        try:
            memoria_antes = self._monitorear_memoria()
            self.agregar_mensaje_sistema(f"Memoria antes del escaneo: {memoria_antes:.1f} MB")
        except Exception:
            memoria_antes = None

        if self.escaneo_en_progreso:
            return

        self.escaneo_en_progreso = True
        self.boton_escanear.setEnabled(False)
        self.boton_escanear.setText("PROCESANDO...")

        try:
            if not hasattr(self, 'hilo_organizador') or self.hilo_organizador is None:
                self._motor_cache = MotorOrganizadorCore(self.asistente.modelo_org.db_path, self.asistente)
                self.hilo_organizador = HiloOrganizador(self._motor_cache)
                try:
                    self.hilo_organizador_ref = weakref.ref(self.hilo_organizador)
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "Error al iniciar escaneo", f"No se pudo iniciar el proceso de escaneo: {str(e)}")
            self.escaneo_en_progreso = False
            self.boton_escanear.setEnabled(True)
            self.boton_escanear.setText("ESCANEAR AHORA")
            return

        try:
            try:
                self.hilo_organizador.progreso_senal.disconnect()
            except Exception:
                pass
            try:
                self.hilo_organizador.finalizado_senal.disconnect()
            except Exception:
                pass

            self.hilo_organizador.progreso_senal.connect(self.registrar_accion_interfaz)
            self.hilo_organizador.finalizado_senal.connect(self.finalizar_escaneo)
            self.hilo_organizador.start()
        except Exception as e:
            QMessageBox.critical(self, "Error al iniciar escaneo", f"No se pudo iniciar el proceso de escaneo: {str(e)}")


    def ejecutar_escaneo_asincrono(self):
        if self.escaneo_en_progreso:
            return
        self.iniciar_escaneo()

    def finalizar_escaneo(self, total_archivos):
        self.escaneo_en_progreso = False
        self.escaneos_ejecutados += 1
        self.ultimo_escaneo = datetime.now()
        
        self.boton_escanear.setEnabled(True)
        self.boton_escanear.setText("ESCANEAR AHORA")

        if hasattr(self, 'hilo_organizador') and self.hilo_organizador is not None:
            try:
                self.hilo_organizador.progreso_senal.disconnect()
                self.hilo_organizador.finalizado_senal.disconnect()
            except Exception:
                pass
            self.hilo_organizador = None

        import gc
        gc.collect()    
        try:
            memoria_despues = self._monitorear_memoria()
            self.agregar_mensaje_sistema(f"Memoria después del escaneo: {memoria_despues:.1f} MB")
        except Exception:
            pass
        
        etiqueta_resumen = QLabel(f" Ciclo completado. Procesados: {total_archivos}")
        etiqueta_resumen.setStyleSheet("color: #000000; font-weight: 700; font-size: 11px; padding: 6px; background-color: #eab308; border-radius: 4px;")
        self.lista_acciones.insertWidget(self.lista_acciones.count() - 1, etiqueta_resumen)
        self._limpiar_entradas_acciones()
        self.scroll_acciones.verticalScrollBar().setValue(self.scroll_acciones.verticalScrollBar().maximum())
        
        self.refrescar_panel_resumen()

    def registrar_accion_interfaz(self, mensaje):
        # Evitar mensajes de monitor duplicados para cola/saturación
        if mensaje.startswith("👀 [Monitor]"):
            if mensaje in self._monitor_message_cache:
                return
            self._monitor_message_cache.add(mensaje)

        etiqueta_accion = QLabel(mensaje)
        etiqueta_accion.setStyleSheet("color: #4ade80; font-size: 11px; padding: 6px; background-color: rgba(34, 197, 94, 0.1); border-left: 2px solid #4ade80; border-radius: 3px;")
        self.lista_acciones.insertWidget(self.lista_acciones.count() - 1, etiqueta_accion)
        self._limpiar_entradas_acciones()
        self.scroll_acciones.verticalScrollBar().setValue(self.scroll_acciones.verticalScrollBar().maximum())

    def al_mover_archivo(self, info: dict):
        try:
            msg = f"👀 [Monitor] {info.get('message')} - {info.get('path')}"
            self.registrar_accion_interfaz(msg)
            try:
                app_signals.stats_changed.emit()
            except Exception:
                self.refrescar_panel_resumen()
        except Exception:
            pass

    def closeEvent(self, evento):
        try:
            if hasattr(self, 'perro_guardian') and self.perro_guardian is not None:
                self.perro_guardian.stop()
                self.perro_guardian.wait(1000)
                self.perro_guardian = None

            if hasattr(self, '_motor_cache'):
                self._motor_cache = None

            if hasattr(self,'_monitor_message_cache'):
                self._monitor_message_cache.clear()

            import gc
            gc.collect()  

        except Exception:
            pass
        super().closeEvent(evento)

    def _maximize_on_current_screen(self):
        try:
            pos = QCursor.pos()
            screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.setGeometry(geom)
            self.showMaximized()
        except Exception:
            try:
                self.showMaximized()
            except Exception:
                pass

    def _monitorear_memoria(self):
        proceso = psutil.Process(os.getpid())
        memoria = proceso.memory_info().rss / 1024 / 1024  # MB
        return memoria

    def refrescar_panel_resumen(self):
        try:
            ruta_bd = self.asistente.modelo_org.db_path
            total_mov = f"{get_total_movidos(ruta_bd):,}"
            total_reglas = f"{get_total_reglas(ruta_bd):,}"
            escaneos = str(self.escaneos_ejecutados)
            # Mostrar solo hora 12H para el último escaneo
            texto_ultimo = self.ultimo_escaneo.strftime("%I:%M %p") if self.ultimo_escaneo else "Nunca"
            
            self.tarjeta_archivos.actualizar_valor(total_mov)
            self.tarjeta_reglas.actualizar_valor(total_reglas)
            self.tarjeta_escaneos.actualizar_valor(escaneos)
            self.tarjeta_ultimo.actualizar_valor(texto_ultimo)
            
            from app.services import obtener_archivos_por_tipo
            top_archivos = obtener_archivos_por_tipo(ruta_bd, limite=5)
            texto_tipos = " | ".join([f"{ext}: {cnt}" for ext, cnt in top_archivos]) if top_archivos else "Sin datos recientes"
            self.etiqueta_tipos_grafico.setText(texto_tipos)

            if getattr(self, 'vista_grafico_stats', None):
                try:
                        colors = ["#eab308", "#22c55e", "#38bdf8", "#a855f7", "#f97316", "#fb7185"]
                        # Palette y fuentes extraídas del tema
                        bg_color = QColor(24, 24, 24, 0)
                        text_color = QColor("#e4e4e7")
                        accent_color = QColor("#eab308")

                        # Si hay muchas categorías, usar gráfico de barras para mejor legibilidad
                        if top_archivos and len(top_archivos) > 6:
                            categorias = [ext for ext, _ in top_archivos]
                            valores = [cnt for _, cnt in top_archivos]
                            set_series = QBarSet('Cantidad')
                            for v in valores:
                                set_series.append(v)
                            bar_series = QBarSeries()
                            bar_series.append(set_series)

                            grafico = QChart()
                            grafico.addSeries(bar_series)
                            grafico.setAnimationOptions(QChart.SeriesAnimations)
                            axis_x = QBarCategoryAxis()
                            axis_x.append(categorias)
                            try:
                                axis_x.setLabelsAngle(45)
                            except Exception:
                                pass
                            axis_x.setLabelsBrush(text_color)
                            grafico.addAxis(axis_x, Qt.AlignBottom)
                            bar_series.attachAxis(axis_x)

                            axis_y = QValueAxis()
                            axis_y.setLabelsBrush(text_color)
                            grafico.addAxis(axis_y, Qt.AlignLeft)
                            bar_series.attachAxis(axis_y)

                            grafico.legend().setVisible(False)
                            grafico.setTitle('Distribución por extensión')
                        else:
                            series = QPieSeries()
                            total = sum([cnt for _, cnt in top_archivos]) if top_archivos else 0
                            for idx, (ext, cnt) in enumerate(top_archivos):
                                slice = QPieSlice(ext, cnt)
                                slice.setLabelVisible(True)
                                slice.setLabel(f"{ext} ({cnt})")
                                slice.setBrush(QColor(colors[idx % len(colors)]))
                                slice.setBorderColor(QColor(255, 255, 255, 60))
                                slice.setLabelColor(text_color)
                                series.append(slice)
                            # Si no hay datos, mostrar un slice único
                            if not top_archivos:
                                s = QPieSlice('Sin datos', 1)
                                s.setLabelVisible(True)
                                s.setBrush(QColor("#6b7280"))
                                s.setBorderColor(QColor(255, 255, 255, 60))
                                s.setLabelColor(text_color)
                                series.append(s)

                            grafico = QChart()
                            grafico.addSeries(series)
                            grafico.setAnimationOptions(QChart.SeriesAnimations)
                            grafico.legend().setAlignment(Qt.AlignRight)
                            grafico.setTitle('Distribución por extensión')

                        # Harmonizar colores y márgenes con el tema de la app
                        try:
                            grafico.setBackgroundBrush(bg_color)
                        except Exception:
                            pass
                        try:
                            grafico.setTitleBrush(accent_color)
                        except Exception:
                            pass
                        try:
                            grafico.setMargins(10)
                        except Exception:
                            pass

                        # Forzar estilos de leyenda y ejes para coincidir con la UI
                        try:
                            grafico.legend().setLabelColor(text_color)
                        except Exception:
                            pass

                        self.vista_grafico_stats.setChart(grafico)
                        self.vista_grafico_stats.setRenderHint(QPainter.Antialiasing)
                except Exception:
                    pass

        except Exception:
            pass

    def inicializar_chat_asistente(self):
        """Inicializa el widget del Asistente Virtual con diseño integrado"""
        self.widget_asistente = QFrame()
        self.widget_asistente.setStyleSheet("""
            QFrame#widget_asistente {
                background-color: rgba(24, 24, 24, 0.6); 
                border-radius: 12px; 
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        self.widget_asistente.setObjectName("widget_asistente")

        distribucion_chat = QVBoxLayout(self.widget_asistente)
        distribucion_chat.setContentsMargins(0,0,0,0)
        distribucion_chat.setSpacing(0)

        # Cabecera del Chat
        marco_cabecera = QFrame()
        marco_cabecera.setStyleSheet("background-color: rgba(0, 0, 0, 0.2); border-top-left-radius: 12px; border-top-right-radius: 12px;")
        distribucion_cabecera = QHBoxLayout(marco_cabecera)
        distribucion_cabecera.setContentsMargins(20, 15, 20, 15)
        titulo_cabecera = QLabel("Asistente Virtual")
        titulo_cabecera.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 14px; background: transparent;")
        distribucion_cabecera.addWidget(titulo_cabecera)
        distribucion_cabecera.addStretch()
        distribucion_chat.addWidget(marco_cabecera)

        # Cuerpo del Chat
        cuerpo_chat = QWidget()
        cuerpo_chat.setStyleSheet("background: transparent;")
        distribucion_cuerpo = QVBoxLayout(cuerpo_chat)
        distribucion_cuerpo.setContentsMargins(20, 15, 20, 20)
        distribucion_cuerpo.setSpacing(15)
        
        self.area_mensajes = QScrollArea()
        self.area_mensajes.setWidgetResizable(True)
        self.area_mensajes.setStyleSheet("border: none; background: transparent;")
        self.area_mensajes.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.area_mensajes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.contenedor_mensajes = QWidget()
        self.contenedor_mensajes.setStyleSheet("background: transparent;")
        self.lista_mensajes = QVBoxLayout(self.contenedor_mensajes)
        self.lista_mensajes.setContentsMargins(0,0,0,0)
        self.lista_mensajes.setSpacing(10)
        self.lista_mensajes.addStretch()
        self.area_mensajes.setWidget(self.contenedor_mensajes)
        distribucion_cuerpo.addWidget(self.area_mensajes)

        # Entrada de Texto
        self.entrada_texto = QLineEdit()
        self.entrada_texto.setPlaceholderText("Escribe un comando aquí...")
        self.entrada_texto.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.3); 
                color: #ffffff; padding: 12px 15px; 
                border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLineEdit:focus { border: 1px solid #eab308; }
        """)
        self.entrada_texto.setFixedHeight(45)
        self.entrada_texto.returnPressed.connect(self.enviar_comando)
        distribucion_cuerpo.addWidget(self.entrada_texto)

        distribucion_chat.addWidget(cuerpo_chat)

        # Sugerencias
        self.contenedor_sugerencias = QWidget()
        self.contenedor_sugerencias.setStyleSheet("background: transparent;")
        self.distribucion_sugerencias = QHBoxLayout(self.contenedor_sugerencias)
        self.distribucion_sugerencias.setContentsMargins(20, 0, 20, 15)
        self.distribucion_sugerencias.setSpacing(10)
        self.contenedor_sugerencias.hide()
        distribucion_chat.addWidget(self.contenedor_sugerencias)

    def enviar_comando(self):
        texto = self.entrada_texto.text().strip()
        if not texto: return
        if texto.lower() in ['/ayuda', 'ayuda']:
            self.mostrar_ayuda()
            self.entrada_texto.clear()
            return

        respuesta = self.asistente.procesar_peticion(texto)
        
        etiqueta_usuario = QLabel(f"<b>Tú:</b> {texto}")
        etiqueta_usuario.setStyleSheet("color: #a3a3a3; font-size: 12px; padding: 5px;")
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta_usuario)

        if isinstance(respuesta, dict) and 'suggestions' in respuesta:
            self.agregar_mensaje_sistema(respuesta.get('message'))
            
            for i in reversed(range(self.distribucion_sugerencias.count())):
                item = self.distribucion_sugerencias.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        self.distribucion_sugerencias.removeWidget(widget)
                        widget.deleteLater()
                    else:
                        self.distribucion_sugerencias.removeItem(item)

            for sugerencia in respuesta.get('suggestions', []):
                boton_sug = QPushButton(sugerencia)
                boton_sug.setStyleSheet("""
                    QPushButton { background: rgba(234, 179, 8, 0.15); color: #eab308; padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(234, 179, 8, 0.3); font-size: 11px; } 
                    QPushButton:hover { background: rgba(234, 179, 8, 0.25); }
                """)
                boton_sug.clicked.connect(lambda _, s=sugerencia: self.usar_sugerencia(s))
                self.distribucion_sugerencias.addWidget(boton_sug)
            self.contenedor_sugerencias.show()
        else:
            self.agregar_mensaje_sistema(str(respuesta))
            self.contenedor_sugerencias.hide()

        self.area_mensajes.verticalScrollBar().setValue(self.area_mensajes.verticalScrollBar().maximum())
        self.entrada_texto.clear()

    def usar_sugerencia(self, texto_sugerencia):
        self.entrada_texto.setText(texto_sugerencia)
        self.enviar_comando()

    def mostrar_ayuda(self):
        try:
            claves_alias = list(self.asistente.rutas_atajo.keys())
        except Exception:
            claves_alias = ['escritorio', 'documentos', 'descargas']

        ejemplos = [
            f"Mueve <b>archivos</b> a <b>{claves_alias[1]}</b>",
            f"Crea una carpeta llamada <b>fotos</b> en <b>{claves_alias[0]}</b>",
            f"Mueve <b>pdf</b> a <b>{claves_alias[2]}</b>",
            "Agregar regla (comando directo): <b>asignar .pdf a Destino_Documentos</b>",
            "Listar: <b>listar reglas</b> | <b>mostrar destinos</b>",
        ]
        html_alias = ''.join(f"<li>{a}</li>" for a in claves_alias[:6])

        html_ayuda = f"<div style='color:#e4e4e7; font-size:12px; line-height:1.5;'>"
        html_ayuda += "<b style='color:#eab308;'>Comandos útiles</b><ul>"
        for ej in ejemplos:
            html_ayuda += f"<li>{ej}</li>"
        html_ayuda += "</ul>"
        html_ayuda += "<b style='color:#eab308;'>Alias reconocidos</b><ul>" + html_alias + "</ul></div>"

        etiqueta_ayuda = QLabel(html_ayuda)
        etiqueta_ayuda.setStyleSheet("background-color: rgba(39, 39, 42, 0.8); padding: 12px; border-radius: 6px; border-left: 3px solid #eab308;")
        etiqueta_ayuda.setTextFormat(Qt.RichText)
        
        etiqueta_cmd = QLabel(f"<b>Tú:</b> /ayuda")
        etiqueta_cmd.setStyleSheet("color: #a3a3a3; font-size: 12px; padding: 5px;")
        
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta_cmd)
        self.lista_mensajes.insertWidget(self.lista_mensajes.count()-1, etiqueta_ayuda)
        self.area_mensajes.verticalScrollBar().setValue(self.area_mensajes.verticalScrollBar().maximum())