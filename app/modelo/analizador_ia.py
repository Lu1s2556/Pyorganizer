from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

class ClasificadorIA:
    def __init__(self):
        # Convertimos texto a números (Vectores)
        self.vectorizador = CountVectorizer()
        self.modelo = MultinomialNB()
        self.categorias = {
            "Documentos": ["pdf", "docx", "txt", "tareas", "informes", "escritos"],
            "Imagenes": ["fotos", "capturas", "dibujos", "png", "jpg", "imagenes"],
            "Videos": ["peliculas", "grabaciones", "mp4", "videos", "clips"],
            "Codigo": ["python", "scripts", "programas", "html", "codigo"]
        }
        self._entrenar()

    def _entrenar(self):
        # Datos de entrenamiento simples
        textos = []
        etiquetas = []
        for categoria, palabras in self.categorias.items():
            for palabra in palabras:
                textos.append(palabra)
                etiquetas.append(categoria)
        
        X = self.vectorizador.fit_transform(textos)
        self.modelo.fit(X, etiquetas)

    def predecir_categoria(self, descripcion_usuario):
        # La IA analiza la frase del usuario
        X_nuevo = self.vectorizador.transform([descripcion_usuario.lower()])
        prediccion = self.modelo.predict(X_nuevo)
        return prediccion[0]