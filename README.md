# Red Neuronal Mk3 · Prendas en contexto

**Mk1: formas → Mk2: detalle → Mk3: localización de varias prendas.**

Mk3 recibe una foto, busca prendas y accesorios y dibuja un cuadro por detección. Puedes seleccionar un resultado para resaltarlo, cambiar el umbral y exportar las cajas a JSON. Funciona con fotos subidas o tomadas desde el selector de cámara de un móvil compatible.

Esta versión utiliza **OWL-ViT preentrenado**, un detector de vocabulario abierto que recibe consultas de texto. No reutiliza los pesos clasificadores de Mk2: clasificar una foto y localizar varios objetos son tareas diferentes. Es una base funcional para estudiar contexto mediante localización; todavía no interpreta relaciones entre personas y prendas ni recomienda combinaciones.

## Ejecutar

Recomendado: Python 3.11 o 3.12, entorno virtual y varios GB de RAM disponibles. La descarga del modelo ocupa aproximadamente 600 MB, además de las dependencias. No hace falta una API de pago ni una clave.

```bash
git clone https://github.com/JuanPablo561/Red-Neuronal-Mk3.git
cd Red-Neuronal-Mk3
python -m venv .venv
```

Activa el entorno:

```bash
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Para CPU en Linux o Windows, instala primero la variante de PyTorch para CPU:

```bash
python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-lock.txt
python servidor.py
```

En macOS usa `python -m pip install -r requirements-lock.txt` directamente. Para GPU instala la combinación compatible de PyTorch/torchvision siguiendo [PyTorch](https://pytorch.org/get-started/locally/) antes de las demás dependencias. Esta versión selecciona CUDA si está disponible y CPU en caso contrario.

Abre **http://127.0.0.1:8000**. El primer inicio descarga el modelo desde Hugging Face en `.modelos/`; los siguientes reutilizan esa caché. Mantén acceso a internet durante la descarga. También puedes prepararla antes con `python modelo.py`.

Si la CPU usa demasiados hilos, prueba `OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python servidor.py` en Linux/macOS. La latencia depende del equipo. La aplicación se sirve en el equipo local; el servidor de desarrollo no está preparado para exposición pública. La cámara de un teléfono solo funciona al abrir la página desde ese teléfono con el acceso y contexto seguro adecuados; no se publica automáticamente en la red.

## Uso y categorías

1. Selecciona una foto con una o varias prendas. Se analiza automáticamente.
2. Revisa los cuadros numerados y la lista de resultados. Puedes seleccionar cada resultado con teclado o ratón.
3. Ajusta la puntuación mínima y pulsa **Analizar imagen** para repetir.
4. Exporta el JSON si quieres conservar las anotaciones propuestas.

Consultas iniciales: camiseta, camisa, pantalón, shorts, vestido, falda, abrigo/chaqueta, suéter, zapato, sombrero/gorra y bolso. Se definen en `CLASES` de `modelo.py`, con etiquetas españolas y consultas inglesas para el detector. Cambiar las consultas no requiere entrenar, pero sí volver a evaluar la calidad de sus resultados.

## API

`POST /predecir`, formulario multipart:

- `imagen`: JPEG, PNG o WebP; hasta 15 MB y 20 megapíxeles.
- `umbral`: número entre `0.01` y `0.9`; por defecto `0.15`.

```bash
curl -F imagen=@foto.jpg -F umbral=0.2 http://127.0.0.1:8000/predecir
```

La respuesta contiene `detecciones`, `ancho`, `alto`, `segundos` y `vista` (JPEG en data URL). Cada detección incluye `clase`, `puntuacion` y `caja: [x_min, y_min, x_max, y_max]`, normalizada entre 0 y 1 respecto a `vista`. La imagen respeta la orientación EXIF y la proporción; se limita a 1600 px por lado antes de procesarla. OWL-ViT aplica después su propio preprocesamiento interno. La vista muestra la imagen de referencia para las cajas, no el tensor interno del modelo.

Las fotos se procesan en memoria en el servidor y no se guardan ni se envían a una API de inferencia. La descarga inicial de pesos sí requiere conectarse a Hugging Face. El navegador solo descarga anotaciones cuando se pulsa Exportar.

## Verificación

```bash
python -m unittest -v
python verificar.py /ruta/a/una/foto.jpg
```

La primera orden prueba límites de carga, archivos inválidos, umbrales, respuesta vacía y formato/filtrado de cajas. Usa un sustituto del detector para probar la API sin descargar pesos; el filtrado usa las operaciones reales de PyTorch. La segunda orden ejecuta el detector real y comprueba la API y las coordenadas con tu foto. Ninguna sustituye una evaluación de precisión con anotaciones humanas.

## Limitaciones y siguiente experimento

- Las puntuaciones **no son probabilidades calibradas de acierto**. Un umbral bajo produce más falsos positivos. No encontrar cuadros no demuestra que la foto no contenga ropa.
- El detector puede confundir categorías, duplicar objetos, ignorar prendas pequeñas u ocultas y depender del fondo. No hay una garantía de robustez frente a oclusiones.
- Se eliminan cajas casi idénticas con NMS entre categorías (IoU 0.65) y se muestran hasta 40. Esto reduce duplicados, pero puede descartar prendas muy superpuestas.
- El modelo aún no se ha afinado con un dataset de detección de ropa propio. No se atribuye una precisión global a esta versión.

El siguiente paso medible es anotar escenas reales con **clase y caja por prenda**, separar entrenamiento/validación/prueba por escena o sesión y evaluar precisión/recobrado y mAP por clase. Comparar prendas aisladas frente a varias prendas, fondos complejos y oclusiones. Ajustar consultas y umbral solo con validación; conservar prueba para la evaluación final. Después decidir, con esos resultados, si conviene afinar un detector especializado.

## Archivos y fuentes

- `modelo.py`: consultas, carga del detector y filtrado de cajas.
- `servidor.py`: validación de imágenes y API Flask.
- `index.html`, `static/`: interfaz sin framework de frontend.
- `test_mk3.py`, `verificar.py`: pruebas de contrato y comprobación real.
- `requirements.txt`: dependencias directas; `requirements-lock.txt`: versiones completas del entorno comprobado (Python 3.12, Linux CPU). La disponibilidad de ruedas depende de tu sistema.

Implementación basada en la [documentación oficial de OWL-ViT en Transformers](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/owlvit) y su [modelo preentrenado](https://huggingface.co/google/owlvit-base-patch32), con revisión fijada en el código y pesos `safetensors`. Consulta la ficha del modelo para su licencia Apache-2.0, procedencia y limitaciones. No se incluyen pesos, datasets ni fotos de prueba en Git.
