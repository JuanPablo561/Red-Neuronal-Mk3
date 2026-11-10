const $ = id => document.getElementById(id);
const lienzo = $('lienzo');
const ctx = lienzo.getContext('2d');
let archivo = null;
let imagen = null;
let resultado = null;
let seleccionado = -1;
let peticion = 0;
let controlador = null;
let urlLocal = null;

function dibujar() {
  if (!imagen) return;
  lienzo.width = imagen.naturalWidth;
  lienzo.height = imagen.naturalHeight;
  ctx.drawImage(imagen, 0, 0);
  const escala = Math.max(lienzo.width / 650, 1);
  (resultado?.detecciones || []).forEach((d, i) => {
    const [x1, y1, x2, y2] = d.caja;
    ctx.strokeStyle = i === seleccionado ? '#14556a' : '#a54427';
    ctx.lineWidth = (i === seleccionado ? 5 : 3) * escala;
    ctx.strokeRect(x1*lienzo.width, y1*lienzo.height, (x2-x1)*lienzo.width, (y2-y1)*lienzo.height);
    const texto = `${i+1} · ${d.clase}`;
    ctx.font = `600 ${14*escala}px system-ui`;
    const ancho = Math.min(ctx.measureText(texto).width + 16*escala, lienzo.width);
    const alto = 26*escala;
    const x = Math.max(0, Math.min(x1*lienzo.width, lienzo.width-ancho));
    const y = Math.max(0, Math.min(y1*lienzo.height-alto, lienzo.height-alto));
    ctx.fillStyle = ctx.strokeStyle;
    ctx.fillRect(x, y, ancho, alto);
    ctx.fillStyle = '#fff';
    ctx.fillText(texto, x+8*escala, y+18*escala, ancho-8*escala);
  });
}

function cargarImagen(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('No se pudo mostrar la imagen.'));
    img.src = url;
  });
}

function listar() {
  $('resultados').replaceChildren();
  resultado.detecciones.forEach((d, i) => {
    const li = document.createElement('li');
    const boton = document.createElement('button');
    boton.className = 'resultado';
    boton.setAttribute('aria-pressed', 'false');
    const numero = document.createElement('span');
    numero.className = 'numero'; numero.textContent = i+1;
    const nombre = document.createElement('span'); nombre.textContent = d.clase;
    const puntuacion = document.createElement('small');
    puntuacion.textContent = d.puntuacion.toFixed(3);
    puntuacion.setAttribute('aria-label', `Puntuación ${d.puntuacion.toFixed(3)}`);
    boton.append(numero, nombre, puntuacion);
    boton.addEventListener('click', () => {
      seleccionado = seleccionado === i ? -1 : i;
      document.querySelectorAll('.resultado').forEach((b, j) => b.setAttribute('aria-pressed', String(j === seleccionado)));
      dibujar();
    });
    li.append(boton); $('resultados').append(li);
  });
}

async function analizar(nuevoArchivo) {
  if (nuevoArchivo) archivo = nuevoArchivo;
  if (!archivo) return;
  const mia = ++peticion;
  controlador?.abort();
  controlador = new AbortController();
  resultado = null; seleccionado = -1;
  imagen = null; lienzo.hidden = true; $('vacio').hidden = false;
  $('dimensiones').textContent = 'JPEG · PNG · WEBP';
  $('resultados').replaceChildren(); $('total').textContent = '—';
  $('descargar').disabled = true; $('analizar').disabled = true;
  $('error').hidden = true; $('estado').textContent = 'Analizando la escena… En CPU puede tardar varios segundos.';
  $('zona').setAttribute('aria-busy', 'true');
  try {
    if (urlLocal) URL.revokeObjectURL(urlLocal);
    urlLocal = URL.createObjectURL(archivo);
    const previa = await cargarImagen(urlLocal);
    if (mia !== peticion) return;
    imagen = previa; $('vacio').hidden = true; lienzo.hidden = false; dibujar();
    const datos = new FormData();
    datos.append('imagen', archivo); datos.append('umbral', $('umbral').value);
    const respuesta = await fetch('/predecir', {method:'POST', body:datos, signal:controlador.signal});
    const json = await respuesta.json();
    if (!respuesta.ok) throw new Error(json.error || 'No se pudo analizar la imagen.');
    const procesada = await cargarImagen(json.vista);
    if (mia !== peticion) return;
    imagen = procesada; resultado = json;
    $('dimensiones').textContent = `${json.ancho} × ${json.alto} px`;
    $('total').textContent = `${json.detecciones.length} encontradas`;
    $('estado').textContent = json.detecciones.length
      ? `Análisis terminado en ${json.segundos} s. Revisa las propuestas del modelo.`
      : 'No se encontraron prendas con este umbral. Prueba otra foto o un valor menor; esto no demuestra que no haya prendas.';
    listar(); dibujar(); $('descargar').disabled = false;
  } catch (err) {
    if (mia !== peticion || err.name === 'AbortError') return;
    $('error').textContent = err instanceof TypeError ? 'No se pudo contactar con el servidor.' : err.message;
    $('error').hidden = false; $('estado').textContent = 'El análisis no se completó.';
  } finally {
    if (mia === peticion) { $('analizar').disabled = false; $('zona').setAttribute('aria-busy', 'false'); }
  }
}

['archivo', 'camara'].forEach(id => $(id).addEventListener('change', e => {
  const f = e.target.files[0]; e.target.value = ''; if (f) analizar(f);
}));
$('analizar').addEventListener('click', () => analizar());
$('umbral').addEventListener('input', () => { $('valor').value = Number($('umbral').value).toFixed(2); });
['dragenter','dragover'].forEach(ev => $('zona').addEventListener(ev, e => {
  e.preventDefault(); $('zona').classList.add('arrastrando');
}));
['dragleave','drop'].forEach(ev => $('zona').addEventListener(ev, e => {
  e.preventDefault(); $('zona').classList.remove('arrastrando');
}));
$('zona').addEventListener('drop', e => { const f = e.dataTransfer.files[0]; if (f) analizar(f); });
$('descargar').addEventListener('click', () => {
  if (!resultado) return;
  const {vista, ...datos} = resultado;
  const url = URL.createObjectURL(new Blob([JSON.stringify(datos, null, 2)], {type:'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'mk3-detecciones.json'; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
