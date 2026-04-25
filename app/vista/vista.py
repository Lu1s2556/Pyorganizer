import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon

# --- CLASE DE TARJETA ESTILIZADA (REUTILIZABLE) ---
class TarjetaMetrica(QFrame):
    def __init__(self, titulo, valor, color_acento, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Estilo de la tarjeta
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #252526;
                border-radius: 8px;
                border: 1px solid #3e3e42;
                padding: 15px;
            }}
            QFrame:hover {{
                border: 1px solid {color_acento};
            }}
        """)
        
        # Sombra suave para efecto "elevado"
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(10)
        sombra.setXOffset(0)
        sombra.setYOffset(4)
        sombra.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet("color: #aaaaaa; font-size: 13px; font-weight: bold; border: none;")
        
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(f"color: {color_acento}; font-size: 32px; font-weight: bold; border: none;")
        
        # Subtítulo simulado (ej: "últimas 24h")
        self.lbl_subtítulo = QLabel("Actualizado")
        self.lbl_subtítulo.setStyleSheet("color: #666666; font-size: 11px; border: none;")

        layout.addWidget(self.lbl_titulo)
        layout.addWidget(self.lbl_valor)
        layout.addWidget(self.lbl_subtítulo)
        layout.addStretch()

# --- CLASE PRINCIPAL DEL DASHBOARD ---
class DashboardOrganizador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VigiData - Organizador Inteligente de Archivos")
        self.resize(1100, 750)
        self.setMinimumSize(900, 650)
        
        # Configurar Estilo Global
        self.set_estilo_base()

        # Widget Central y Layout Principal
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QHBoxLayout(self.widget_central)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # Inicializar Componentes
        self.inicializar_barra_lateral()
        self.inicializar_area_contenido()

    def set_estilo_base(self):
        """Define los colores y fuentes globales de la aplicación."""
        fuente_id = QFont("Segoe UI", 10)
        self.setFont(fuente_id)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { color: #cccccc; }
            QLabel { background: transparent; }
        """)

    def inicializar_barra_lateral(self):
        """Crea la navegación lateral izquierda."""
        self.barra_lateral = QFrame()
        self.barra_lateral.setFixedWidth(240)
        self.barra_lateral.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-right: 1px solid #3e3e42;
            }
            QPushButton {
                color: #cccccc;
                background-color: transparent;
                border: none;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                border-radius: 5px;
                margin: 2px 10px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2d2d30;
            }
            QPushButton#activo {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
            QPushButton#boton_accion {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton#boton_accion:hover {
                background-color: #218838;
            }
        """)
        
        layout_lateral = QVBoxLayout(self.barra_lateral)
        layout_lateral.setContentsMargins(0, 10, 0, 10)
        layout_lateral.setSpacing(5)

        # Sección Logo/Título
        contenedor_logo = QWidget()
        layout_logo = QHBoxLayout(contenedor_logo)
        self.lbl_logo_icono = QLabel("📁") # Icono Unicode simple
        self.lbl_logo_icono.setStyleSheet("font-size: 24px;")
        self.lbl_logo_texto = QLabel("VigiData")
        self.lbl_logo_texto.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        layout_logo.addWidget(self.lbl_logo_icono)
        layout_logo.addWidget(self.lbl_logo_texto)
        layout_logo.addStretch()
        
        layout_lateral.addWidget(contenedor_logo)
        layout_lateral.addSpacing(20)

        # Botones de Navegación
        self.btn_inicio = QPushButton("  Panel Resumen")
        self.btn_inicio.setObjectName("activo")
        
        self.btn_reglas = QPushButton("  Reglas de IA")
        self.btn_historial = QPushButton("  Historial")
        self.btn_config = QPushButton("  Configuración")
        
        layout_lateral.addWidget(self.btn_inicio)
        layout_lateral.addWidget(self.btn_reglas)
        layout_lateral.addWidget(self.btn_historial)
        layout_lateral.addStretch() # Empuja el resto hacia abajo
        
        # Botón de acción principal
        self.btn_escanear = QPushButton("⚡ ESCANEAR AHORA")
        self.btn_escanear.setObjectName("boton_accion")
        self.btn_escanear.setMinimumHeight(45)
        layout_lateral.addWidget(self.btn_escanear)
        
        # Versión al pie
        lbl_version = QLabel("v0.1.0-alpha")
        lbl_version.setStyleSheet("color: #555555; font-size: 10px; margin: 10px;")
        lbl_version.setAlignment(Qt.AlignCenter)
        layout_lateral.addWidget(lbl_version)

        self.layout_principal.addWidget(self.barra_lateral)

    def inicializar_area_contenido(self):
        """Crea el área principal donde se muestran los datos."""
        widget_contenido = QWidget()
        layout_v_contenido = QVBoxLayout(widget_contenido)
        layout_v_contenido.setContentsMargins(30, 20, 30, 30)
        layout_v_contenido.setSpacing(20)

        # --- CABECERA DE LA PÁGINA ---
        cabecera = QWidget()
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(0, 0, 0, 0)
        
        div_titulo = QWidget()
        layout_div_titulo = QVBoxLayout(div_titulo)
        layout_div_titulo.setContentsMargins(0,0,0,0)
        layout_div_titulo.setSpacing(0)
        
        self.lbl_pagina_titulo = QLabel("Panel de Control")
        self.lbl_pagina_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        
        self.lbl_pagina_subtitulo = QLabel("Bienvenido al organizador inteligente optimizado.")
        self.lbl_pagina_subtitulo.setStyleSheet("color: #888888; font-size: 14px;")
        
        layout_div_titulo.addWidget(self.lbl_pagina_titulo)
        layout_div_titulo.addWidget(self.lbl_pagina_subtitulo)

        # Botón de estado de Watchdog (Simulado)
        self.btn_estado_servicio = QPushButton("● Servicio Activo")
        self.btn_estado_servicio.setStyleSheet("""
            QPushButton {
                background-color: #2d2d30;
                color: #28a745;
                border: 1px solid #3e3e42;
                padding: 8px 15px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout_cabecera.addWidget(div_titulo)
        layout_cabecera.addStretch()
        layout_cabecera.addWidget(self.btn_estado_servicio)
        
        layout_v_contenido.addWidget(cabecera)

        # --- SECCIÓN DE TARJETAS (MÉTRICAS) ---
        self.contenedor_metricas = QWidget()
        self.layout_grid_metricas = QGridLayout(self.contenedor_metricas)
        self.layout_grid_metricas.setContentsMargins(0, 0, 0, 0)
        self.layout_grid_metricas.setSpacing(20)

        # Creación de maquetas de tarjetas
        self.card_archivos = TarjetaMetrica("ARCHIVOS PROCESADOS", "1,250", "#007acc")
        self.card_categorias = TarjetaMetrica("CATEGORÍAS IA", "12", "#886ce4")
        self.card_precision = TarjetaMetrica("PRECISIÓN NLP", "96.4%", "#28a745")
        self.card_ahorro = TarjetaMetrica("ESPACIO LIBERADO", "14.2 GB", "#ffc107")

        # Añadir al grid (fila, columna)
        self.layout_grid_metricas.addWidget(self.card_archivos, 0, 0)
        self.layout_grid_metricas.addWidget(self.card_categorias, 0, 1)
        self.layout_grid_metricas.addWidget(self.card_precision, 0, 2)
        self.layout_grid_metricas.addWidget(self.card_ahorro, 0, 3)

        layout_v_contenido.addWidget(self.contenedor_metricas)

        # --- SECCIÓN INFERIOR (Detalles y Actividad) ---
        self.contenedor_inferior = QWidget()
        self.layout_h_inferior = QHBoxLayout(self.contenedor_inferior)
        self.layout_h_inferior.setContentsMargins(0, 0, 0, 0)
        self.layout_h_inferior.setSpacing(20)

        # 1. Panel de Gráfico/Visualización (Placeholder)
        self.panel_visualizacion = QFrame()
        self.panel_visualizacion.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3e3e42;")
        self.layout_v_vis = QVBoxLayout(self.panel_visualizacion)
        
        self.lbl_tit_vis = QLabel("Distribución de Archivos por Categoría")
        self.lbl_tit_vis.setStyleSheet("font-weight: bold; color: white; padding: 10px; font-size: 14px;")
        self.lbl_tit_vis.setAlignment(Qt.AlignCenter)
        
        # Simulamos un gráfico con un label grande y borde
        self.mock_grafico = QLabel("MOCKUP DE GRÁFICO TIPO PIE\n(Usa PyQtGraph aquí para producción)")
        self.mock_grafico.setStyleSheet("border: 2px dashed #3e3e42; color: #555555; margin: 20px;")
        self.mock_grafico.setAlignment(Qt.AlignCenter)
        
        self.layout_v_vis.addWidget(self.lbl_tit_vis)
        self.layout_v_vis.addWidget(self.mock_grafico, 1) # Factor estiramiento 1

        # 2. Panel de Última Actividad (Lista simula SQLite)
        self.panel_actividad = QFrame()
        self.panel_actividad.setMinimumWidth(350)
        self.panel_actividad.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3e3e42;")
        self.layout_v_act = QVBoxLayout(self.panel_actividad)
        
        self.lbl_tit_act = QLabel("Últimas Acciones Inteligentes")
        self.lbl_tit_act.setStyleSheet("font-weight: bold; color: white; padding: 10px; font-size: 14px;")
        
        # Área de scroll para la lista de actividad
        self.scroll_actividad = QScrollArea()
        self.scroll_actividad.setWidgetResizable(True)
        self.scroll_actividad.setStyleSheet("border: none; background: transparent;")
        
        self.contenedor_lista = QWidget()
        self.contenedor_lista.setStyleSheet("background: transparent;")
        self.layout_lista = QVBoxLayout(self.contenedor_lista)
        self.layout_lista.setContentsMargins(5, 5, 5, 5)
        self.layout_lista.setSpacing(8)

        # Añadir elementos de maqueta a la lista
        self.añadir_item_actividad("📄 reporte_final.pdf", "Mover -> /Documentos/Informes", "10m ago")
        self.añadir_item_actividad("📸 img_001.jpg", "Mover -> /Imágenes/Fotos", "15m ago")
        self.añadir_item_actividad("📊 datos_2023.csv", "Mover -> /Documentos/Datasets", "22m ago")
        self.añadir_item_actividad("🎵 cancion.mp3", "Ignorado (Sin Regla)", "30m ago")
        self.añadir_item_actividad("📄 tesis_v2.docx", "Mover -> /Documentos/Estudios", "1h ago")
        self.layout_lista.addStretch() # Empuja hacia arriba

        self.scroll_actividad.setWidget(self.contenedor_lista)
        
        self.layout_v_act.addWidget(self.lbl_tit_act)
        self.layout_v_act.addWidget(self.scroll_actividad)

        # Añadir paneles al layout inferior
        self.layout_h_inferior.addWidget(self.panel_visualizacion, 2) # Más ancho
        self.layout_h_inferior.addWidget(self.panel_actividad, 1) # Más angosto

        layout_v_contenido.addWidget(self.contenedor_inferior, 1) # Factor de estiramiento 1

        # Barra de estado inferior (Footer)
        self.barra_estado = QFrame()
        self.barra_estado.setFixedHeight(25)
        self.barra_estado.setStyleSheet("background-color: #007acc; color: white; border-top: 1px solid #3e3e42;")
        layout_estado = QHBoxLayout(self.barra_estado)
        layout_estado.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_estado_bd = QLabel("Base de Datos: SQLite Conectada")
        self.lbl_estado_bd.setStyleSheet("color: white; font-size: 11px;")
        self.lbl_memoria = QLabel("RAM Uso (UI): ~45MB") # Hardcoded para maqueta
        self.lbl_memoria.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        
        layout_estado.addWidget(self.lbl_estado_bd)
        layout_estado.addStretch()
        layout_estado.addWidget(self.lbl_memoria)
        
        layout_v_contenido.addWidget(self.barra_estado)

        self.layout_principal.addWidget(widget_contenido)

    def añadir_item_actividad(self, archivo, accion, tiempo):
        """Helper para crear filas de actividad rápidas."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 4px;
                padding: 8px;
                border: 1px solid #2d2d30;
            }
            QFrame:hover {
                background-color: #2d2d30;
            }
        """)
        layout = QHBoxLayout(item)
        layout.setContentsMargins(5, 2, 5, 2)
        
        icono = QLabel("✅")
        # Asegurarnos de que el texto no se corte si el panel es estrecho
        lbl_archivo = QLabel(archivo)
        lbl_archivo.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        lbl_archivo.setMinimumWidth(100) 
        
        lbl_accion = QLabel(accion)
        lbl_accion.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        
        lbl_tiempo = QLabel(tiempo)
        lbl_tiempo.setStyleSheet("color: #666666; font-size: 11px;")
        lbl_tiempo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(icono)
        layout.addWidget(lbl_archivo)
        layout.addWidget(lbl_accion, 1) # Toma el espacio central
        layout.addWidget(lbl_tiempo)
        
        self.layout_lista.addWidget(item)

if __name__ == "__main__":
    # Esto permite probar la vista de forma independiente
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # Fuente por defecto más moderna si está disponible
    app.setFont(QFont("Segoe UI", 9)) 
    ventana = DashboardOrganizador()
    ventana.show()
    sys.exit(app.exec())