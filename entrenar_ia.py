import fasttext
import os

# 1. Asegúrate de que la carpeta de recursos exista
if not os.path.exists('app/recursos'):
    os.makedirs('app/recursos')

# 2. Ruta de tu archivo de texto (el que tiene las etiquetas __label__)
ruta_txt = 'app/recursos/entrenamiento.txt'

if os.path.exists(ruta_txt):
    print("Entrenando el modelo de PyOrganizer...")
    # Entrenamos el modelo (puedes ajustar el epoch para más precisión)
    model = fasttext.train_supervised(input=ruta_txt, epoch=100, lr=0.5)
    
    # 3. Guardamos el archivo .bin
    model.save_model('app/recursos/modelo_asistente.bin')
    print("✅ ¡Éxito! El archivo 'modelo_asistente.bin' ha sido creado en app/recursos/")
else:
    print(f"❌ Error: No encontré el archivo {ruta_txt}. Créalo primero con tus frases de ejemplo.")