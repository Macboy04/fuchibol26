"""
generar_poisson.py
------------------
RESPONSABILIDAD: Calcular predicciones usando el modelo de Poisson.

¿QUÉ ES EL MODELO DE POISSON EN FÚTBOL?
  La distribución de Poisson modela eventos que ocurren a una tasa
  promedio conocida. Los goles en fútbol siguen esta distribución.
  
  IDEA: Si Brasil mete en promedio 2.5 goles por partido,
        ¿cuál es la probabilidad de que meta exactamente 0, 1, 2, 3... goles?
  
  P(k goles) = (e^(-λ) × λ^k) / k!
  
  Donde:
  - λ (lambda) = promedio de goles esperados
  - k = número de goles específico (0, 1, 2, 3...)
  - e = número de Euler ≈ 2.718
  
  Para un partido entre local y visitante:
  - λ_local = ataque_local × defensa_visitante × promedio_global
  - λ_visitante = ataque_visitante × defensa_local × promedio_global

Guarda el resultado en: datos/procesados/predicciones.csv
"""

import os
import pandas as pd
import numpy as np
from scipy.stats import poisson  # Distribución de Poisson de SciPy

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
ARCHIVO_ESTADISTICAS = os.path.join(RUTA_BASE, "datos", "procesados", "estadisticas.csv")
ARCHIVO_ELO = os.path.join(RUTA_BASE, "datos", "procesados", "ranking_elo.csv")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
ARCHIVO_PREDICCIONES = os.path.join(RUTA_PROCESADOS, "predicciones.csv")

# Goles máximos a considerar en la matriz de probabilidades
# (probabilidad de meter más de 8 goles es negligible)
MAX_GOLES = 8

# Partidos de fase de grupos del Mundial 2026
# Estos son los partidos que vamos a predecir
PARTIDOS_MUNDIAL = [
    # Grupo A
    {"id": "p1", "fecha": "2026-06-11", "grupo": "A", "local": "Mexico", "visitante": "Canada"},
    {"id": "p2", "fecha": "2026-06-12", "grupo": "A", "local": "United States", "visitante": "New Zealand"},
    # Grupo B
    {"id": "p3", "fecha": "2026-06-13", "grupo": "B", "local": "Argentina", "visitante": "Chile"},
    {"id": "p4", "fecha": "2026-06-14", "grupo": "B", "local": "Australia", "visitante": "Peru"},
    # Grupo C
    {"id": "p5", "fecha": "2026-06-15", "grupo": "C", "local": "Brazil", "visitante": "Uruguay"},
    {"id": "p6", "fecha": "2026-06-16", "grupo": "C", "local": "Panama", "visitante": "Guatemala"},
    # Grupo D
    {"id": "p7", "fecha": "2026-06-17", "grupo": "D", "local": "England", "visitante": "France"},
    {"id": "p8", "fecha": "2026-06-18", "grupo": "D", "local": "Germany", "visitante": "Switzerland"},
    # Grupo E
    {"id": "p9", "fecha": "2026-06-19", "grupo": "E", "local": "Spain", "visitante": "Portugal"},
    {"id": "p10", "fecha": "2026-06-20", "grupo": "E", "local": "Belgium", "visitante": "Ivory Coast"},
    # Grupo F
    {"id": "p11", "fecha": "2026-06-21", "grupo": "F", "local": "Netherlands", "visitante": "Turkey"},
    # Grupo G
    {"id": "p12", "fecha": "2026-06-22", "grupo": "G", "local": "Japan", "visitante": "South Korea"},
]


# ── FUNCIONES ─────────────────────────────────────────────────────────────────

