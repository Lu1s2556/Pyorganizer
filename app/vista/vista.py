import sys
import os
import re
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QSizePolicy, QGraphicsDropShadowEffect, QLineEdit)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon

# --- IMPORTACIÓN DE IA (Scikit-Learn) ---
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# =================================================================
# 🧠 MODELO: IA DE CLASIFICACIÓN Y EXTRACCIÓN (NUEVO COMPONENTE)
# =================================================================
class AnalizadorIA:
    def __init__(self):
        self.vectorizador = CountVectorizer()
        self.modelo = MultinomialNB()
        self.categorias = {
            "Documentos": ["pdf", "docx", "txt", "tareas", "informe", "escrito", "tesis", "universidad"],
            "Imagenes": ["fotos", "capturas", "dibujos", "png", "jpg", "imagenes", "vacaciones"],
            "Videos": ["peliculas", "grabaciones", "mp4", "videos", "clips"],
            "Codigo": ["python", "scripts", "programas", "html", "codigo", "desarrollo"]
        }
        self._entrenar()

    def _entrenar(self):
        textos, etiquetas = [], []
        for cat, palabras in self.categorias.items():
            for p in palabras:
                textos.append(p)
                etiquetas.append(cat)
        X = self.vectorizador.fit_transform(textos)
        self.modelo.fit(X, etiquetas)

    def extraer_nombre_especifico(self, texto):
        patrones = [r"llamada\s+([\w\s]+)", r"nombre\s+([\w\s]+)", r"carpeta\s+([\w\s]+)"]
        for p in patrones:
            coincidencia = re.search(p, texto, re.IGNORECASE)
            if coincidencia:
                return coincidencia.group(1).strip().title()
        return None

    def predecir_categoria(self, texto):
        X_nuevo = self.vectorizador.transform([texto.lower()])
        return self.modelo.predict(X_nuevo)[0]

# --- NOTIFICACIÓN FLOTANTE (NUEVO COMPONENTE) ---
class NotificacionToast(QFrame):
    def __init__(self, mensaje, padre=None):
        super().__init__(padre)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: #28a745; color: white; border-radius: 8px; padding: 12px;")
        layout = QHBoxLayout(self)
        self.label = QLabel(f"🤖 IA: {mensaje}")
        self.label.setStyleSheet("font-weight: bold; font-size: 12px; border: none;")
        layout.addWidget(self.label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)

    def mostrar(self, pos):
        self.move(pos)
        self.show()
        self.timer.start(3500)

