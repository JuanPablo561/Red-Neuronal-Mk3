"""Detección de prendas por texto con OWL-ViT; no clasifica la foto completa."""
from pathlib import Path
import threading

import torch
from torchvision.ops import nms
from transformers import OwlViTForObjectDetection, OwlViTProcessor

MODELO_ID = 'google/owlvit-base-patch32'
REVISION = 'cbc355fb364588351c5d51c7f74465e8e7ec6f72'
CACHE = Path(__file__).parent / '.modelos'
# Una consulta por categoría; el índice enlaza etiquetas y resultados.
CLASES = [
    ('Camiseta', 'a photo of a t-shirt'),
    ('Camisa', 'a photo of a buttoned shirt'),
    ('Pantalón', 'a photo of pants'),
    ('Shorts', 'a photo of shorts'),
    ('Vestido', 'a photo of a dress'),
    ('Falda', 'a photo of a skirt'),
    ('Abrigo / chaqueta', 'a photo of a coat or jacket'),
    ('Suéter', 'a photo of a sweater'),
    ('Zapato', 'a photo of a shoe'),
    ('Sombrero / gorra', 'a photo of a hat'),
    ('Bolso', 'a photo of a handbag'),
]


def seleccionar_detecciones(cajas, puntuaciones, etiquetas, tamano):
    """Normaliza xyxy a [0,1] y elimina cajas degeneradas y duplicadas."""
    ancho, alto = tamano
    cajas = torch.as_tensor(cajas, dtype=torch.float32).reshape(-1, 4).clone()
    scores = torch.as_tensor(puntuaciones, dtype=torch.float32)
    labels = torch.as_tensor(etiquetas, dtype=torch.long)
    cajas[:, [0, 2]] = cajas[:, [0, 2]].clamp(0, ancho)
    cajas[:, [1, 3]] = cajas[:, [1, 3]].clamp(0, alto)
    validas = (cajas[:, 2] > cajas[:, 0]) & (cajas[:, 3] > cajas[:, 1])
    cajas, scores, labels = cajas[validas], scores[validas], labels[validas]
    # ponytail: NMS entre clases puede ocultar prendas muy superpuestas;
    # evaluar NMS por clase cuando haya un conjunto anotado de escenas reales.
    indices = nms(cajas, scores, iou_threshold=0.65)[:40]
    escala = torch.tensor([ancho, alto, ancho, alto])
    return [
        {'clase': CLASES[int(labels[i])][0],
         'puntuacion': round(float(scores[i]), 4),
         'caja': [round(v, 5) for v in (cajas[i] / escala).tolist()]}
        for i in indices
    ]


class Detector:
    def __init__(self):
        opciones = dict(revision=REVISION, cache_dir=str(CACHE))
        self.procesador = OwlViTProcessor.from_pretrained(MODELO_ID, **opciones)
        self.dispositivo = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.modelo = OwlViTForObjectDetection.from_pretrained(
            MODELO_ID, use_safetensors=True, **opciones,
        ).to(self.dispositivo).eval()
        self.lock = threading.Lock()

    def __call__(self, imagen, umbral):
        textos = [[texto for _, texto in CLASES]]
        # Una inferencia simultánea por proceso evita saturar memoria en CPU.
        with self.lock, torch.inference_mode():
            entradas = self.procesador(text=textos, images=imagen, return_tensors='pt')
            entradas = entradas.to(self.dispositivo)
            salidas = self.modelo(**entradas)
            resultado = self.procesador.post_process_grounded_object_detection(
                outputs=salidas, threshold=umbral, target_sizes=[(imagen.height, imagen.width)],
                text_labels=textos,
            )[0]
        return seleccionar_detecciones(
            resultado['boxes'].cpu(), resultado['scores'].cpu(),
            resultado['labels'].cpu(), imagen.size,
        )


if __name__ == '__main__':
    detector = Detector()
    print(f'Modelo listo en {detector.dispositivo}. Caché: {CACHE}')
