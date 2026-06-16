/*
 * app.js - Fuchibol26
 * ====================
 * RESPONSABILIDAD: Cargar los datos desde JSON y renderizar la UI.
 * 
 * FLUJO DE DATOS:
 * 1. Al cargar la página → fetch() descarga los JSON desde web/data/
 * 2. Los datos se guardan en variables globales (DATOS_*)
 * 3. Cada función de renderizado usa esas variables
 * 4. Si los JSON cambian (nuevo run de Python), la página muestra datos nuevos
 *    automáticamente al recargar
 * 
 * IMPORTANTE: Los datos NO están hardcodeados aquí.
 * Los JSON son generados por: python scripts/ejecutar_todo.py
 */

// ════════════════════════════════════════════════════════════════
// VARIABLES GLOBALES
// ════════════════════════════════════════════════════════════════

// Datos cargados desde los archivos JSON
let DATOS_ELO = [];          // ranking_elo.json
let DATOS_PREDICCIONES = []; // predicciones.json
let DATOS_SIMULACION = [];   // simulacion.json
let DATOS_STATS = [];        // estadisticas.json

// Estado de la app
let usuarioActual = '';
let todasLasQuinielas = JSON.parse(localStorage.getItem('fuchi26_quinielas') || '{}');
let modoOscuro = localStorage.getItem('fuchi26_dark') === '1';


// ════════════════════════════════════════════════════════════════
// CARGA DE DATOS JSON
// ════════════════════════════════════════════════════════════════

/**
 * Carga UN archivo JSON desde la carpeta data/
 * 
 * fetch() es una función nativa del navegador para hacer peticiones HTTP.
 * Devuelve una "Promise" (promesa) que se resuelve cuando llegan los datos.
 * 
 * @param {string} archivo - Nombre del archivo (ej: "ranking_elo.json")
 * @returns {Promise<Array>} - Los datos del JSON como array
 */
async function cargarJSON(archivo) {
  try {
    // fetch() descarga el archivo
    const respuesta = await fetch(`data/${archivo}`);
    
    if (!respuesta.ok) {
      // Si el servidor devolvió error (404 = no encontrado, etc.)
      throw new Error(`HTTP ${respuesta.status}: ${archivo} no encontrado`);
    }
    
    // .json() convierte el texto JSON a un objeto JavaScript
    return await respuesta.json();
    
  } catch (error) {
    console.error(`❌ Error cargando ${archivo}:`, error);
    return []; // Devolver array vacío en caso de error
  }
}

/**
 * Carga TODOS los archivos JSON en paralelo.
 * 
 * Promise.all() ejecuta múltiples fetches al mismo tiempo (más rápido
 * que hacerlos uno por uno).
 * 
 * @returns {Promise<boolean>} - true si todos cargaron bien
 */
async function cargarTodosLosDatos() {
  try {
    // Cargar todos los JSON al mismo tiempo
    const [elo, predicciones, simulacion, stats, metadata] = await Promise.all([
      cargarJSON('ranking_elo.json'),
      cargarJSON('predicciones.json'),
      cargarJSON('simulacion.json'),
      cargarJSON('estadisticas.json'),
      cargarJSON('metadata.json'),
    ]);
    
    // Guardar en variables globales
    DATOS_ELO = elo;
    DATOS_PREDICCIONES = predicciones;
    DATOS_SIMULACION = simulacion;
    DATOS_STATS = stats;
    
    // Mostrar fecha de actualización en la barra de nav
    if (metadata && metadata.ultima_actualizacion_legible) {
      const badge = document.getElementById('ultima-actualizacion');
      if (badge) badge.textContent = `📅 ${metadata.ultima_actualizacion_legible}`;
    }
    
    console.log('✅ Datos cargados:', {
      elo: DATOS_ELO.length,
      predicciones: DATOS_PREDICCIONES.length,
      simulacion: DATOS_SIMULACION.length,
      stats: DATOS_STATS.length,
    });
    
    return true;
    
  } catch (error) {
    console.error('❌ Error cargando datos:', error);
    return false;
  }
}


// ════════════════════════════════════════════════════════════════
// TEMA OSCURO / CLARO
// ════════════════════════════════════════════════════════════════

function aplicarTema() {
  document.body.classList.toggle('dark', modoOscuro);
  document.getElementById('theme-btn').textContent = modoOscuro ? '☀️' : '🌙';
}

function toggleTheme() {
  modoOscuro = !modoOscuro;
  localStorage.setItem('fuchi26_dark', modoOscuro ? '1' : '0');
  aplicarTema();
}


// ════════════════════════════════════════════════════════════════
// LOGIN
// ════════════════════════════════════════════════════════════════

