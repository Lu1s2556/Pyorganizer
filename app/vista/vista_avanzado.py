from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
from PySide6.QtCore import Qt
import os
import shutil

class VistaAvanzado(QWidget):
    def __init__(self, asistente, callback_regresar, parent=None):
        super().__init__(parent)
        self.asistente = asistente
        self.callback_regresar = callback_regresar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        tit = QLabel("Opciones Avanzadas")
        tit.setStyleSheet("color: white; font-size: 28px; font-weight: 800;")
        layout.addWidget(tit)

        # ponytail: simplified layout for requested parameters
        
        # 1. Frecuencia de escaneo
        lbl_intervalo = QLabel("Frecuencia de Escaneo:")
        lbl_intervalo.setStyleSheet("color: #a1a1aa; font-size: 14px;")
        layout.addWidget(lbl_intervalo)

        self.combo_intervalo = QComboBox()
        self.combo_intervalo.addItems(["1 min", "5 min", "15 min", "30 min", "60 min"])
        self.combo_intervalo.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); color: white; padding: 10px;")
        self.combo_intervalo.setFixedWidth(150)
        
        try:
            val = int(self.asistente.modelo_org.gestor.obtener_configuracion("intervalo_escaneo_min", 5) or 5)
            idx = self.combo_intervalo.findText(f"{val} min")
            if idx >= 0: self.combo_intervalo.setCurrentIndex(idx)
        except Exception: pass
        
        self.combo_intervalo.currentIndexChanged.connect(self.guardar_intervalo)
        layout.addWidget(self.combo_intervalo)

        layout.addSpacing(20)

        # 2. Limpiar TEMP
        btn_temp = QPushButton("🧹 Limpiar Caché de Windows (%TEMP%)")
        btn_temp.setFixedWidth(300)
        btn_temp.setStyleSheet("QPushButton { background: rgba(239, 68, 68, 0.15); color: #ef4444; font-weight: bold; padding: 12px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3); } QPushButton:hover { background: rgba(239, 68, 68, 0.25); }")
        btn_temp.clicked.connect(self.limpiar_temp)
        layout.addWidget(btn_temp)

        layout.addStretch()

        btn_volver = QPushButton("← VOLVER AL PANEL RESUMEN")
        btn_volver.setFixedWidth(300)
        btn_volver.setStyleSheet("QPushButton { background: rgba(255, 255, 255, 0.05); color: #a1a1aa; font-weight: bold; padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); } QPushButton:hover { background: rgba(255, 255, 255, 0.1); color: white; }")
        btn_volver.clicked.connect(self.callback_regresar)
        layout.addWidget(btn_volver, alignment=Qt.AlignLeft)

    def guardar_intervalo(self, index):
        val_str = self.combo_intervalo.currentText().split()[0]
        try:
            self.asistente.modelo_org.gestor.guardar_configuracion("intervalo_escaneo_min", val_str)
            QMessageBox.information(self, "Guardado", "Reinicia la app para aplicar el intervalo.")
        except Exception: pass

    def limpiar_temp(self):
        # ponytail: minimal temp clearing. Standard library os and shutil.
        temp_dir = os.environ.get('TEMP')
        if not temp_dir or not os.path.exists(temp_dir):
            return
        
        borrados = 0
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                borrados += 1
            except Exception:
                pass # Archivos en uso, ignorar
        
        QMessageBox.information(self, "Caché Limpia", f"Se limpiaron {borrados} elementos temporales (algunos archivos en uso se omitieron).")
