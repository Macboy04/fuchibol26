"""
generar_estadisticas.py
-----------------------
RESPONSABILIDAD: Calcular estadísticas históricas por selección nacional.

Qué calcula:
- Partidos jugados, ganados, empatados, perdidos
- Goles a favor y en contra
- % de victorias
- Promedio de goles por partido (necesario para el modelo Poisson)

Guarda el resultado en: datos/procesados/estadisticas.csv

CONCEPTO CLAVE - Promedio de goles (λ = lambda):
  El modelo Poisson necesita saber cuántos goles mete un equipo en promedio.
  Este promedio se llama "lambda" y se calcula como:
    lambda = total_goles / total_partidos
  
  Ejemplo: Si Brasil metió 180 goles en 60 partidos:
    lambda_brasil = 180 / 60 = 3.0 goles por partido
"""

# ── IMPORTACIONES ──────────────────────────────────────────────────────────────
import os
import pandas as pd
import numpy as np

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

# Rutas de archivos
RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
ARCHIVO_HISTORICOS = os.path.join(RUTA_BASE, "datos", "historicos", "resultados.csv")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
ARCHIVO_ESTADISTICAS = os.path.join(RUTA_PROCESADOS, "estadisticas.csv")

# Solo usar partidos desde este año para que los datos sean más relevantes
# Usar todo el histórico puede perjudicar a equipos que mejoraron mucho
ANNO_MINIMO = 2010

# Lista de las 48 selecciones clasificadas al Mundial 2026
# (usamos los nombres exactos del dataset de martj42)
SELECCIONES_MUNDIAL = [
    "United States", "Canada", "Mexico",
    "Argentina", "Brazil", "Uruguay", "Colombia", "Ecuador", "Venezuela",
    "Chile", "Peru", "Bolivia",
    "Spain", "France", "England", "Germany", "Portugal", "Netherlands",
    "Belgium", "Italy", "Switzerland", "Denmark", "Sweden", "Turkey",
    "Romania", "Greece", "Czech Republic", "Azerbaijan",
    "Morocco", "Senegal", "Ivory Coast", "South Africa", "Ghana",
    "Cameroon", "Nigeria", "Algeria",
    "Japan", "South Korea", "Iran", "Australia", "Saudi Arabia",
    "Uzbekistan", "Iraq", "Jordan", "Kuwait", "New Zealand",
    "Panama", "Guatemala",
]


# ── FUNCIONES ─────────────────────────────────────────────────────────────────