function entrar() {
  const input = document.getElementById('login-input').value.trim();
  if (!input) return;
  
  usuarioActual = input;
  document.getElementById('user-badge').textContent = '👤 ' + input;
  document.getElementById('login-screen').style.display = 'none';
  
  if (!todasLasQuinielas[usuarioActual]) {
    todasLasQuinielas[usuarioActual] = {};
  }
  
  iniciarApp();
}

// Permitir entrar con Enter
document.getElementById('login-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') entrar();
});

function cambiarUsuario() {
  if (confirm('¿Cambiar de usuario?')) {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('login-input').value = '';
  }
}


// ════════════════════════════════════════════════════════════════
// NAVEGACIÓN
// ════════════════════════════════════════════════════════════════

function showPage(id, el) {
  // Ocultar todas las páginas
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  // Desactivar todos los links del nav
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  
  // Mostrar la página solicitada
  document.getElementById('page-' + id).classList.add('active');
  el.classList.add('active');
}


// ════════════════════════════════════════════════════════════════
// INICIALIZACIÓN
// ════════════════════════════════════════════════════════════════

/**
 * Se llama después del login. Renderiza todos los componentes.
 */
function iniciarApp() {
  // Si los datos ya están cargados, renderizar directamente
  if (DATOS_ELO.length > 0) {
    renderizarTodo();
  } else {
    // Si no, mostrar mensaje de espera
    console.warn('⚠ Los datos aún no están cargados');
  }
}

/**
 * Renderiza todos los componentes de la UI con los datos actuales.
 */
function renderizarTodo() {
  renderPartidos();
  renderRankingQuiniela();
  renderElo('todos');
  renderPrediccionesGrupos();
  renderSimulacion();
  poblarSelectores();
  actualizarHeroes();
}

/**
 * Actualiza los números grandes en los heroes de cada página.
 */
function actualizarHeroes() {
  // Hero de estadísticas
  document.getElementById('total-selecciones').textContent = DATOS_ELO.length;
  if (DATOS_ELO.length > 0) {
    // El primer equipo del JSON ya viene ordenado por ELO (el más alto primero)
    document.getElementById('hero-top-equipo').textContent = 
      `${DATOS_ELO[0].bandera || ''} ${DATOS_ELO[0].seleccion}`;
  }
  
  // Hero de predicciones
  document.getElementById('hero-partidos-pred').textContent = DATOS_PREDICCIONES.length;
  
  // Hero de simulación
  if (DATOS_SIMULACION.length > 0) {
    const favorito = DATOS_SIMULACION[0]; // Ya viene ordenado por probabilidad
    document.getElementById('hero-favorito-pct').textContent = 
      `${favorito.probabilidad_campeon}%`;
    document.getElementById('hero-favorito-nombre').textContent = 
      `${favorito.bandera || ''} ${favorito.seleccion}`;
  }
}


// ════════════════════════════════════════════════════════════════
// QUINIELA - PARTIDOS
// ════════════════════════════════════════════════════════════════

/**
 * Obtener la bandera de un equipo desde los datos de ELO.
 * @param {string} nombre - Nombre del equipo
 * @returns {string} - Emoji de bandera o '🏳️'
 */
function getBandera(nombre) {
  const equipo = DATOS_ELO.find(e => e.seleccion === nombre);
  return equipo ? (equipo.bandera || '🏳️') : '🏳️';
}

/**
 * Renderiza la lista de partidos para la quiniela.
 * Los partidos vienen de predicciones.json (generado por Python).
 */
