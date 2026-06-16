"""
generar_elo.py
--------------
RESPONSABILIDAD: Calcular el ranking ELO de todas las selecciones.

¿QUÉ ES ELO?
  ELO es un sistema de puntuación que mide la fortaleza relativa de un equipo.
  Fue creado por Arpad Elo para el ajedrez y se adapta perfectamente al fútbol.
  
  IDEA BÁSICA:
  - Cada equipo empieza con 1000 puntos
  - Ganar contra un rival fuerte → ganas MUCHOS puntos
  - Ganar contra un rival débil  → ganas POCOS puntos
  - Perder contra un rival fuerte → pierdes POCOS puntos
  - Perder contra un rival débil  → pierdes MUCHOS puntos
  
  FÓRMULA:
  ELO_nuevo = ELO_viejo + K × (Resultado_real - Resultado_esperado)
  
  Donde:
  - K = 30 (factor de ajuste; más grande = cambios más rápidos)
  - Resultado_real: 1 si ganó, 0.5 si empató, 0 si perdió
  - Resultado_esperado = 1 / (1 + 10^((ELO_rival - ELO_propio) / 400))

Guarda el resultado en: datos/procesados/ranking_elo.csv
"""

import os
from collections import defaultdict

import numpy as np
import pandas as pd

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
ARCHIVO_HISTORICOS = os.path.join(RUTA_BASE, "datos", "historicos", "resultados.csv")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
ARCHIVO_ELO = os.path.join(RUTA_PROCESADOS, "ranking_elo.csv")

# Parámetros del modelo ELO
ELO_INICIAL = 1000   # Puntos con los que empieza cada equipo
K_FACTOR = 30        # Qué tan rápido cambia el ELO después de cada partido
ANNO_INICIO = 2000   # Solo usar partidos desde este año

# Confederaciones (para mostrar en la tabla)
CONFEDERACIONES = {
    "United States": "CONCACAF", "Canada": "CONCACAF", "Mexico": "CONCACAF",
    "Panama": "CONCACAF", "Guatemala": "CONCACAF",
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Ecuador": "CONMEBOL", "Venezuela": "CONMEBOL",
    "Chile": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL",
    "Spain": "UEFA", "France": "UEFA", "England": "UEFA", "Germany": "UEFA",
    "Portugal": "UEFA", "Netherlands": "UEFA", "Belgium": "UEFA",
    "Italy": "UEFA", "Switzerland": "UEFA", "Denmark": "UEFA",
    "Sweden": "UEFA", "Turkey": "UEFA", "Romania": "UEFA",
    "Greece": "UEFA", "Czech Republic": "UEFA", "Azerbaijan": "UEFA",
    "Morocco": "CAF", "Senegal": "CAF", "Ivory Coast": "CAF",
    "South Africa": "CAF", "Ghana": "CAF", "Cameroon": "CAF",
    "Nigeria": "CAF", "Algeria": "CAF",
    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC",
    "Australia": "AFC", "Saudi Arabia": "AFC", "Uzbekistan": "AFC",
    "Iraq": "AFC", "Jordan": "AFC", "Kuwait": "AFC", "New Zealand": "OFC",
}

# Banderas emoji para cada selección
BANDERAS = {
    "United States": "🇺🇸", "Canada": "🇨🇦", "Mexico": "🇲🇽",
    "Panama": "🇵🇦", "Guatemala": "🇬🇹",
    "Argentina": "🇦🇷", "Brazil": "🇧🇷", "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴", "Ecuador": "🇪🇨", "Venezuela": "🇻🇪",
    "Chile": "🇨🇱", "Peru": "🇵🇪", "Bolivia": "🇧🇴",
    "Spain": "🇪🇸", "France": "🇫🇷", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Germany": "🇩🇪",
    "Portugal": "🇵🇹", "Netherlands": "🇳🇱", "Belgium": "🇧🇪",
    "Switzerland": "🇨🇭", "Denmark": "🇩🇰", "Sweden": "🇸🇪",
    "Turkey": "🇹🇷", "Romania": "🇷🇴", "Greece": "🇬🇷",
    "Czech Republic": "🇨🇿", "Azerbaijan": "🇦🇿",
    "Morocco": "🇲🇦", "Senegal": "🇸🇳", "Ivory Coast": "🇨🇮",
    "South Africa": "🇿🇦", "Ghana": "🇬🇭", "Cameroon": "🇨🇲",
    "Nigeria": "🇳🇬", "Algeria": "🇩🇿",
    "Japan": "🇯🇵", "South Korea": "🇰🇷", "Iran": "🇮🇷",
    "Australia": "🇦🇺", "Saudi Arabia": "🇸🇦", "Uzbekistan": "🇺🇿",
    "Iraq": "🇮🇶", "Jordan": "🇯🇴", "Kuwait": "🇰🇼", "New Zealand": "🇳🇿",
}


# ── FUNCIONES ─────────────────────────────────────────────────────────────────

