import fasttext
from pathlib import Path


def entrenar_modelo_ia():
    raiz = Path(__file__).resolve().parent.parent
    ruta_txt = raiz / 'app' / 'recursos' / 'entrenamiento.txt'
    ruta_bin = raiz / 'app' / 'recursos' / 'modelo_asistente.bin'
    
    print("🧠 Entrenando el cerebro de VigiData con FastText...")
    
    model = fasttext.train_supervised(
        input=str(ruta_txt),
        epoch=50,
        lr=0.5,
        wordNgrams=2,
        bucket=200000,
        dim=100,
        loss='ova'
    )
    
    model.save_model(str(ruta_bin))
    print("✅ ¡Modelo guardado con éxito en app/recursos/modelo_asistente.bin!")


if __name__ == "__main__":
    entrenar_modelo_ia()
