from vista.panel_dashboard import DashboardPanel

class ControladorPrincipal:
    def __init__(self):
        self.inicializar_paneles()

    def inicializar_paneles(self):
        """Inicializar todos los paneles"""
        self.paneles = {"dashboard": DashboardPanel(self)}

    def mostrar_panel(self,nombre_panel):
        """mostrar panel especifico"""
        panel = self.paneles.get(nombre_panel)
        if panel:
            self.limpiar_area_principal()
            self.area_principal_layout.addWidget(panel)
            panel.setVisible        