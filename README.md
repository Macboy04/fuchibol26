# Fuchibol26

Plataforma de análisis, predicción y simulación del Mundial FIFA 2026.

## Objetivo

Fuchibol26 busca construir un motor estadístico capaz de:

* Analizar selecciones nacionales.
* Generar rankings de fortaleza.
* Predecir resultados de partidos.
* Simular torneos completos.
* Estimar probabilidades de clasificación.
* Estimar probabilidades de campeonato.
* Evolucionar hacia modelos avanzados de Machine Learning.

---

## Arquitectura Actual

### Paso 1 - Actualización de Datos

Fuente:

https://raw.githubusercontent.com/martj42/international_results/master/results.csv

Genera:

datos/historicos/resultados.csv

---

### Paso 2 - Estadísticas Históricas

Script:

scripts/generar_estadisticas.py

Genera:

datos/procesados/estadisticas.csv

Incluye:

* Partidos jugados
* Victorias
* Empates
* Derrotas
* Goles a favor
* Goles en contra
* Lambda ataque
* Lambda defensa

---

### Paso 3 - Ranking ELO

Script:

scripts/generar_elo.py

Genera:

datos/procesados/ranking_elo.csv

Basado en:

ELO clásico.

---

### Paso 4 - Predicción Poisson

Script:

scripts/generar_poisson.py

Genera:

datos/procesados/predicciones.csv

Calcula:

* Victoria local
* Empate
* Victoria visitante
* Marcador más probable

---

### Paso 5 - Simulación Monte Carlo

Script:

scripts/simular_mundial.py

Genera:

datos/procesados/simulacion_mundial.csv

Ejecuta:

1000 simulaciones completas del Mundial.

---

### Paso 6 - Exportación JSON

Script:

scripts/generar_json.py

Genera:

web/data/*.json

---

## Ejecución

Actualizar todo:

```bash
python scripts/ejecutar_todo.py
```

Visualizar web:

```bash
python -m http.server 8000
```

Abrir:

http://localhost:8000/web/

---

## Estado Actual

Pipeline funcional:

✅ Actualización de datos

✅ Estadísticas

✅ ELO

✅ Poisson

✅ Monte Carlo

✅ Exportación JSON

---

## Próxima Fase

* Dynamic ELO
* xG
* Machine Learning
* API REST
* Dashboard avanzado
* Simulación de 100,000 torneos
* Historial ELO
* Brackets interactivos
* Deployment en nube
