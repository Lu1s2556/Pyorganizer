#!/usr/bin/env python3
"""Entrena un modelo FastText supervisado a partir de app/recursos/entrenamiento.txt
Guarda el binario en app/recursos/modelo_asistente.bin por defecto.
"""
import argparse
import os
import sys
import fasttext


def main():
    parser = argparse.ArgumentParser(description="Entrena y guarda el modelo FastText para el asistente")
    parser.add_argument('--input', '-i', default=os.path.join('app', 'recursos', 'entrenamiento.txt'), help='Archivo de entrenamiento (formato FastText)')
    parser.add_argument('--output', '-o', default=os.path.join('app', 'recursos', 'modelo_asistente.bin'), help='Ruta de salida para el modelo .bin')
    parser.add_argument('--epoch', type=int, default=25)
    parser.add_argument('--lr', type=float, default=0.5)
    parser.add_argument('--wordNgrams', type=int, default=2)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: archivo de entrenamiento no encontrado: {args.input}")
        sys.exit(2)

    print(f"Entrenando modelo con: input={args.input}, epoch={args.epoch}, lr={args.lr}, wordNgrams={args.wordNgrams}")

    model = fasttext.train_supervised(input=args.input, epoch=args.epoch, lr=args.lr, wordNgrams=args.wordNgrams)

    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    model.save_model(args.output)
    print(f"✅ Modelo guardado en: {args.output}")


if __name__ == '__main__':
    main()
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