function renderPartidos() {
  const mis = todasLasQuinielas[usuarioActual] || {};
  
  if (DATOS_PREDICCIONES.length === 0) {
    document.getElementById('partidos-list').innerHTML = 
      `<p class="error-msg">⚠ No se encontraron datos de partidos.<br>
       Ejecuta: <code>python scripts/ejecutar_todo.py</code></p>`;
    return;
  }
  
  let html = '';
  let grupoActual = '';
  
  DATOS_PREDICCIONES.forEach(p => {
    // Separador de grupo
    if (p.grupo !== grupoActual) {
      grupoActual = p.grupo;
      html += `<div class="grupo-label">Grupo ${p.grupo}</div>`;
    }
    
    const banderaLocal = getBandera(p.local);
    const banderaVisitante = getBandera(p.visitante);
    const pred = mis[p.id] || { l: '', v: '' };
    
    // Formatear fecha
    const fecha = new Date(p.fecha + 'T12:00:00');
    const fechaStr = fecha.toLocaleDateString('es', { day: 'numeric', month: 'short' });
    
    html += `
    <div class="partido" id="partido-${p.id}">
      <div class="equipo">
        <span class="bandera">${banderaLocal}</span>
        <span>${p.local}</span>
      </div>
      
      <div class="vs-box">
        <div class="vs-label">${fechaStr}</div>
        <div class="score-inputs">
          <input class="score-input" type="number" min="0" max="20"
            id="${p.id}-l" value="${pred.l}"
            onchange="guardarTemp('${p.id}','l',this.value)">
          <span class="score-sep">-</span>
          <input class="score-input" type="number" min="0" max="20"
            id="${p.id}-v" value="${pred.v}"
            onchange="guardarTemp('${p.id}','v',this.value)">
        </div>
        <div style="font-size:11px;color:var(--texto-suave);margin-top:3px">
          Modelo: ${p.marcador_probable || '—'}
        </div>
      </div>
      
      <div class="equipo visitante">
        <span class="bandera">${banderaVisitante}</span>
        <span>${p.visitante}</span>
      </div>
    </div>`;
  });
  
  document.getElementById('partidos-list').innerHTML = html;
  calcularPuntos();
}

function guardarTemp(id, lado, val) {
  if (!todasLasQuinielas[usuarioActual]) todasLasQuinielas[usuarioActual] = {};
  if (!todasLasQuinielas[usuarioActual][id]) todasLasQuinielas[usuarioActual][id] = { l: '', v: '' };
  todasLasQuinielas[usuarioActual][id][lado] = val;
}

function guardarQuiniela() {
  localStorage.setItem('fuchi26_quinielas', JSON.stringify(todasLasQuinielas));
  const msg = document.getElementById('save-msg');
  msg.style.display = 'block';
  renderRankingQuiniela();
  setTimeout(() => msg.style.display = 'none', 2500);
}

function calcularPuntos() {
  // Por ahora no hay resultados reales en el JSON, devuelve 0
  // Cuando haya resultados en el JSON de predicciones, se calculará aquí
  document.getElementById('hero-puntos').textContent = 0;
  return 0;
}

function renderRankingQuiniela() {
  const todos = Object.entries(todasLasQuinielas).map(([nombre, preds]) => {
    return { nombre, pts: 0 }; // Se actualizará cuando haya resultados reales
  }).sort((a, b) => b.pts - a.pts);
  
  const medalas = ['🥇', '🥈', '🥉'];
  
  const html = todos.map((j, i) => `
    <div class="jugador">
      <div class="avatar">${j.nombre[0].toUpperCase()}</div>
      <div class="jugador-info">
        <div class="jugador-nombre">${j.nombre}${j.nombre === usuarioActual ? ' <span style="font-size:11px;color:var(--verde)">· tú</span>' : ''}</div>
        <div class="jugador-pts">${medalas[i] || '#' + (i + 1)} posición</div>
      </div>
      <div class="pts-badge">${j.pts} pts</div>
    </div>`).join('');
  
  document.getElementById('ranking-list').innerHTML = 
    html || '<p class="cargando">Aún no hay predicciones guardadas.</p>';
}


// ════════════════════════════════════════════════════════════════
// ESTADÍSTICAS - RANKING ELO
// ════════════════════════════════════════════════════════════════

/**
 * Renderiza la tabla de ranking ELO.
 * Lee de DATOS_ELO que viene de ranking_elo.json (generado por Python).
 * 
 * @param {string} filtro - 'todos' o una confederación (UEFA, CONMEBOL, etc.)
 */
function renderElo(filtro) {
  if (DATOS_ELO.length === 0) {
    document.getElementById('elo-tbody').innerHTML = 
      `<tr><td colspan="4" class="error-msg">⚠ No hay datos ELO. Ejecuta el script Python.</td></tr>`;
    return;
  }
  
  // Filtrar por confederación si se especificó
  const lista = filtro === 'todos' 
    ? DATOS_ELO 
    : DATOS_ELO.filter(e => e.confederacion === filtro);
  
  // Valor máximo de ELO para calcular el ancho de las barras
  const maxElo = Math.max(...DATOS_ELO.map(e => e.elo));
  
  const html = lista.map((e, i) => `
    <tr>
      <td class="pos ${i < 3 ? 'top' : ''}">${e.posicion}</td>
      <td><span style="margin-right:6px">${e.bandera || '🏳️'}</span>${e.seleccion}</td>
      <td style="color:var(--texto-suave);font-size:12px">${e.confederacion}</td>
      <td style="text-align:right">
        <strong>${e.elo}</strong>
        <div class="elo-bar">
          <div class="elo-fill" style="width:${Math.round(e.elo / maxElo * 100)}%"></div>
        </div>
      </td>
    </tr>`).join('');
  
  document.getElementById('elo-tbody').innerHTML = html;
}

