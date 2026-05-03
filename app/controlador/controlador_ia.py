import os

class ControladorInteligente:
    def __init__(self, modelo_ia):
        self.ia = modelo_ia

    def crear_repositorio_inteligente(self, ruta_base, descripcion_usuario):
        """
        Ejemplo: ruta_base="C:/Descargas", descripcion="guardar mis fotos"
        """
        try:
            # 1. Preguntar a la IA qué quiere el usuario
            categoria = self.ia.predecir_categoria(descripcion_usuario)
            
            # 2. Definir la ruta de la nueva carpeta
            ruta_final = os.path.join(ruta_base, categoria)
            
            # 3. Crear la carpeta si no existe
            if not os.path.exists(ruta_final):
                os.makedirs(ruta_final)
                return f"✅ IA: He detectado '{categoria}'. Carpeta creada en: {ruta_final}"
            else:
                return f"ℹ️ La carpeta de '{categoria}' ya existe."
                
        except Exception as e:
            return f"❌ Error al crear carpeta: {str(e)}"