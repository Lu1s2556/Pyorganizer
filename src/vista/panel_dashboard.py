# vista/panel_dashboard.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QGridLayout, QSizePolicy)
from PySide6.QtGui import QFont, QColor, QLinearGradient, QGradient, QPainter
from PySide6.QtCore import Qt, QSize
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QAreaSeries, QPieSeries, QPieSlice
import random
from datetime import datetime, timedelta

class DashboardPanel(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz del dashboard"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título principal
        title_layout = QHBoxLayout()
        title_label = QLabel("Visión General del Sistema")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet("color: #1a1a1a;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Tarjetas de estadísticas
        stats_cards = self.create_stats_cards()
        main_layout.addLayout(stats_cards)
        
        # Gráficos
        charts_layout = QHBoxLayout()
        
        # Gráfico de área
        area_chart = self.create_area_chart()
        charts_layout.addWidget(area_chart, 60)  # 60% del ancho
        
        # Gráfico de pastel
        pie_chart = self.create_pie_chart()
        charts_layout.addWidget(pie_chart, 40)  # 40% del ancho
        
        main_layout.addLayout(charts_layout)
        
        # Actividad reciente
        recent_activity = self.create_recent_activity()
        main_layout.addWidget(recent_activity)
        
    def create_stats_cards(self):
        """Crear tarjetas de estadísticas"""
        layout = QGridLayout()
        layout.setSpacing(15)
        
        stats_data = [
            {"title": "Archivos Organizados", "value": "80", "icon": "✓", "trend": "+4 hoy", "color": "#10b981"},
            {"title": "Almacenamiento Gestionado", "value": "392.53 MB", "icon": "💾", "trend": "Volumen total", "color": "#3b82f6"},
            {"title": "Reglas Activas", "value": "11/12", "icon": "⚙️", "trend": "Reglas ejecutándose", "color": "#f59e0b"},
            {"title": "Duplicados Evitados", "value": "6", "icon": "🚫", "trend": "Espacio ahorrado", "color": "#ef4444"}
        ]
        
        for i, stat in enumerate(stats_data):
            card = self.create_stat_card(stat)
            layout.addWidget(card, i // 2, i % 2)
            
        return layout
    
    def create_stat_card(self, data):
        """Crear una tarjeta de estadística individual"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                padding: 20px;
            }}
        """)
        card.setMinimumHeight(120)
        
        layout = QVBoxLayout(card)
        
        # Header de la tarjeta
        header_layout = QHBoxLayout()
        title_label = QLabel(data["title"])
        title_label.setStyleSheet("font-size: 14px; color: #6b7280; font-weight: 500;")
        header_layout.addWidget(title_label)
        
        icon_label = QLabel(data["icon"])
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Valor principal
        value_label = QLabel(data["value"])
        value_label.setStyleSheet(f"""
            font-size: 24px; 
            font-weight: bold; 
            color: {data['color']};
            margin: 5px 0;
        """)
        layout.addWidget(value_label)
        
        # Trend
        trend_label = QLabel(data["trend"])
        trend_label.setStyleSheet("font-size: 12px; color: #9ca3af;")
        layout.addWidget(trend_label)
        
        return card
    
    def create_area_chart(self):
        """Crear gráfico de área de actividad"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        layout = QVBoxLayout(container)
        
        # Título del gráfico
        title_label = QLabel("Actividad Últimos 30 Días")
        title_label.setStyleSheet("font-size: 14px; font-weight: 500; padding: 15px 15px 0 15px;")
        layout.addWidget(title_label)
        
        # Gráfico
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setTitle("")
        chart.legend().hide()
        
        # Crear datos de ejemplo (últimos 30 días)
        series = QLineSeries()
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            value = random.randint(0, 8)  # Valores aleatorios para el ejemplo
            series.append(i, value)
        
        # Crear área series
        area_series = QAreaSeries(series)
        area_series.setColor(QColor("#3b82f6"))
        area_series.setOpacity(0.3)
        
        chart.addSeries(area_series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setMinimumHeight(300)
        
        layout.addWidget(chart_view)
        
        return container
    
    def create_pie_chart(self):
        """Crear gráfico de pastel de categorías"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        layout = QVBoxLayout(container)
        
        # Título del gráfico
        title_label = QLabel("Distribución por Categorías")
        title_label.setStyleSheet("font-size: 14px; font-weight: 500; padding: 15px 15px 0 15px;")
        layout.addWidget(title_label)
        
        # Gráfico de pastel
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setTitle("")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        series = QPieSeries()
        
        categories = [
            {"name": "Videos", "value": 15, "color": "#a855f7"},
            {"name": "Audio", "value": 10, "color": "#f59e0b"},
            {"name": "Imágenes", "value": 25, "color": "#22d3ee"},
            {"name": "Código", "value": 20, "color": "#3b82f6"},
            {"name": "Hojas de cálculo", "value": 12, "color": "#84cc16"},
            {"name": "Archivos", "value": 8, "color": "#10b981"},
            {"name": "Documentos", "value": 10, "color": "#6366f1"}
        ]
        
        for category in categories:
            slice = series.append(category["name"], category["value"])
            slice.setColor(QColor(category["color"]))
            slice.setLabelVisible(True)
        
        chart.addSeries(series)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setMinimumHeight(300)
        
        layout.addWidget(chart_view)
        
        return container
    
    def create_recent_activity(self):
        """Crear sección de actividad reciente"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        layout = QVBoxLayout(container)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Actividad Reciente")
        title_label.setStyleSheet("font-size: 16px; font-weight: 500;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Lista de actividades
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_area.setWidgetResizable(True)
        
        activities_widget = QWidget()
        activities_layout = QVBoxLayout(activities_widget)
        activities_layout.setSpacing(10)
        
        activities_data = [
            {"type": "file_moved", "description": "9 imágenes organizadas a Medios/Imágenes", "details": "Tamaño total: 12.4 MB", "time": "hace 5 horas"},
            {"type": "file_moved", "description": "4 scripts Python organizados a Código/Python", "details": "Tamaño total: 48 KB", "time": "hace 1 día"},
            {"type": "file_moved", "description": "6 archivos de audio organizados a Medios/Audio", "details": "Tamaño total: 34 MB", "time": "hace 3 días"},
            {"type": "file_moved", "description": "15 documentos organizados a Documentos/", "details": "Tamaño total: 5.1 MB", "time": "hace 7 días"},
            {"type": "rule_created", "description": 'Regla "Audio MP3" creada', "details": "Patrón: .mp3, Categoría: Audio", "time": "hace 10 días"}
        ]
        
        for activity in activities_data:
            activity_widget = self.create_activity_item(activity)
            activities_layout.addWidget(activity_widget)
        
        activities_layout.addStretch()
        scroll_area.setWidget(activities_widget)
        layout.addWidget(scroll_area)
        
        return container
    
    def create_activity_item(self, activity):
        """Crear elemento de actividad individual"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        layout = QHBoxLayout(item)
        
        # Badge de tipo
        badge = QLabel(activity["type"].replace("_", " ").title())
        badge.setStyleSheet("""
            QLabel {
                background-color: #e5e7eb;
                color: #374151;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        badge.setFixedHeight(20)
        layout.addWidget(badge)
        
        # Descripción
        desc_layout = QVBoxLayout()
        desc_label = QLabel(activity["description"])
        desc_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        desc_layout.addWidget(desc_label)
        
        details_label = QLabel(activity["details"])
        details_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        desc_layout.addWidget(details_label)
        
        layout.addLayout(desc_layout, 70)
        
        # Tiempo
        time_label = QLabel(activity["time"])
        time_label.setStyleSheet("font-size: 12px; color: #9ca3af;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(time_label, 30)
        
        return item

# Ejemplo de uso en el controlador principal
# En controlador_principal.py podrías integrarlo así:

class ControladorPrincipal:
    def __init__(self):
        # ... código existente ...
        self.setup_dashboard()
    
    def setup_dashboard(self):
        """Configurar el dashboard"""
        from vista.panel_dashboard import DashboardPanel
        self.dashboard_panel = DashboardPanel(self)
        # Agregar este panel a tu interfaz principal