function filtrarElo(filtro, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderElo(filtro);
}


// ════════════════════════════════════════════════════════════════
// PREDICCIONES - POISSON
// ════════════════════════════════════════════════════════════════

/**
 * Renderiza las predicciones de todos los partidos de grupos.
 * Los datos vienen de predicciones.json (calculado por generar_poisson.py).
 */
function renderPrediccionesGrupos() {
  const contenedor = document.getElementById('predicciones-grupos-list');
  
  if (DATOS_PREDICCIONES.length === 0) {
    contenedor.innerHTML = `<p class="error-msg">⚠ Sin datos. Ejecuta el script Python.</p>`;
    return;
  }
  
  const html = DATOS_PREDICCIONES.map(p => {
    const banderaL = getBandera(p.local);
    const banderaV = getBandera(p.visitante);
    
    return `
    <div class="pred-partido">
      <div class="pred-equipos">
        <div>
          <div style="font-size:20px">${banderaL}</div>
          <div class="pred-equipo" style="margin-top:4px">${p.local}</div>
          <div style="font-size:11px;color:var(--texto-suave)">ELO ${p.elo_local || '—'}</div>
        </div>
        
        <div class="pred-centro">
          <div style="font-size:11px;color:var(--texto-suave);margin-bottom:4px">más probable</div>
          <div class="marcador-probable">${p.marcador_probable || '—'}</div>
          <div style="font-size:11px;color:var(--texto-suave);margin-top:2px">Grupo ${p.grupo} · ${p.fecha}</div>
        </div>
        
        <div style="text-align:right">
          <div style="font-size:20px">${banderaV}</div>
          <div class="pred-equipo right" style="margin-top:4px">${p.visitante}</div>
          <div style="font-size:11px;color:var(--texto-suave)">ELO ${p.elo_visitante || '—'}</div>
        </div>
      </div>
      
      <!-- Barra de probabilidades -->
      <div class="prob-bar">
        <div class="prob-local" style="width:${p.prob_local || 33}%"></div>
        <div class="prob-empate" style="width:${p.prob_empate || 34}%"></div>
        <div class="prob-visit" style="width:${p.prob_visitante || 33}%"></div>
      </div>
      
      <div class="prob-numeros">
        <span style="color:var(--verde)">🟢 ${p.prob_local || '—'}%</span>
        <span style="color:var(--dorado)">🟡 ${p.prob_empate || '—'}% empate</span>
        <span style="color:#d44">🔴 ${p.prob_visitante || '—'}%</span>
      </div>
    </div>`;
  }).join('');
  
  contenedor.innerHTML = html;
}

/**
 * Llena los selectores de equipos para la simulación ad-hoc.
 */
function poblarSelectores() {
  if (DATOS_ELO.length === 0) return;
  
  const opts = DATOS_ELO
    .map(e => `<option value="${e.seleccion}">${e.bandera || '🏳️'} ${e.seleccion}</option>`)
    .join('');
  
  document.getElementById('sel-local').innerHTML = '<option value="">Local...</option>' + opts;
  document.getElementById('sel-visit').innerHTML = '<option value="">Visitante...</option>' + opts;
}

/**
 * Simula un partido ad-hoc usando los datos de ELO y estadísticas.
 * Esta es una simulación rápida en el navegador (no tan precisa como Python).
 */
