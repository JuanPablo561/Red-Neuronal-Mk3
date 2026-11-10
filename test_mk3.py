import io
import unittest
from PIL import Image

from modelo import seleccionar_detecciones
from servidor import crear_app


class Mk3Tests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def detectar(imagen, umbral):
            self.calls.append((imagen.size, umbral))
            return [dict(clase='Camisa', puntuacion=0.8, caja=[0.1, 0.2, 0.5, 0.7])]
        self.app = crear_app(detectar)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def imagen(self):
        archivo = io.BytesIO()
        Image.new('RGB', (200, 100), 'white').save(archivo, 'PNG')
        archivo.seek(0)
        return archivo

    def test_foto_devuelve_cajas_y_conserva_proporcion(self):
        r = self.client.post('/predecir', data={'imagen': (self.imagen(), 'foto.png'), 'umbral': '0.2'})
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual((d['ancho'], d['alto']), (200, 100))
        self.assertEqual(d['detecciones'][0]['caja'], [0.1, 0.2, 0.5, 0.7])
        self.assertTrue(d['vista'].startswith('data:image/jpeg;base64,'))
        self.assertEqual(self.calls, [((200, 100), 0.2)])

    def test_rechaza_archivo_invalido_y_umbral_no_finito(self):
        self.assertEqual(self.client.post('/predecir').status_code, 400)
        r = self.client.post('/predecir', data={'imagen': (io.BytesIO(b'no imagen'), 'x.jpg')})
        self.assertEqual(r.status_code, 400)
        for umbral in ['nan', 'inf', '0', '1.1', 'texto']:
            r = self.client.post('/predecir', data={'imagen': (self.imagen(), 'x.png'), 'umbral': umbral})
            self.assertEqual(r.status_code, 400, umbral)
        self.assertEqual(self.calls, [])

    def test_limite_de_archivo(self):
        self.app.config['MAX_CONTENT_LENGTH'] = 128
        r = self.client.post('/predecir', data={'imagen': (io.BytesIO(b'x' * 200), 'x.png')})
        self.assertEqual(r.status_code, 413)
        self.assertIn('error', r.get_json())

    def test_sin_detecciones_es_un_resultado_valido(self):
        client = crear_app(lambda imagen, umbral: []).test_client()
        r = client.post('/predecir', data={'imagen': (self.imagen(), 'x.png')})
        self.assertEqual(r.get_json()['detecciones'], [])

    def test_suprime_duplicados_recorta_cajas_y_conserva_otras_prendas(self):
        d = seleccionar_detecciones(
            [[-10, 0, 110, 50], [0, 0, 100, 50], [100, 60, 200, 100], [5, 5, 5, 10]],
            [0.9, 0.8, 0.7, 0.95], [0, 1, 2, 0], (200, 100),
        )
        self.assertEqual(len(d), 2)
        self.assertEqual(d[0]['caja'], [0.0, 0.0, 0.55, 0.5])
        self.assertEqual(d[1]['caja'], [0.5, 0.6, 1.0, 1.0])


if __name__ == '__main__':
    unittest.main()
