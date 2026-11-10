# Verificación de la primera versión

Comprobada el 10 de noviembre de 2026 en Linux, Python 3.12 y CPU, con el entorno de `requirements-lock.txt`.

- `python -m unittest -v`: 5 pruebas aprobadas (contrato de API, validación, límites, respuesta vacía y filtrado de cajas).
- `python verificar.py <foto>`: inferencia real de OWL-ViT, respuesta HTTP 200 y coordenadas válidas. La foto de prueba contenía una persona con abrigo y bolsas; se obtuvieron cinco propuestas a umbral 0.15, incluidas propuestas superpuestas de puntuación baja. Este resultado no mide exactitud ni cinco objetos distintos correctamente reconocidos.
- Navegador Chromium con Playwright: carga real hacia Flask y el modelo, cajas y lista, selección del resultado, exportación JSON sin imagen, cambio de umbral y nuevo análisis, error ante archivo ilegible y limpieza del resultado anterior.
- Vista a 320, 768, 1024 y 1440 px sin desbordamiento horizontal; sin errores de JavaScript observados durante el recorrido.
- `node --check static/app.js`, `python -m pip check` y `git diff --check`: aprobados.

No se comprobó la cámara física de un teléfono, CUDA, Windows ni macOS. No hay evaluación de mAP, oclusión o precisión por clase; requiere un conjunto de escenas anotadas independiente. Las pruebas de integración usan la imagen de prueba solo de forma temporal; no se incluye en el repositorio.
