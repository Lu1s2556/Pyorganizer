import sys
from  import QApplication
from controlador.ControladorPrincipal import ControladorPrincipal

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    controlador = ControladorPrincipal
    controlador.ejecutar()

    sys.exit(app.exec())

if __name__ == "__main__" :
    main()