# --- CLASE DE TARJETA ESTILIZADA (REUTILIZABLE) ---
class TarjetaMetrica(QFrame):
    def __init__(self, titulo, valor, color_acento, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
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
        
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(10)
        sombra.setXOffset(0)
        sombra.setYOffset(4)
        sombra.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet("color: #aaaaaa; font-size: 13px; font-weight: bold; border: none;")
        
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(f"color: {color_acento}; font-size: 32px; font-weight: bold; border: none;")
        
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
        # INICIALIZACIÓN DE LA IA
        self.ia = AnalizadorIA()
        
        self.setWindowTitle("VigiData - Organizador Inteligente de Archivos")
        self.resize(1100, 750)
        self.setMinimumSize(900, 650)
        
        self.set_estilo_base()

        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QHBoxLayout(self.widget_central)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        self.inicializar_barra_lateral()
        self.inicializar_area_contenido()

    def set_estilo_base(self):
        fuente_id = QFont("Segoe UI", 10)
        self.setFont(fuente_id)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { color: #cccccc; }
            QLabel { background: transparent; }
        """)

    def inicializar_barra_lateral(self):
        self.barra_lateral = QFrame()
        self.barra_lateral.setFixedWidth(240)
        self.barra_lateral.setStyleSheet("""
            QFrame { background-color: #252526; border-right: 1px solid #3e3e42; }
            QPushButton {
                color: #cccccc; background-color: transparent; border: none;
                padding: 12px 20px; text-align: left; font-size: 14px;
                font-weight: 500; border-radius: 5px; margin: 2px 10px;
            }
            QPushButton:hover { background-color: #3e3e42; color: white; }
            QPushButton#activo { background-color: #007acc; color: white; font-weight: bold; }
            QPushButton#boton_accion { background-color: #28a745; color: white; font-weight: bold; margin-top: 20px; }
        """)
        
        layout_lateral = QVBoxLayout(self.barra_lateral)
        layout_lateral.setContentsMargins(0, 10, 0, 10)
        layout_lateral.setSpacing(5)

        contenedor_logo = QWidget()
        layout_logo = QHBoxLayout(contenedor_logo)
        self.lbl_logo_icono = QLabel("📁")
        self.lbl_logo_icono.setStyleSheet("font-size: 24px;")
        self.lbl_logo_texto = QLabel("VigiData")
        self.lbl_logo_texto.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        layout_logo.addWidget(self.lbl_logo_icono)
        layout_logo.addWidget(self.lbl_logo_texto)
        layout_logo.addStretch()
        layout_lateral.addWidget(contenedor_logo)

        # --- PANEL DE COMANDO IA (AGREGADO) ---
        self.panel_ia = QFrame()
        self.panel_ia.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; border: 1px solid #3e3e42; margin: 10px;")
        layout_ia = QVBoxLayout(self.panel_ia)
        lbl_ia = QLabel("COMANDO INTELIGENTE")
        lbl_ia.setStyleSheet("color: #007acc; font-size: 10px; font-weight: bold; border: none;")
        self.entrada_ia = QLineEdit()
        self.entrada_ia.setPlaceholderText("Ej: Carpeta llamada Tareas")
        self.entrada_ia.setStyleSheet("background-color: #2d2d30; color: white; padding: 8px; border: 1px solid #3e3e42;")
        self.entrada_ia.returnPressed.connect(self.procesar_ia)
        btn_ia = QPushButton("Ejecutar IA")
        btn_ia.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; padding: 5px; margin: 0px;")
        btn_ia.clicked.connect(self.procesar_ia)
        layout_ia.addWidget(lbl_ia)
        layout_ia.addWidget(self.entrada_ia)
        layout_ia.addWidget(btn_ia)
        layout_lateral.addWidget(self.panel_ia)

        layout_lateral.addSpacing(10)
        self.btn_inicio = QPushButton("  Panel Resumen")
        self.btn_inicio.setObjectName("activo")
        self.btn_reglas = QPushButton("  Reglas de IA")
        self.btn_historial = QPushButton("  Historial")
        self.btn_config = QPushButton("  Configuración")
        
        layout_lateral.addWidget(self.btn_inicio)
        layout_lateral.addWidget(self.btn_reglas)
        layout_lateral.addWidget(self.btn_historial)
        layout_lateral.addStretch()
        
        self.btn_escanear = QPushButton("⚡ ESCANEAR AHORA")
        self.btn_escanear.setObjectName("boton_accion")
        self.btn_escanear.setMinimumHeight(45)
        layout_lateral.addWidget(self.btn_escanear)
        
        lbl_version = QLabel("v0.1.0-alpha")
        lbl_version.setStyleSheet("color: #555555; font-size: 10px; margin: 10px;")
        lbl_version.setAlignment(Qt.AlignCenter)
        layout_lateral.addWidget(lbl_version)

        self.layout_principal.addWidget(self.barra_lateral)

    def inicializar_area_contenido(self):
        widget_contenido = QWidget()
        layout_v_contenido = QVBoxLayout(widget_contenido)
        layout_v_contenido.setContentsMargins(30, 20, 30, 30)
        layout_v_contenido.setSpacing(20)

        cabecera = QWidget()
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(0, 0, 0, 0)
        div_titulo = QWidget()
        layout_div_titulo = QVBoxLayout(div_titulo)
        layout_div_titulo.setContentsMargins(0,0,0,0)
        self.lbl_pagina_titulo = QLabel("Panel de Control")
        self.lbl_pagina_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        self.lbl_pagina_subtitulo = QLabel("Bienvenido al organizador inteligente optimizado.")
        self.lbl_pagina_subtitulo.setStyleSheet("color: #888888; font-size: 14px;")
        layout_div_titulo.addWidget(self.lbl_pagina_titulo)
        layout_div_titulo.addWidget(self.lbl_pagina_subtitulo)
        self.btn_estado_servicio = QPushButton("● Servicio Activo")
        self.btn_estado_servicio.setStyleSheet("background-color: #2d2d30; color: #28a745; border: 1px solid #3e3e42; padding: 8px 15px; border-radius: 15px; font-weight: bold; font-size: 12px;")
        layout_cabecera.addWidget(div_titulo)
        layout_cabecera.addStretch()
        layout_cabecera.addWidget(self.btn_estado_servicio)
        layout_v_contenido.addWidget(cabecera)

        self.contenedor_metricas = QWidget()
        self.layout_grid_metricas = QGridLayout(self.contenedor_metricas)
        self.layout_grid_metricas.setContentsMargins(0, 0, 0, 0)
        self.layout_grid_metricas.setSpacing(20)
        self.card_archivos = TarjetaMetrica("ARCHIVOS PROCESADOS", "1,250", "#007acc")
        self.card_categorias = TarjetaMetrica("CATEGORÍAS IA", "12", "#886ce4")
        self.card_precision = TarjetaMetrica("PRECISIÓN NLP", "96.4%", "#28a745")
        self.card_ahorro = TarjetaMetrica("ESPACIO LIBERADO", "14.2 GB", "#ffc107")
        self.layout_grid_metricas.addWidget(self.card_archivos, 0, 0)
        self.layout_grid_metricas.addWidget(self.card_categorias, 0, 1)
        self.layout_grid_metricas.addWidget(self.card_precision, 0, 2)
        self.layout_grid_metricas.addWidget(self.card_ahorro, 0, 3)
        layout_v_contenido.addWidget(self.contenedor_metricas)

        self.contenedor_inferior = QWidget()
        self.layout_h_inferior = QHBoxLayout(self.contenedor_inferior)
        self.layout_h_inferior.setContentsMargins(0, 0, 0, 0)
        self.layout_h_inferior.setSpacing(20)

        self.panel_visualizacion = QFrame()
        self.panel_visualizacion.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3e3e42;")
        self.layout_v_vis = QVBoxLayout(self.panel_visualizacion)
        self.lbl_tit_vis = QLabel("Distribución de Archivos por Categoría")
        self.lbl_tit_vis.setStyleSheet("font-weight: bold; color: white; padding: 10px; font-size: 14px;")
        self.mock_grafico = QLabel("MOCKUP DE GRÁFICO TIPO PIE\n(Usa PyQtGraph aquí para producción)")
        self.mock_grafico.setStyleSheet("border: 2px dashed #3e3e42; color: #555555; margin: 20px;")
        self.mock_grafico.setAlignment(Qt.AlignCenter)
        self.layout_v_vis.addWidget(self.lbl_tit_vis)
        self.layout_v_vis.addWidget(self.mock_grafico, 1)

        self.panel_actividad = QFrame()
        self.panel_actividad.setMinimumWidth(350)
        self.panel_actividad.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3e3e42;")
        self.layout_v_act = QVBoxLayout(self.panel_actividad)
        self.lbl_tit_act = QLabel("Últimas Acciones Inteligentes")
        self.lbl_tit_act.setStyleSheet("font-weight: bold; color: white; padding: 10px; font-size: 14px;")
        self.scroll_actividad = QScrollArea()
        self.scroll_actividad.setWidgetResizable(True)
        self.scroll_actividad.setStyleSheet("border: none; background: transparent;")
        self.contenedor_lista = QWidget()
        self.layout_lista = QVBoxLayout(self.contenedor_lista)
        self.layout_lista.setSpacing(8)
        self.añadir_item_actividad("📄 reporte_final.pdf", "Mover -> /Documentos/Informes", "10m ago")
        self.añadir_item_actividad("📸 img_001.jpg", "Mover -> /Imágenes/Fotos", "15m ago")
        self.layout_lista.addStretch()
        self.scroll_actividad.setWidget(self.contenedor_lista)
        self.layout_v_act.addWidget(self.lbl_tit_act)
        self.layout_v_act.addWidget(self.scroll_actividad)

        self.layout_h_inferior.addWidget(self.panel_visualizacion, 2)
        self.layout_h_inferior.addWidget(self.panel_actividad, 1)
        layout_v_contenido.addWidget(self.contenedor_inferior, 1)

        self.barra_estado = QFrame()
        self.barra_estado.setFixedHeight(25)
        self.barra_estado.setStyleSheet("background-color: #007acc; color: white; border-top: 1px solid #3e3e42;")
        layout_estado = QHBoxLayout(self.barra_estado)
        layout_estado.setContentsMargins(10, 0, 10, 0)
        self.lbl_estado_bd = QLabel("Base de Datos: SQLite Conectada")
        self.lbl_estado_bd.setStyleSheet("color: white; font-size: 11px;")
        self.lbl_memoria = QLabel("RAM Uso (UI): ~45MB")
        self.lbl_memoria.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        layout_estado.addWidget(self.lbl_estado_bd)
        layout_estado.addStretch()
        layout_estado.addWidget(self.lbl_memoria)
        layout_v_contenido.addWidget(self.barra_estado)

        self.layout_principal.addWidget(widget_contenido)

    # --- LÓGICA IA (AGREGADA) ---
    def procesar_ia(self):
        texto = self.entrada_ia.text().strip()
        if not texto: return
        nombre = self.ia.extraer_nombre_especifico(texto)
        if not nombre:
            nombre = self.ia.predecir_categoria(texto)
            tipo = "Categoría Detectada"
        else:
            tipo = "Nombre Manual"
        try:
            if not os.path.exists(nombre):
                os.makedirs(nombre)
                msg = f"Carpeta '{nombre}' creada."
            else:
                msg = f"Carpeta '{nombre}' ya existe."
            self.toast = NotificacionToast(msg, self)
            self.toast.mostrar(self.mapToGlobal(QSize(250, 500).toPoint()))
            self.añadir_item_actividad(f"📂 {nombre}", tipo, "Ahora")
            self.entrada_ia.clear()
        except Exception as e:
            print(f"Error: {e}")

    def añadir_item_actividad(self, archivo, accion, tiempo):
        item = QFrame()
        item.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 8px; border: 1px solid #2d2d30;")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(5, 2, 5, 2)
        icono = QLabel("✅")
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
        layout.addWidget(lbl_accion, 1)
        layout.addWidget(lbl_tiempo)
        self.layout_lista.insertWidget(0, item) # Insertar arriba

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9)) 
    ventana = DashboardOrganizador()
    ventana.show()
    sys.exit(app.exec())