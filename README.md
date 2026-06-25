# PyOrganizer

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)
![Framework](https://img.shields.io/badge/PySide6-GUI-green)
![AI/ML](https://img.shields.io/badge/fastText-orange)

**PyOrganizer** (también conocido como VigiData) es un bot inteligente de escritorio diseñado para monitorear, clasificar y organizar archivos de forma automática. Integra modelos de Machine Learning y procesamiento de lenguaje natural (NLP) para tomar decisiones inteligentes sobre la ubicación de los archivos.

##  Características Principales

*   **Organización Inteligente:** Uso de IA (scikit-learn, fastText, nltk) para clasificar y organizar archivos según su contenido y metadatos.
*   **Monitoreo en Tiempo Real:** Utiliza `watchdog` para detectar cambios en los directorios mediante hilos en segundo plano (`WatcherThread`), asegurando un rendimiento óptimo de la interfaz.
*   **Interfaz Gráfica Moderna:** Desarrollada con `PySide6` (Qt), proporcionando una experiencia de usuario fluida y multiplataforma.
*   **Arquitectura Escalable:** Implementación estricta del patrón de diseño **MVC** (Modelo-Vista-Controlador).
*   **Eficiencia de Recursos:** Carga perezosa (Lazy Loading) de módulos pesados, optimizado para entornos de recursos limitados (8GB RAM).
*   **Persistencia:** Base de datos local SQLite para reglas y configuraciones.

##  Stack Tecnológico

*   **Lenguaje:** Python 3.12+
*   **Gestor de Dependencias:** Poetry
*   **GUI:** PySide6
*   **Machine Learning / NLP:** scikit-learn, nltk, textblob, fasttext
*   **Sistema de Archivos:** watchdog, psutil

##  Arquitectura del Proyecto

El proyecto está estructurado utilizando el patrón **Modelo-Vista-Controlador (MVC)** para separar la lógica de negocio de la interfaz de usuario:

```text
Pyorganizer/
├── app/
│   ├── controlador/   # Lógica que conecta Vista y Modelo (ej. watcher_thread.py)
│   ├── modelo/        # Interacción con la base de datos y procesamiento AI
│   ├── vista/         # Interfaces gráficas (DashboardOrganizador)
│   ├── core/          # Lógica central del negocio
│   ├── recursos/      # Assets y bases de datos (SQLite)
│   └── utiles/        # Funciones auxiliares genéricas
├── main.py            # Punto de entrada de la aplicación
└── pyproject.toml     # Configuración de dependencias (Poetry)
```

##  Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Lu1s2556/Pyorganizer.git
   cd Pyorganizer
   ```

2. **Instalar dependencias con Poetry:**
   ```bash
   poetry install
   ```

3. **Ejecutar la aplicación:**
   ```bash
   poetry run python main.py
   ```

##  Autor

**Luis Rojas** - [luiserojasp06@gmail.com](mailto:luiserojasp06@gmail.com)
