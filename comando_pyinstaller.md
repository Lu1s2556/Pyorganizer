# Comando de PyInstaller para Pyorganizer

Ejecuta este comando en la raíz del proyecto para generar el `.exe` con el ícono y los recursos empaquetados:

```bash
poetry run pyinstaller --noconfirm --onedir --windowed --icon "logo.ico" --name "Pyorganizer" --add-data "logo.ico;." --add-data "logo.png;." --add-data "app/recursos;app/recursos" "main.py"
```

El programa compilado quedará listo en la ruta `dist/Pyorganizer`.
