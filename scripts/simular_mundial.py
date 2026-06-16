"""
simular_mundial.py
------------------
RESPONSABILIDAD: Simular el Mundial 2026 completo usando Monte Carlo.

¿QUÉ ES SIMULACIÓN MONTE CARLO?
  En lugar de calcular probabilidades exactas (muy complejo para 48 equipos),
  simulamos el torneo 1000 veces y contamos cuántas veces ganó cada equipo.
  
  Ejemplo: Si simulamos 1000 mundiales y Brasil ganó 150 veces,
           la probabilidad de que Brasil sea campeón ≈ 15%

Proceso:
1. Simular fase de grupos (3 partidos por equipo)
2. Seleccionar los 2 mejores de cada grupo + 8 mejores terceros
3. Simular octavos, cuartos, semis y final
4. Contar cuántas veces ganó cada selección

Guarda en: datos/procesados/simulacion_mundial.csv
"""

import os
import random
import numpy as np
import pandas as pd
from scipy.stats import poisson
from collections import defaultdict

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
ARCHIVO_ESTADISTICAS = os.path.join(RUTA_BASE, "datos", "procesados", "estadisticas.csv")
ARCHIVO_ELO = os.path.join(RUTA_BASE, "datos", "procesados", "ranking_elo.csv")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
ARCHIVO_SIMULACION = os.path.join(RUTA_PROCESADOS, "simulacion_mundial.csv")

# Número de simulaciones (más = más preciso pero más lento)
# 1000 tarda ~10 segundos, 10000 tarda ~2 minutos
N_SIMULACIONES = 1000

# Grupos del Mundial 2026 (12 grupos de 4 equipos)
GRUPOS_MUNDIAL = {
    "A": ["Mexico", "Canada", "United States", "New Zealand"],
    "B": ["Argentina", "Chile", "Australia", "Peru"],
    "C": ["Brazil", "Uruguay", "Panama", "Guatemala"],
    "D": ["England", "France", "Germany", "Switzerland"],
    "E": ["Spain", "Portugal", "Belgium", "Ivory Coast"],
    "F": ["Netherlands", "Turkey", "Senegal", "South Korea"],
    "G": ["Japan", "Iran", "Morocco", "Algeria"],
    "H": ["Colombia", "Ecuador", "Nigeria", "South Africa"],
    "I": ["Ghana", "Cameroon", "Saudi Arabia", "Jordan"],
    "J": ["Uzbekistan", "Iraq", "Romania", "Greece"],
    "K": ["Czech Republic", "Azerbaijan", "Venezuela", "Bolivia"],
    "L": ["Sweden", "Denmark", "Kuwait", "Romania"],
}


# ── FUNCIONES ─────────────────────────────────────────────────────────────────

def simular_partido(lambda_local, lambda_visitante):
    """
    Simula UN partido usando distribución de Poisson.
    
    Toma muestras aleatorias de la distribución de Poisson para
    determinar cuántos goles marca cada equipo.
    
    Args:
        lambda_local (float): Goles esperados del local
        lambda_visitante (float): Goles esperados del visitante
    
    Returns:
        tuple: (goles_local, goles_visitante)
    """
    # np.random.poisson(lam) devuelve un número aleatorio de goles
    # siguiendo la distribución de Poisson con media lam
    goles_local = np.random.poisson(lambda_local)
    goles_visitante = np.random.poisson(lambda_visitante)
    return goles_local, goles_visitante


def obtener_lambdas(equipo1, equipo2, stats_dict, promedio_global):
    """
    Calcula las lambdas de ataque para cada equipo en un partido.
    
    Args:
        equipo1 (str): Nombre del equipo local
        equipo2 (str): Nombre del equipo visitante
        stats_dict (dict): Diccionario de estadísticas
        promedio_global (float): Promedio global de goles
    
    Returns:
        tuple: (lambda_local, lambda_visitante)
    """
    s1 = stats_dict.get(equipo1, {'lambda_ataque': 1.0, 'lambda_defensa': 1.0})
    s2 = stats_dict.get(equipo2, {'lambda_ataque': 1.0, 'lambda_defensa': 1.0})
    
    lambda_local = max(s1['lambda_ataque'] * s2['lambda_defensa'] / promedio_global, 0.1)
    lambda_visitante = max(s2['lambda_ataque'] * s1['lambda_defensa'] / promedio_global, 0.1)
    
    return lambda_local, lambda_visitante