def predecir_partido(stats_local, stats_visitante, promedio_global):
    """
    Predice el resultado de un partido usando el modelo Poisson.
    
    CÓMO FUNCIONA:
    1. Calculamos λ_local: cuántos goles esperamos que meta el local
       λ_local = (ataque_local / promedio_global) × (defensa_visitante / promedio_global) × promedio_global
       
       Simplificado: λ_local = ataque_local × (defensa_visitante / promedio_global)
    
    2. Hacemos lo mismo para el visitante
    
    3. Creamos una matriz de probabilidades donde:
       - filas = goles del local (0,1,2,...,8)
       - columnas = goles del visitante (0,1,2,...,8)
       - celda [i][j] = probabilidad de que el local meta i goles Y el visitante meta j goles
    
    4. Sumamos las probabilidades para obtener P(local gana), P(empate), P(visitante gana)
    
    Args:
        stats_local (dict): Estadísticas del equipo local
        stats_visitante (dict): Estadísticas del equipo visitante  
        promedio_global (float): Promedio de goles por partido de todos los equipos
    
    Returns:
        dict: Predicciones del partido
    """
    
    # Lambda esperada para cada equipo
    # Fórmula de Dixon-Coles simplificada
    lambda_local = (
        stats_local['lambda_ataque'] *
        stats_visitante['lambda_defensa'] /
        promedio_global
    )
    
    lambda_visitante = (
        stats_visitante['lambda_ataque'] *
        stats_local['lambda_defensa'] /
        promedio_global
    )
    
    # Asegurar que lambda no sea negativa o cero
    lambda_local = max(lambda_local, 0.1)
    lambda_visitante = max(lambda_visitante, 0.1)
    
    # Crear la distribución de Poisson para cada equipo
    # poisson.pmf(k, mu) = probabilidad de exactamente k goles con media mu
    # Calculamos para 0, 1, 2, ..., MAX_GOLES goles
    goles_posibles = np.arange(0, MAX_GOLES + 1)
    
    prob_local = poisson.pmf(goles_posibles, lambda_local)    # [P(0), P(1), ..., P(8)]
    prob_visitante = poisson.pmf(goles_posibles, lambda_visitante)
    
    # Crear la matriz de resultados
    # np.outer(a, b) crea una matriz donde matrix[i][j] = a[i] × b[j]
    # Esto funciona porque los goles de cada equipo son independientes
    matriz_prob = np.outer(prob_local, prob_visitante)
    
    # Probabilidad de victoria del local: suma de la triangular inferior
    # (cuando goles_local > goles_visitante, es decir, filas > columnas)
    prob_victoria_local = np.tril(matriz_prob, k=-1).sum()
    
    # Probabilidad de empate: diagonal principal
    prob_empate = np.trace(matriz_prob)
    
    # Probabilidad de victoria del visitante: triangular superior
    prob_victoria_visitante = np.triu(matriz_prob, k=1).sum()
    
    # Marcador más probable: la celda con mayor probabilidad en la matriz
    idx_max = np.unravel_index(np.argmax(matriz_prob), matriz_prob.shape)
    marcador_probable_local = int(idx_max[0])
    marcador_probable_visitante = int(idx_max[1])
    
    return {
        'lambda_local': round(lambda_local, 4),
        'lambda_visitante': round(lambda_visitante, 4),
        'prob_local': round(prob_victoria_local * 100, 2),
        'prob_empate': round(prob_empate * 100, 2),
        'prob_visitante': round(prob_victoria_visitante * 100, 2),
        'goles_esperados_local': round(lambda_local, 2),
        'goles_esperados_visitante': round(lambda_visitante, 2),
        'marcador_probable': f"{marcador_probable_local}-{marcador_probable_visitante}",
    }


def generar_predicciones():
    """Función principal: genera predicciones para todos los partidos del Mundial."""
    
    print("=" * 60)
    print("GENERANDO PREDICCIONES CON MODELO POISSON")
    print("=" * 60)
    
    # Verificar archivos necesarios
    for archivo in [ARCHIVO_ESTADISTICAS, ARCHIVO_ELO]:
        if not os.path.exists(archivo):
            print(f"❌ No se encontró: {archivo}")
            print("   Ejecuta primero los scripts anteriores")
            return None
    
    # Cargar estadísticas
    df_stats = pd.read_csv(ARCHIVO_ESTADISTICAS)
    df_elo = pd.read_csv(ARCHIVO_ELO)
    
    # Calcular promedio global de goles por partido
    promedio_global = df_stats['lambda_ataque'].mean()
    print(f"\n📊 Promedio global de goles por partido: {promedio_global:.4f}")
    
    # Crear diccionarios para acceso rápido: nombre → estadísticas
    stats_dict = {row['seleccion']: row.to_dict() for _, row in df_stats.iterrows()}
    elo_dict = {row['seleccion']: row['elo'] for _, row in df_elo.iterrows()}
    
    print(f"\n⚙️  Prediciendo {len(PARTIDOS_MUNDIAL)} partidos...")
    
    predicciones = []
    for partido in PARTIDOS_MUNDIAL:
        local = partido['local']
        visitante = partido['visitante']
        
        # Verificar que tenemos datos de ambos equipos
        if local not in stats_dict or visitante not in stats_dict:
            print(f"  ⚠ Sin datos para: {local} vs {visitante}")
            continue
        
        pred = predecir_partido(
            stats_dict[local],
            stats_dict[visitante],
            promedio_global
        )
        
        predicciones.append({
            'id': partido['id'],
            'fecha': partido['fecha'],
            'grupo': partido['grupo'],
            'local': local,
            'visitante': visitante,
            'elo_local': elo_dict.get(local, 1000),
            'elo_visitante': elo_dict.get(visitante, 1000),
            **pred  # Agregar todas las predicciones del partido
        })
        
        print(f"  {local} vs {visitante}: {pred['prob_local']}% / {pred['prob_empate']}% / {pred['prob_visitante']}% | {pred['marcador_probable']}")
    
    # Guardar
    df_pred = pd.DataFrame(predicciones)
    df_pred.to_csv(ARCHIVO_PREDICCIONES, index=False, encoding='utf-8')
    
    print(f"\n✅ Predicciones guardadas en: {ARCHIVO_PREDICCIONES}")
    return df_pred


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    generar_predicciones()