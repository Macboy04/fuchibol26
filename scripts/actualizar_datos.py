"""
actualizar_datos.py
-------------------
RESPONSABILIDAD: Descargar y guardar datos históricos de fútbol internacional.

Fuente: martj42/international_results en GitHub
        (dataset público con +47,000 partidos desde 1872 hasta hoy)

Qué hace este archivo:
1. Descarga el CSV de resultados históricos desde GitHub
2. Lo guarda en datos/historicos/resultados.csv
3. Muestra un resumen de los datos descargados

AUTOR: Fuchibol26
FECHA: 2026
"""

# ── IMPORTACIONES ──────────────────────────────────────────────────────────────
import os          # Para crear carpetas si no existen
import requests    # Para hacer peticiones HTTP (descargar archivos)
import pandas as pd  # Para leer y manipular datos tabulares

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

# URL del dataset público de resultados históricos de fútbol
# Este repositorio tiene datos desde 1872 hasta la fecha actual
URL_DATOS = (
    "https://raw.githubusercontent.com/martj42/international_results"
    "/master/results.csv"
)

# Ruta donde guardaremos el archivo descargado
# os.path.dirname(__file__) → carpeta donde está este script (scripts/)
# .. → subir un nivel (Fuchibol26/)
# datos/historicos → carpeta de destino
RUTA_HISTORICOS = os.path.join(
    os.path.dirname(__file__), "..", "datos", "historicos"
)

ARCHIVO_DESTINO = os.path.join(RUTA_HISTORICOS, "resultados.csv")


# ── FUNCIÓN PRINCIPAL ──────────────────────────────────────────────────────────

def descargar_datos():
    """
    Descarga el CSV de resultados históricos y lo guarda localmente.
    
    Returns:
        pd.DataFrame: Los datos descargados como tabla de pandas
        None: Si hubo un error
    """
    
    print("=" * 60)
    print("ACTUALIZANDO DATOS HISTÓRICOS")
    print("=" * 60)
    
    # Paso 1: Crear la carpeta si no existe
    # exist_ok=True → no da error si la carpeta ya existe
    os.makedirs(RUTA_HISTORICOS, exist_ok=True)
    print(f"✓ Carpeta lista: {RUTA_HISTORICOS}")
    
    # Paso 2: Descargar el archivo
    print(f"\n⬇ Descargando datos desde GitHub...")
    print(f"  URL: {URL_DATOS}")
    
    try:
        # timeout=30 → espera máximo 30 segundos antes de cancelar
        respuesta = requests.get(URL_DATOS, timeout=30)
        
        # raise_for_status() → lanza error si el servidor devolvió error (404, 500, etc.)
        respuesta.raise_for_status()
        
        # Paso 3: Guardar el contenido en disco
        # "w" → modo escritura
        # encoding="utf-8" → para manejar caracteres especiales (tildes, ñ, etc.)
        with open(ARCHIVO_DESTINO, "w", encoding="utf-8") as archivo:
            archivo.write(respuesta.text)
        
        print(f"✓ Datos guardados en: {ARCHIVO_DESTINO}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No hay conexión a internet")
        return None
    except requests.exceptions.Timeout:
        print("❌ Error: La descarga tardó demasiado (timeout)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        return None
    
    # Paso 4: Leer los datos y mostrar un resumen
    df = pd.read_csv(ARCHIVO_DESTINO)
    
    print("\n📊 RESUMEN DE DATOS DESCARGADOS:")
    print(f"  Total de partidos: {len(df):,}")
    print(f"  Primer partido: {df['date'].min()}")
    print(f"  Último partido: {df['date'].max()}")
    print(f"  Columnas: {list(df.columns)}")
    
    # Contar partidos de los últimos 5 años para verificar actualidad
    df['date'] = pd.to_datetime(df['date'])
    recientes = df[df['date'].dt.year >= 2020]
    print(f"  Partidos desde 2020: {len(recientes):,}")
    
    print("\n✅ Datos históricos actualizados correctamente")
    return df


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
# Este bloque solo se ejecuta cuando corres el archivo directamente:
#   python scripts/actualizar_datos.py
# No se ejecuta si otro script importa este archivo como módulo

if __name__ == "__main__":
    descargar_datos()