def simular_grupo(equipos, stats_dict, promedio_global):
    """
    Simula la fase de grupos de UN grupo (todos contra todos).
    
    En la fase de grupos, cada equipo juega contra los otros 3.
    Sistema de puntos:
    - Victoria: 3 puntos
    - Empate: 1 punto
    - Derrota: 0 puntos
    
    Args:
        equipos (list): Lista de 4 equipos del grupo
        stats_dict (dict): Estadísticas de todos los equipos
        promedio_global (float): Promedio global
    
    Returns:
        list: Equipos ordenados por puntos (mejor a peor)
    """
    # Tabla de puntos: nombre_equipo → puntos
    puntos = {eq: 0 for eq in equipos}
    goles_favor = {eq: 0 for eq in equipos}
    goles_contra = {eq: 0 for eq in equipos}
    
    # Simular todos los partidos del grupo (6 partidos para 4 equipos)
    for i in range(len(equipos)):
        for j in range(i + 1, len(equipos)):
            local = equipos[i]
            visitante = equipos[j]
            
            lambda_l, lambda_v = obtener_lambdas(local, visitante, stats_dict, promedio_global)
            goles_l, goles_v = simular_partido(lambda_l, lambda_v)
            
            # Acumular goles
            goles_favor[local] += goles_l
            goles_contra[local] += goles_v
            goles_favor[visitante] += goles_v
            goles_contra[visitante] += goles_l
            
            # Asignar puntos
            if goles_l > goles_v:
                puntos[local] += 3
            elif goles_l == goles_v:
                puntos[local] += 1
                puntos[visitante] += 1
            else:
                puntos[visitante] += 3
    
    # Ordenar equipos: primero por puntos, luego por diferencia de goles
    clasificados = sorted(
        equipos,
        key=lambda eq: (puntos[eq], goles_favor[eq] - goles_contra[eq], goles_favor[eq]),
        reverse=True
    )
    
    # Devolver también la tabla para calcular los mejores terceros
    tabla = [{
        'equipo': eq,
        'puntos': puntos[eq],
        'gf': goles_favor[eq],
        'gc': goles_contra[eq],
        'dg': goles_favor[eq] - goles_contra[eq]
    } for eq in clasificados]
    
    return clasificados, tabla


def simular_eliminatoria(equipo1, equipo2, stats_dict, promedio_global):
    """
    Simula un partido de eliminatoria (sin empate, hay penales).
    
    En eliminatorias no hay empate: si el partido termina empatado,
    simulamos penales (50/50 ajustado por ELO).
    
    Args:
        equipo1, equipo2 (str): Nombres de los equipos
        stats_dict (dict): Estadísticas
        promedio_global (float): Promedio global
    
    Returns:
        str: Nombre del equipo ganador
    """
    lambda_1, lambda_2 = obtener_lambdas(equipo1, equipo2, stats_dict, promedio_global)
    goles_1, goles_2 = simular_partido(lambda_1, lambda_2)
    
    if goles_1 > goles_2:
        return equipo1
    elif goles_2 > goles_1:
        return equipo2
    else:
        # Penales: 50/50 (simplificado)
        return random.choice([equipo1, equipo2])