def calcular_estadisticas_seleccion(df, seleccion):
    """
    Calcula las estadísticas históricas de UNA selección.
    
    Explicación de cómo funciona el dataset:
    - Cada fila es un partido
    - 'home_team' = equipo local, 'away_team' = equipo visitante
    - 'home_score' = goles local, 'away_score' = goles visitante
    
    Para calcular las estadísticas de un equipo, necesitamos buscar
    en AMBAS columnas (local Y visitante).
    
    Args:
        df (pd.DataFrame): Dataset completo de partidos
        seleccion (str): Nombre del equipo a calcular
    
    Returns:
        dict: Diccionario con todas las estadísticas
    """
    
    # Filtrar partidos donde este equipo jugó como LOCAL
    como_local = df[df['home_team'] == seleccion].copy()
    
    # Filtrar partidos donde este equipo jugó como VISITANTE
    como_visita = df[df['away_team'] == seleccion].copy()
    
    # Total de partidos jugados
    total_partidos = len(como_local) + len(como_visita)
    
    # Si el equipo no tiene datos, devolver estadísticas en cero
    if total_partidos == 0:
        return {
            'seleccion': seleccion,
            'partidos': 0,
            'ganados': 0,
            'empatados': 0,
            'perdidos': 0,
            'goles_favor': 0,
            'goles_contra': 0,
            'victorias_pct': 0.0,
            'lambda_ataque': 1.0,   # valor por defecto
            'lambda_defensa': 1.0,  # valor por defecto
        }
    
    # ── CALCULAR VICTORIAS, EMPATES, DERROTAS ─────────────────────────────────
    
    # Cuando jugó como local:
    # Victoria = sus goles (home_score) > goles rival (away_score)
    ganados_local = (como_local['home_score'] > como_local['away_score']).sum()
    empatados_local = (como_local['home_score'] == como_local['away_score']).sum()
    perdidos_local = (como_local['home_score'] < como_local['away_score']).sum()
    
    # Cuando jugó como visitante (la lógica se invierte):
    # Victoria = sus goles (away_score) > goles rival (home_score)
    ganados_visita = (como_visita['away_score'] > como_visita['home_score']).sum()
    empatados_visita = (como_visita['away_score'] == como_visita['home_score']).sum()
    perdidos_visita = (como_visita['away_score'] < como_visita['home_score']).sum()
    
    total_ganados = ganados_local + ganados_visita
    total_empatados = empatados_local + empatados_visita
    total_perdidos = perdidos_local + perdidos_visita
    
    # ── CALCULAR GOLES ────────────────────────────────────────────────────────
    
    # Goles a FAVOR: los que metió el equipo
    goles_favor_local = como_local['home_score'].sum()    # goles cuando fue local
    goles_favor_visita = como_visita['away_score'].sum()  # goles cuando fue visitante
    total_goles_favor = goles_favor_local + goles_favor_visita
    
    # Goles en CONTRA: los que le metieron al equipo
    goles_contra_local = como_local['away_score'].sum()   # rival le metió siendo local
    goles_contra_visita = como_visita['home_score'].sum() # rival le metió siendo visitante
    total_goles_contra = goles_contra_local + goles_contra_visita
    
    # ── CALCULAR MÉTRICAS PARA POISSON ───────────────────────────────────────
    
    # lambda_ataque: promedio de goles que METE por partido
    # (cuántos goles se esperan que meta en el próximo partido)
    lambda_ataque = round(total_goles_favor / total_partidos, 4)
    
    # lambda_defensa: promedio de goles que RECIBE por partido
    # (cuántos goles se esperan que le metan en el próximo partido)
    lambda_defensa = round(total_goles_contra / total_partidos, 4)
    
    # Porcentaje de victorias (0 a 100)
    victorias_pct = round(total_ganados / total_partidos * 100, 2)
    
    return {
        'seleccion': seleccion,
        'partidos': total_partidos,
        'ganados': int(total_ganados),
        'empatados': int(total_empatados),
        'perdidos': int(total_perdidos),
        'goles_favor': int(total_goles_favor),
        'goles_contra': int(total_goles_contra),
        'victorias_pct': victorias_pct,
        'lambda_ataque': lambda_ataque,
        'lambda_defensa': lambda_defensa,
    }


def generar_estadisticas():
    """
    Función principal: lee los datos históricos y calcula estadísticas
    para todas las selecciones del Mundial 2026.
    """
    
    print("=" * 60)
    print("GENERANDO ESTADÍSTICAS POR SELECCIÓN")
    print("=" * 60)
    
    # Paso 1: Verificar que existen los datos históricos
    if not os.path.exists(ARCHIVO_HISTORICOS):
        print(f"❌ No se encontró el archivo: {ARCHIVO_HISTORICOS}")
        print("   Ejecuta primero: python scripts/actualizar_datos.py")
        return None
    
    # Paso 2: Cargar los datos
    print(f"\n📂 Cargando datos desde: {ARCHIVO_HISTORICOS}")
    df = pd.read_csv(ARCHIVO_HISTORICOS)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"  Total de partidos en el dataset: {len(df):,}")
    
    # Paso 3: Filtrar solo partidos desde ANNO_MINIMO
    # Así los datos reflejan el nivel actual de los equipos
    df = df[df['date'].dt.year >= ANNO_MINIMO].copy()
    print(f"  Partidos desde {ANNO_MINIMO}: {len(df):,}")
    
    # Paso 4: Calcular estadísticas para cada selección
    print(f"\n⚙️  Calculando estadísticas para {len(SELECCIONES_MUNDIAL)} selecciones...")
    
    lista_estadisticas = []
    for seleccion in SELECCIONES_MUNDIAL:
        stats = calcular_estadisticas_seleccion(df, seleccion)
        lista_estadisticas.append(stats)
    
    # Paso 5: Convertir lista de diccionarios a DataFrame de pandas
    df_stats = pd.DataFrame(lista_estadisticas)
    
    # Ordenar por % de victorias (mayor primero)
    df_stats = df_stats.sort_values('victorias_pct', ascending=False).reset_index(drop=True)
    
    # Paso 6: Guardar en CSV
    os.makedirs(RUTA_PROCESADOS, exist_ok=True)
    df_stats.to_csv(ARCHIVO_ESTADISTICAS, index=False, encoding='utf-8')
    
    print(f"\n📊 RESUMEN:")
    print(df_stats[['seleccion', 'partidos', 'victorias_pct', 'lambda_ataque']].head(10).to_string(index=False))
    
    print(f"\n✅ Estadísticas guardadas en: {ARCHIVO_ESTADISTICAS}")
    return df_stats


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    generar_estadisticas()