function simularPartido() {
  const localNombre = document.getElementById('sel-local').value;
  const visitanteNombre = document.getElementById('sel-visit').value;
  const div = document.getElementById('simulacion-resultado');
  
  if (!localNombre || !visitanteNombre || localNombre === visitanteNombre) {
    div.innerHTML = '';
    return;
  }
  
  const eqL = DATOS_ELO.find(e => e.seleccion === localNombre);
  const eqV = DATOS_ELO.find(e => e.seleccion === visitanteNombre);
  
  if (!eqL || !eqV) return;
  
  // Ver si hay una predicción pre-calculada por Python para este partido
  const predCalculada = DATOS_PREDICCIONES.find(
    p => p.local === localNombre && p.visitante === visitanteNombre
  );
  
  let probL, probE, probV, marcadorProbable;
  
  if (predCalculada) {
    // Usar la predicción exacta de Python (más precisa)
    probL = predCalculada.prob_local;
    probE = predCalculada.prob_empate;
    probV = predCalculada.prob_visitante;
    marcadorProbable = predCalculada.marcador_probable;
  } else {
    // Calcular aproximación con ELO (menos precisa pero rápida)
    const diff = (eqL.elo - eqV.elo) / 400;
    probL = Math.round(1 / (1 + Math.pow(10, -diff)) * 70 * 10) / 10;
    probE = Math.round(Math.max(5, 30 - Math.abs(eqL.elo - eqV.elo) / 50) * 10) / 10;
    probV = Math.round(Math.max(5, 100 - probL - probE) * 10) / 10;
    marcadorProbable = '— (usa Python para Poisson exacto)';
  }
  
  div.innerHTML = `
    <div style="border:1px solid var(--borde);border-radius:var(--radio-sm);padding:16px">
      <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:1rem;margin-bottom:14px">
        <div>
          <div style="font-size:24px">${eqL.bandera || '🏳️'}</div>
          <div style="font-weight:600;margin-top:4px">${eqL.seleccion}</div>
          <div style="font-size:11px;color:var(--texto-suave)">ELO ${eqL.elo}</div>
        </div>
        
        <div style="text-align:center">
          <div style="font-size:11px;color:var(--texto-suave)">marcador probable</div>
          <div style="font-size:22px;font-weight:700;color:var(--verde)">${marcadorProbable}</div>
          ${predCalculada ? '<div style="font-size:10px;color:var(--verde)">✓ Poisson (Python)</div>' : '<div style="font-size:10px;color:var(--texto-suave)">Aprox. ELO</div>'}
        </div>
        
        <div style="text-align:right">
          <div style="font-size:24px">${eqV.bandera || '🏳️'}</div>
          <div style="font-weight:600;margin-top:4px">${eqV.seleccion}</div>
          <div style="font-size:11px;color:var(--texto-suave)">ELO ${eqV.elo}</div>
        </div>
      </div>
      
      <div class="prob-bar">
        <div class="prob-local" style="width:${probL}%"></div>
        <div class="prob-empate" style="width:${probE}%"></div>
        <div class="prob-visit" style="width:${probV}%"></div>
      </div>
      <div class="prob-numeros">
        <span style="color:var(--verde)">🟢 ${probL}%</span>
        <span style="color:var(--dorado)">🟡 ${probE}%</span>
        <span style="color:#d44">🔴 ${probV}%</span>
      </div>
    </div>`;
}


// ════════════════════════════════════════════════════════════════
// SIMULACIÓN DEL MUNDIAL
// ════════════════════════════════════════════════════════════════

/**
 * Renderiza la lista de probabilidades de ser campeón.
 * Los datos vienen de simulacion.json (generado por simular_mundial.py).
 */
function renderSimulacion() {
  const contenedor = document.getElementById('prob-campeon-list');
  
  if (DATOS_SIMULACION.length === 0) {
    contenedor.innerHTML = `<p class="error-msg">⚠ Sin datos. Ejecuta el script Python.</p>`;
    return;
  }
  
  // Mostrar solo los top 20 (el resto tiene probabilidades muy bajas)
  const top20 = DATOS_SIMULACION.slice(0, 20);
  const maxProb = top20[0].probabilidad_campeon;
  
  const html = top20.map((e, i) => `
    <div class="campeon-item">
      <div style="width:24px;font-size:13px;font-weight:700;color:var(--texto-suave)">
        ${i + 1}
      </div>
      <div style="font-size:20px;width:30px">${e.bandera || '🏳️'}</div>
      <div style="flex:1;font-size:14px;font-weight:500">${e.seleccion}</div>
      <div class="campeon-barra-wrap" style="width:120px">
        <div class="campeon-barra">
          <div class="campeon-fill" 
               style="width:${(e.probabilidad_campeon / maxProb * 100).toFixed(0)}%">
          </div>
        </div>
        <div style="font-size:10px;color:var(--texto-suave);margin-top:2px">
          ELO: ${e.elo || '—'}
        </div>
      </div>
      <div class="campeon-pct">${e.probabilidad_campeon}%</div>
    </div>`).join('');
  
  contenedor.innerHTML = html;
}


// ════════════════════════════════════════════════════════════════
// INICIALIZACIÓN DE LA APLICACIÓN
// ════════════════════════════════════════════════════════════════

/**
 * Función que se ejecuta cuando se carga la página.
 * Primero carga los datos, luego aplica el tema.
 */
async function init() {
  // Aplicar tema oscuro/claro
  aplicarTema();
  
  // Cargar todos los JSON en segundo plano
  await cargarTodosLosDatos();
  
  // Si el usuario ya está logueado (por ejemplo, recargó la página),
  // renderizar la app. (Normalmente el login se muestra primero)
}

// Ejecutar al cargar la página
init();