def simular_mundial_completo(stats_dict, promedio_global):
    """
    Simula UN Mundial completo desde grupos hasta la final.
    
    Returns:
        str: Nombre del equipo campeón
    """
    
    # ── FASE DE GRUPOS ────────────────────────────────────────────────────────
    primeros = []    # Primeros de cada grupo (clasificados directos)
    segundos = []    # Segundos de cada grupo (clasificados directos)
    terceros = []    # Terceros (los mejores de estos pasan)
    
    for grupo, equipos in GRUPOS_MUNDIAL.items():
        clasificados, tabla = simular_grupo(equipos, stats_dict, promedio_global)
        primeros.append(clasificados[0])
        segundos.append(clasificados[1])
        terceros.append(tabla[2])  # Tabla del tercer lugar con sus puntos
    
    # Los 8 mejores terceros clasifican (de 12 grupos)
    terceros_ordenados = sorted(
        terceros,
        key=lambda t: (t['puntos'], t['dg'], t['gf']),
        reverse=True
    )
    mejores_terceros = [t['equipo'] for t in terceros_ordenados[:8]]
    
    # ── RONDA DE 32 (simplificada) ────────────────────────────────────────────
    # 24 clasificados directos (12 primeros + 12 segundos) + 8 mejores terceros = 32
    clasificados_eliminatorias = primeros + segundos + mejores_terceros
    
    # Barajar para simplificar los cruces (en la realidad hay un cuadro fijo)
    random.shuffle(clasificados_eliminatorias)
    
    # ── ELIMINATORIAS (32 → 16 → 8 → 4 → 2 → 1) ─────────────────────────────
    ronda_actual = clasificados_eliminatorias
    
    while len(ronda_actual) > 1:
        siguiente_ronda = []
        
        # Emparejar equipos: 1 vs 2, 3 vs 4, etc.
        for i in range(0, len(ronda_actual), 2):
            if i + 1 < len(ronda_actual):
                ganador = simular_eliminatoria(
                    ronda_actual[i], ronda_actual[i + 1],
                    stats_dict, promedio_global
                )
                siguiente_ronda.append(ganador)
        
        ronda_actual = siguiente_ronda
    
    # El último equipo que queda es el campeón
    return ronda_actual[0] if ronda_actual else None


def simular_mundial_n_veces():
    """
    Función principal: simula el Mundial N veces y calcula probabilidades.
    """
    
    print("=" * 60)
    print(f"SIMULANDO MUNDIAL 2026 ({N_SIMULACIONES} veces)")
    print("=" * 60)
    
    # Cargar datos
    if not os.path.exists(ARCHIVO_ESTADISTICAS):
        print(f"❌ No se encontró: {ARCHIVO_ESTADISTICAS}")
        return None
    
    df_stats = pd.read_csv(ARCHIVO_ESTADISTICAS)
    df_elo = pd.read_csv(ARCHIVO_ELO)
    
    # Crear diccionario de estadísticas
    stats_dict = {row['seleccion']: row.to_dict() for _, row in df_stats.iterrows()}
    promedio_global = df_stats['lambda_ataque'].mean()
    
    print(f"\n⚽ Simulando {N_SIMULACIONES} mundiales...")
    
    # Contador de veces que ganó cada equipo
    campeonatos = defaultdict(int)
    
    for i in range(N_SIMULACIONES):
        if i % 100 == 0:
            print(f"  Simulación {i}/{N_SIMULACIONES}...")
        
        campeon = simular_mundial_completo(stats_dict, promedio_global)
        if campeon:
            campeonatos[campeon] += 1
    
    # Calcular probabilidades
    resultados = []
    for equipo, victorias in campeonatos.items():
        resultados.append({
            'seleccion': equipo,
            'victorias': victorias,
            'probabilidad_campeon': round(victorias / N_SIMULACIONES * 100, 2),
        })
    
    df_resultado = pd.DataFrame(resultados)
    df_resultado = df_resultado.sort_values('probabilidad_campeon', ascending=False).reset_index(drop=True)
    
    # Agregar info de ELO y bandera
    elo_dict = {row['seleccion']: row['elo'] for _, row in df_elo.iterrows()}
    bandera_dict = {row['seleccion']: row['bandera'] for _, row in df_elo.iterrows()}
    
    df_resultado['elo'] = df_resultado['seleccion'].map(elo_dict)
    df_resultado['bandera'] = df_resultado['seleccion'].map(bandera_dict).fillna('🏳️')
    
    # Guardar
    os.makedirs(RUTA_PROCESADOS, exist_ok=True)
    df_resultado.to_csv(ARCHIVO_SIMULACION, index=False, encoding='utf-8')
    
    print("\n🏆 TOP 10 FAVORITOS:")
    print(df_resultado[['seleccion', 'probabilidad_campeon', 'elo']].head(10).to_string(index=False))
    
    print(f"\n✅ Simulación guardada en: {ARCHIVO_SIMULACION}")
    return df_resultado


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    simular_mundial_n_veces()
    