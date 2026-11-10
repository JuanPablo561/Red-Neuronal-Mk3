"""Aplicación local: python servidor.py → http://127.0.0.1:8000."""
import base64
import io
import math
from pathlib import Path
import time
import warnings

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageOps, UnidentifiedImageError

CARPETA = Path(__file__).parent
MAX_PIXELES = 20_000_000


def crear_app(detector):
    app = Flask(__name__, static_folder='static')
    app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

    @app.errorhandler(413)
    def demasiado_grande(_):
        return jsonify(error='La imagen supera el máximo de 15 MB.'), 413

    @app.get('/')
    def inicio():
        return send_from_directory(CARPETA, 'index.html')

    @app.post('/predecir')
    def predecir():
        archivo = request.files.get('imagen')
        if archivo is None:
            return jsonify(error='Selecciona una imagen.'), 400
        try:
            umbral = float(request.form.get('umbral', '0.15'))
            if not math.isfinite(umbral) or not 0.01 <= umbral <= 0.9:
                raise ValueError
        except ValueError:
            return jsonify(error='El umbral debe estar entre 0.01 y 0.9.'), 400
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(archivo.stream) as original:
                    if original.format not in {'JPEG', 'PNG', 'WEBP'}:
                        return jsonify(error='Usa una imagen JPEG, PNG o WebP.'), 400
                    if original.width * original.height > MAX_PIXELES:
                        return jsonify(error='La imagen supera los 20 megapíxeles.'), 400
                    imagen = ImageOps.exif_transpose(original).convert('RGB')
        except (UnidentifiedImageError, OSError, ValueError,
                Image.DecompressionBombError, Image.DecompressionBombWarning):
            return jsonify(error='No se pudo leer la imagen o sus dimensiones son excesivas.'), 400
        # Conserva proporción y limita el trabajo de preprocesamiento.
        imagen.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        inicio = time.perf_counter()
        try:
            detecciones = detector(imagen, umbral)
        except Exception:
            app.logger.exception('Falló la detección')
            return jsonify(error='No se pudo analizar la foto. Revisa la terminal e inténtalo de nuevo.'), 500
        buffer = io.BytesIO()
        imagen.save(buffer, 'JPEG', quality=90)
        return jsonify(
            detecciones=detecciones, ancho=imagen.width, alto=imagen.height,
            segundos=round(time.perf_counter() - inicio, 2),
            vista='data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode(),
        )

    return app


if __name__ == '__main__':
    from modelo import Detector
    print('Cargando OWL-ViT. La primera ejecución descarga los pesos del modelo…')
    app = crear_app(Detector())
    app.run(host='127.0.0.1', port=8000, debug=False)
