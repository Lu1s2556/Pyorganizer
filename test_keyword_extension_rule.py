import os
import tempfile
from pathlib import Path

from app.core.motor_organizador import MotorOrganizadorCore
from app.modelo.base_de_datos import inicializar_nueva_db


def test_keyword_extension_rule():
    db_path = Path(tempfile.mkdtemp()) / 'test_rules.db'
    os.environ['PYORGANIZER_TEST_DB'] = str(db_path)

    # Inicializa DB en ruta temporal
    try:
        inicializar_nueva_db(str(db_path))
    except TypeError:
        # si inicializar_nueva_db no acepta ruta, copiar la base de datos generada
        inicializar_nueva_db()

    # Preparar reglas
    from app.modelo.base_de_datos import GestorBaseDatos
    db = GestorBaseDatos(str(db_path))
    db.db.cursor.execute("DELETE FROM reglas_organizacion")
    db.db.cursor.execute("DELETE FROM directorios_destino")
    db.db.cursor.execute("DELETE FROM carpetas_monitoreadas")
    db.db.confirmar()

    db.db.cursor.execute("INSERT INTO directorios_destino (ruta, nombre_alias) VALUES (?, ?)", (str(Path(tempfile.mkdtemp())), 'destino_importante'))
    db.db.cursor.execute(
        "INSERT INTO reglas_organizacion (nombre, extension, palabras_clave, carpeta_destino, activa) VALUES (?, ?, ?, ?, ?)",
        ('Importante PDF', '.pdf', 'importante', 'destino_importante', 1)
    )
    db.db.confirmar()

    # Crear archivos falsos
    base_dir = Path(tempfile.mkdtemp())
    archivo_correcto = base_dir / 'reporte_importante.pdf'
    archivo_incorrecto = base_dir / 'documento_basura.pdf'
    archivo_correcto.write_text('dummy')
    archivo_incorrecto.write_text('dummy')

    # Ejecutar motor con configuración manual
    motor = MotorOrganizadorCore(str(db_path))
    destinos = {'destino_importante': Path(db.db.cursor.execute("SELECT ruta FROM directorios_destino WHERE nombre_alias = ?", ('destino_importante',)).fetchone()[0])}
    reglas = [{'id': 1, 'extensions': ['.pdf'], 'keywords': ['importante'], 'destino_alias': 'destino_importante', 'nombre_regla': 'Importante PDF'}]

    aplicado_correcto = motor._evaluar_regla_para_archivo('.pdf', archivo_correcto.name.lower(), ['.pdf'], ['importante'])
    aplicado_incorrecto = motor._evaluar_regla_para_archivo('.pdf', archivo_incorrecto.name.lower(), ['.pdf'], ['importante'])

    print('reporte_importante.pdf aplicable:', aplicado_correcto)
    print('documento_basura.pdf aplicable:', aplicado_incorrecto)

    assert aplicado_correcto is True
    assert aplicado_incorrecto is False


if __name__ == '__main__':
    test_keyword_extension_rule()
    print('Test completado satisfactoriamente.')
