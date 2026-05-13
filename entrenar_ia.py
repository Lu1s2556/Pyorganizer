import fasttext
from pathlib import Path

proyecto_raiz = Path(__file__).resolve().parent
recursos_dir = proyecto_raiz / 'app' / 'recursos'
recursos_dir.mkdir(parents=True, exist_ok=True)

ruta_txt = recursos_dir / 'entrenamiento.txt'

ruta_modelo = recursos_dir / 'modelo_asistente.bin'

if ruta_txt.exists():
    print("Entrenando el modelo de PyOrganizer...")
    # Entrenamos el modelo (puedes ajustar el epoch para más precisión)
    try:
        model = fasttext.train_supervised(
            input=str(ruta_txt),
            epoch=50,
            lr=0.5,
            wordNgrams=2,
            verbose=2
        )
        model.save_model(str(ruta_modelo))
        print(f"✅ ¡Éxito! El archivo '{ruta_modelo.name}' ha sido creado en {recursos_dir}")
    except Exception as e:
        print(f"❌ Error al entrenar el modelo: {e}")
else:
    print(f"❌ Error: No encontré el archivo {ruta_txt}. Créalo primero con tus frases de ejemplo.")