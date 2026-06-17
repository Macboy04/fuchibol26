"""
generar_elo_history.py
----------------------
RESPONSABILIDAD: Generar el historial de ELO por seleccion y anio.

Lee: datos/historicos/resultados.csv
Guarda: datos/procesados/elo_history.csv
Columnas: seleccion, anio, elo
"""

import os
import pandas as pd
from collections import defaultdict

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────

RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
ARCHIVO_HISTORICOS = os.path.join(RUTA_BASE, "datos", "historicos", "resultados.csv")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
ARCHIVO_SALIDA = os.path.join(RUTA_PROCESADOS, "elo_history.csv")

# Mismos parámetros que generar_elo.py para consistencia
ELO_INICIAL = 1000
K_FACTOR = 30
ANNO_INICIO = 2000


# ── FUNCIONES ──────────────────────────────────────────────────────────────

def calcular_resultado_esperado(elo_local, elo_visitante):
    return 1 / (1 + 10 ** ((elo_visitante - elo_local) / 400))


def actualizar_elo(elo_local, elo_visitante, goles_local, goles_visitante, k=K_FACTOR):
    if goles_local > goles_visitante:
        resultado_real_local = 1.0
    elif goles_local == goles_visitante:
        resultado_real_local = 0.5
    else:
        resultado_real_local = 0.0

    resultado_real_visitante = 1.0 - resultado_real_local
    esperado_local = calcular_resultado_esperado(elo_local, elo_visitante)
    esperado_visitante = 1.0 - esperado_local

    nuevo_elo_local = elo_local + k * (resultado_real_local - esperado_local)
    nuevo_elo_visitante = elo_visitante + k * (resultado_real_visitante - esperado_visitante)

    return round(nuevo_elo_local, 2), round(nuevo_elo_visitante, 2)


def generar_elo_history():
    """
    Función principal: recorre resultados.csv partido a partido,
    acumula el ELO de cada selección y toma un snapshot al final
    de cada año. Guarda elo_history.csv con columnas:
    seleccion, anio, elo
    """

    print("=" * 60)
    print("GENERANDO HISTORIAL ELO POR AÑO")
    print("=" * 60)

    if not os.path.exists(ARCHIVO_HISTORICOS):
        print(f"  ✗ No existe {ARCHIVO_HISTORICOS}")
        return

    df = pd.read_csv(ARCHIVO_HISTORICOS)
    df['date'] = pd.to_datetime(df['date'])
    df['anio'] = df['date'].dt.year
    df = df[df['anio'] >= ANNO_INICIO].sort_values('date').reset_index(drop=True)

    elo = defaultdict(lambda: ELO_INICIAL)
    filas = []
    anio_actual = df['anio'].iloc[0]

    for _, fila in df.iterrows():
        # Snapshot al cambiar de año
        if fila['anio'] != anio_actual:
            for seleccion, puntos in elo.items():
                filas.append({'seleccion': seleccion, 'anio': anio_actual, 'elo': round(puntos, 2)})
            anio_actual = fila['anio']

        local = fila['home_team']
        visitante = fila['away_team']
        elo[local], elo[visitante] = actualizar_elo(
            elo[local], elo[visitante],
            fila['home_score'], fila['away_score']
        )

    # Snapshot del último año
    for seleccion, puntos in elo.items():
        filas.append({'seleccion': seleccion, 'anio': anio_actual, 'elo': round(puntos, 2)})

    df_history = pd.DataFrame(filas, columns=['seleccion', 'anio', 'elo'])
    df_history = df_history.sort_values(['seleccion', 'anio']).reset_index(drop=True)

    os.makedirs(RUTA_PROCESADOS, exist_ok=True)
    df_history.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8')

    print(f"  ✔ {len(df_history)} registros → {os.path.basename(ARCHIVO_SALIDA)}")
    print(f"  Años: {df_history['anio'].min()} – {df_history['anio'].max()}")
    print(f"  Selecciones: {df_history['seleccion'].nunique()}")
    print(f"\n✅ Historial ELO guardado en: {ARCHIVO_SALIDA}")
    return df_history


# ── PUNTO DE ENTRADA ────────────────────────────────────────────────────────
if __name__ == "__main__":
    generar_elo_history()