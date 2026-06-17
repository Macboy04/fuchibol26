"""
generar_json.py
---------------
RESPONSABILIDAD: Convertir los datos procesados (CSV) en archivos JSON
                 que la pagina web pueda consumir directamente.

POR QUE JSON Y NO CSV?
  - Los navegadores web NO pueden leer archivos CSV directamente
  - JSON es el formato nativo de JavaScript
  - Es mas facil de usar en HTML/JS
  - Permite estructuras de datos mas complejas

Archivos que genera:
  web/data/ranking_elo.json      -> Ranking ELO de las 48 selecciones
  web/data/estadisticas.json     -> Estadisticas historicas
  web/data/predicciones.json     -> Probabilidades por partido (Poisson)
  web/data/simulacion.json       -> Probabilidades de ser campeon
  web/data/elo_history.json      -> Historial ELO por seleccion y anio
  web/data/metadata.json         -> Fecha de ultima actualizacion
"""

import os
import json
import pandas as pd
from datetime import datetime

# -- CONFIGURACION -----------------------------------------------------------

RUTA_BASE = os.path.join(os.path.dirname(__file__), "..")
RUTA_PROCESADOS = os.path.join(RUTA_BASE, "datos", "procesados")
RUTA_WEB_DATA = os.path.join(RUTA_BASE, "web", "data")

# Archivos de entrada (CSV)
ARCHIVOS_ENTRADA = {
    'elo': os.path.join(RUTA_PROCESADOS, "ranking_elo.csv"),
    'estadisticas': os.path.join(RUTA_PROCESADOS, "estadisticas.csv"),
    'predicciones': os.path.join(RUTA_PROCESADOS, "predicciones.csv"),
    'simulacion': os.path.join(RUTA_PROCESADOS, "simulacion_mundial.csv"),
    'elo_history': os.path.join(RUTA_PROCESADOS, "elo_history.csv"),
}

# Archivos de salida (JSON)
ARCHIVOS_SALIDA = {
    'elo': os.path.join(RUTA_WEB_DATA, "ranking_elo.json"),
    'estadisticas': os.path.join(RUTA_WEB_DATA, "estadisticas.json"),
    'predicciones': os.path.join(RUTA_WEB_DATA, "predicciones.json"),
    'simulacion': os.path.join(RUTA_WEB_DATA, "simulacion.json"),
    'elo_history': os.path.join(RUTA_WEB_DATA, "elo_history.json"),
    'metadata': os.path.join(RUTA_WEB_DATA, "metadata.json"),
}


# -- FUNCIONES ---------------------------------------------------------------

def csv_a_json(archivo_csv, archivo_json, nombre):
    """
    Convierte un archivo CSV a JSON y lo guarda.

    Args:
        archivo_csv (str): Ruta del CSV de entrada
        archivo_json (str): Ruta del JSON de salida
        nombre (str): Nombre para mostrar en mensajes
    """
    if not os.path.exists(archivo_csv):
        print(f"  ⚠  No existe {archivo_csv} → se omite {nombre}")
        return False

    df = pd.read_csv(archivo_csv)

    if df.empty:
        print(f"  ⚠  {archivo_csv} esta vacio → se omite {nombre}")
        return False

    # orient='records' -> convierte cada fila a un objeto JSON
    # Ejemplo: [{"seleccion": "Spain", "elo": 1457}, {"seleccion": "France", ...}]
    datos = df.to_dict(orient='records')

    # Guardar como JSON con formato legible (indent=2 -> sangria de 2 espacios)
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"  ✔ {nombre}: {len(datos)} registros → {os.path.basename(archivo_json)}")
    return True


def generar_json():
    """Funcion principal: convierte todos los CSV a JSON."""

    print("=" * 60)
    print("GENERANDO ARCHIVOS JSON PARA LA WEB")
    print("=" * 60)

    # Crear carpeta de destino si no existe
    os.makedirs(RUTA_WEB_DATA, exist_ok=True)
    print(f"\nCarpeta de destino: {RUTA_WEB_DATA}\n")

    # Convertir cada archivo
    csv_a_json(ARCHIVOS_ENTRADA['elo'], ARCHIVOS_SALIDA['elo'], "Ranking ELO")
    csv_a_json(ARCHIVOS_ENTRADA['estadisticas'], ARCHIVOS_SALIDA['estadisticas'], "Estadisticas")
    csv_a_json(ARCHIVOS_ENTRADA['predicciones'], ARCHIVOS_SALIDA['predicciones'], "Predicciones Poisson")
    csv_a_json(ARCHIVOS_ENTRADA['simulacion'], ARCHIVOS_SALIDA['simulacion'], "Simulacion Mundial")
    csv_a_json(ARCHIVOS_ENTRADA['elo_history'], ARCHIVOS_SALIDA['elo_history'], "Historial ELO")

    # Generar metadata con la fecha y hora de la ultima actualizacion
    metadata = {
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ultima_actualizacion_legible": datetime.now().strftime("%d de %B de %Y, %H:%M"),
        "version": "1.0.0",
        "descripcion": "Fuchibol26 - Sistema de prediccion del Mundial 2026"
    }

    with open(ARCHIVOS_SALIDA['metadata'], 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  ✔ Metadata: fecha de actualizacion guardada")

    print(f"\nArchivos JSON generados en: {RUTA_WEB_DATA}")
    print("   La pagina web ya puede leer los datos actualizados")


# -- PUNTO DE ENTRADA --------------------------------------------------------
if __name__ == "__main__":
    generar_json()
