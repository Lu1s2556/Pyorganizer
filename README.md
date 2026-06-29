<div align="center">
  <img src="logo.png" alt="PyOrganizer Logo" width="200"/>

  # PyOrganizer
  
  ![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python&logoColor=white)
  ![Framework](https://img.shields.io/badge/PySide6-GUI-green?style=for-the-badge&logo=qt&logoColor=white)
  ![AI/ML](https://img.shields.io/badge/fastText-Machine_Learning-orange?style=for-the-badge)

  *Tu bot inteligente de escritorio para monitoreo, clasificación y organización automática de archivos.*
</div>

---

**PyOrganizer** (también conocido como VigiData) es una aplicación avanzada diseñada para mantener tus archivos siempre organizados. Integra modelos de **Machine Learning** y procesamiento de lenguaje natural (NLP) para tomar decisiones inteligentes sobre dónde ubicar cada archivo, aprendiendo de tu entorno.

## ✨ Novedades y Actualizaciones Recientes

* 🖼️ **Nueva Identidad Visual:** Incorporación del logotipo oficial y mejoras gráficas.
* 📊 **Nuevo Dashboard y Pantallas:** Gráficos de estadísticas actualizados e interfaz más completa para el monitoreo de tus archivos.
* 🧠 **FastText Potenciado:** Entrenamiento del modelo FastText mucho más completo, garantizando mayor precisión en la clasificación con **mejoras en la optimización de uso de memoria**.
* ⚙️ **Configuración Avanzada:** Nuevo control de frecuencia de escaneo (1, 5, 15, 30, 60 min) directamente desde la interfaz gráfica.

## 🚀 Características Principales

*   🤖 **Organización Inteligente:** Uso de IA (scikit-learn, fastText, nltk) para clasificar y organizar archivos según su contenido y metadatos.
*   ⚡ **Monitoreo en Tiempo Real:** Utiliza `watchdog` para detectar cambios en los directorios mediante hilos en segundo plano (`WatcherThread`), asegurando un rendimiento óptimo sin congelar la interfaz.
*   🎨 **Interfaz Gráfica Moderna:** Desarrollada con `PySide6` (Qt), proporcionando una experiencia de usuario fluida, atractiva y multiplataforma.
*   🏗️ **Arquitectura Escalable:** Implementación estricta del patrón de diseño **MVC** (Modelo-Vista-Controlador).
*   📉 **Eficiencia de Recursos:** Carga perezosa (Lazy Loading) de módulos pesados, optimizado para entornos de recursos limitados (ideal para equipos de 8GB RAM o menos).
*   💾 **Persistencia de Datos:** Base de datos local SQLite robusta para el almacenamiento seguro de reglas, configuraciones e historial.

## 🛠️ Stack Tecnológico

*   **Lenguaje:** Python 3.12+
*   **Gestor de Dependencias:** Poetry
*   **GUI (Interfaz de Usuario):** PySide6
*   **Machine Learning / NLP:** scikit-learn, nltk, textblob, fasttext
*   **Sistema de Archivos y SO:** watchdog, psutil

## 📁 Arquitectura del Proyecto

El proyecto está estructurado utilizando el patrón **Modelo-Vista-Controlador (MVC)** para separar de forma limpia la lógica de negocio de la interfaz de usuario:

```text
Pyorganizer/
├── app/
│   ├── controlador/   # Lógica que conecta Vista y Modelo (ej. watcher_thread.py)
│   ├── modelo/        # Interacción con la base de datos y procesamiento AI
│   ├── vista/         # Interfaces gráficas (Dashboards, Vistas de Configuración)
│   ├── core/          # Lógica central del negocio y algoritmos de clasificación
│   ├── recursos/      # Assets, imágenes (logo) y bases de datos (SQLite)
│   └── utiles/        # Funciones auxiliares genéricas
├── main.py            # Punto de entrada de la aplicación
└── pyproject.toml     # Configuración de dependencias (Poetry)
```

## ⚙️ Instalación y Uso

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

## 👨‍💻 Autor

**Luis Rojas** - [luiserojasp06@gmail.com](mailto:luiserojasp06@gmail.com)