def calcular_resultado_esperado(elo_local, elo_visitante):
    """
    Calcula la probabilidad de que el equipo local gane según ELO.
    
    Fórmula: 1 / (1 + 10^((ELO_rival - ELO_propio) / 400))
    
    Ejemplos:
    - ELO_local=1500, ELO_visitante=1000 → esperado=0.97 (97% de ganar)
    - ELO_local=1000, ELO_visitante=1000 → esperado=0.50 (50/50)
    - ELO_local=1000, ELO_visitante=1500 → esperado=0.03 (3% de ganar)
    
    Args:
        elo_local (float): ELO del equipo local
        elo_visitante (float): ELO del equipo visitante
    
    Returns:
        float: Probabilidad de victoria del local (0 a 1)
    """
    return 1 / (1 + 10 ** ((elo_visitante - elo_local) / 400))


def actualizar_elo(elo_local, elo_visitante, goles_local, goles_visitante, k=K_FACTOR):
    """
    Actualiza el ELO de ambos equipos después de un partido.
    
    Args:
        elo_local (float): ELO actual del equipo local
        elo_visitante (float): ELO actual del equipo visitante
        goles_local (int): Goles anotados por el local
        goles_visitante (int): Goles anotados por el visitante
        k (int): Factor de ajuste
    
    Returns:
        tuple: (nuevo_elo_local, nuevo_elo_visitante)
    """
    # Resultado real: 1=victoria local, 0.5=empate, 0=derrota local
    if goles_local > goles_visitante:
        resultado_real_local = 1.0
    elif goles_local == goles_visitante:
        resultado_real_local = 0.5
    else:
        resultado_real_local = 0.0

    # El visitante tiene el resultado complementario
    resultado_real_visitante = 1.0 - resultado_real_local

    # Resultado esperado según ELO
    esperado_local = calcular_resultado_esperado(elo_local, elo_visitante)
    esperado_visitante = 1.0 - esperado_local

    # Actualizar ELO con la fórmula
    nuevo_elo_local = elo_local + k * (resultado_real_local - esperado_local)
    nuevo_elo_visitante = elo_visitante + k * (resultado_real_visitante - esperado_visitante)

    return round(nuevo_elo_local, 2), round(nuevo_elo_visitante, 2)


def generar_elo():
    """
    Función principal: procesa todos los partidos históricos y calcula
    el ELO final de cada selección.
    """

    print("=" * 60)
    print("CALCULANDO RANKING ELO")
    print("=" * 60)

    # Verificar que existen los datos
    if not os.path.exists(ARCHIVO_HISTORICOS):
        print(f"❌ No se encontró: {ARCHIVO_HISTORICOS}")
        print("   Ejecuta primero: python scripts/actualizar_datos.py")
        return None

    # Cargar datos
    print("\n📂 Cargando datos históricos...")
    df = pd.read_csv(ARCHIVO_HISTORICOS)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Descartar filas con fecha inválida
    df = df.dropna(subset=['date'])

    # Filtrar partidos desde ANNO_INICIO
    df = df[df['date'].dt.year >= ANNO_INICIO].copy()
    df = df.sort_values('date').reset_index(drop=True)

    # Eliminar partidos sin resultado (NaN en goles)
    df = df.dropna(subset=['home_score', 'away_score'])

    # Convertir goles a enteros de forma segura (evita ValueError con NaN residuales)
    df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce')
    df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce')
    df = df.dropna(subset=['home_score', 'away_score'])
    df['home_score'] = df['home_score'].astype(int)
    df['away_score'] = df['away_score'].astype(int)

    # Descartar filas con equipos vacíos
    df = df.dropna(subset=['home_team', 'away_team'])
    df = df[df['home_team'].str.strip() != '']
    df = df[df['away_team'].str.strip() != '']

    print(f"  Procesando {len(df):,} partidos desde {ANNO_INICIO}...")

    # Diccionario: nombre_equipo → ELO actual
    # Usamos defaultdict: si un equipo no existe, empieza con ELO_INICIAL
    elos = defaultdict(lambda: float(ELO_INICIAL))

    # Procesar cada partido cronológicamente
    for _, partido in df.iterrows():
        local = partido['home_team']
        visitante = partido['away_team']
        goles_local = partido['home_score']
        goles_visitante = partido['away_score']

        # Actualizar ELO de ambos equipos
        nuevo_local, nuevo_visitante = actualizar_elo(
            elos[local], elos[visitante],
            goles_local, goles_visitante
        )

        elos[local] = nuevo_local
        elos[visitante] = nuevo_visitante

    # Crear DataFrame con los resultados finales
    # Solo incluir selecciones del Mundial 2026
    selecciones_mundial = list(CONFEDERACIONES.keys())

    filas = []
    for seleccion in selecciones_mundial:
        filas.append({
            'seleccion': seleccion,
            'elo': round(elos[seleccion]),
            'confederacion': CONFEDERACIONES.get(seleccion, 'N/A'),
            'bandera': BANDERAS.get(seleccion, '🏳️'),
        })

    df_elo = pd.DataFrame(filas)
    df_elo = df_elo.sort_values('elo', ascending=False).reset_index(drop=True)
    df_elo['posicion'] = df_elo.index + 1

    # Guardar CSV
    os.makedirs(RUTA_PROCESADOS, exist_ok=True)
    df_elo.to_csv(ARCHIVO_ELO, index=False, encoding='utf-8')

    print("\n🏆 TOP 10 ELO:")
    print(df_elo[['posicion', 'seleccion', 'elo', 'confederacion']].head(10).to_string(index=False))

    print(f"\n✅ Ranking ELO guardado en: {ARCHIVO_ELO}")
    return df_elo


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    generar_elo()
