"""Prueba real del modelo y la API: python verificar.py /ruta/a/foto.jpg."""
import json
from pathlib import Path
import sys

from modelo import Detector
from servidor import crear_app


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python verificar.py /ruta/a/foto.jpg')
    ruta = Path(sys.argv[1])
    with ruta.open('rb') as archivo:
        respuesta = crear_app(Detector()).test_client().post(
            '/predecir', data={'imagen': (archivo, ruta.name)},
        )
    datos = respuesta.get_json()
    if respuesta.status_code != 200:
        raise SystemExit(datos)
    for d in datos['detecciones']:
        x1, y1, x2, y2 = d['caja']
        assert 0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1, d
        assert 0 <= d['puntuacion'] <= 1, d
    del datos['vista']
    print(json.dumps(datos, ensure_ascii=False, indent=2))
    print('Prueba real terminada. Un resultado vacío también puede ser válido.')


if __name__ == '__main__':
    main()
