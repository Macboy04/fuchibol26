# =============================================================
# FUCHIBOL26 - Script 01: Descarga de Datos Históricos
# =============================================================
# ¿Qué hace este script?
# Descarga dos archivos CSV con datos históricos de fútbol
# internacional y los guarda en la carpeta datos/historicos/
# =============================================================

import pandas as pd      # Para manejar tablas de datos
import requests          # Para descargar archivos de internet
import os               # Para manejar carpetas y archivos

# ----------------------------------------------------------
# PASO 1: Definir las URLs de los datos
# ----------------------------------------------------------
# Estas URLs apuntan a archivos CSV en GitHub con datos
# de partidos internacionales de fútbol

URL_RESULTADOS = (
    "https://raw.githubusercontent.com/"
    "martj42/international_results/master/results.csv"
)

URL_GOLEADORES = (
    "https://raw.githubusercontent.com/"
    "martj42/international_results/master/goalscorers.csv"
)

# ----------------------------------------------------------
# PASO 2: Definir dónde guardar los archivos
# ----------------------------------------------------------
# os.path.dirname(__file__) obtiene la carpeta del script actual
# Luego navegamos hacia arriba y entramos a datos/historicos/

CARPETA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_SCRIPTS)
CARPETA_DESTINO = os.path.join(CARPETA_PROYECTO, "datos", "historicos")

# ----------------------------------------------------------
# PASO 3: Crear la carpeta si no existe
# ----------------------------------------------------------
os.makedirs(CARPETA_DESTINO, exist_ok=True)
print(f"📁 Carpeta de destino: {CARPETA_DESTINO}")

# ----------------------------------------------------------
# PASO 4: Función para descargar un archivo
# ----------------------------------------------------------
def descargar_archivo(url, nombre_archivo):
    """
    Descarga un archivo de internet y lo guarda localmente.
    
    Parámetros:
        url: dirección web del archivo
        nombre_archivo: nombre con el que se guardará
    """
    print(f"\n⬇️  Descargando {nombre_archivo}...")
    
    try:
        # Hacemos la solicitud al servidor
        respuesta = requests.get(url, timeout=30)
        
        # Verificamos que la descarga fue exitosa (código 200 = OK)
        respuesta.raise_for_status()
        
        # Construimos la ruta completa donde guardaremos el archivo
        ruta_completa = os.path.join(CARPETA_DESTINO, nombre_archivo)
        
        # Guardamos el contenido en el archivo
        with open(ruta_completa, "wb") as archivo:
            archivo.write(respuesta.content)
        
        print(f"✅ Guardado en: {ruta_completa}")
        return ruta_completa
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: No hay conexión a internet.")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Error: La descarga tardó demasiado.")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

# ----------------------------------------------------------
# PASO 5: Descargar los archivos
# ----------------------------------------------------------
ruta_resultados = descargar_archivo(URL_RESULTADOS, "resultados.csv")
ruta_goleadores = descargar_archivo(URL_GOLEADORES, "goleadores.csv")

# ----------------------------------------------------------
# PASO 6: Verificar y mostrar un resumen de los datos
# ----------------------------------------------------------
if ruta_resultados:
    print("\n" + "="*50)
    print("📊 RESUMEN DEL ARCHIVO: resultados.csv")
    print("="*50)
    
    # Cargamos el CSV en un DataFrame (tabla de datos)
    df_resultados = pd.read_csv(ruta_resultados)
    
    # Mostramos información básica
    print(f"Total de partidos: {len(df_resultados):,}")
    print(f"Columnas disponibles: {list(df_resultados.columns)}")
    print(f"Rango de fechas: {df_resultados['date'].min()} → {df_resultados['date'].max()}")
    
    print("\n📋 Primeras 5 filas:")
    print(df_resultados.head())

if ruta_goleadores:
    print("\n" + "="*50)
    print("📊 RESUMEN DEL ARCHIVO: goleadores.csv")
    print("="*50)
    
    df_goleadores = pd.read_csv(ruta_goleadores)
    
    print(f"Total de registros de goles: {len(df_goleadores):,}")
    print(f"Columnas disponibles: {list(df_goleadores.columns)}")
    
    print("\n📋 Primeras 5 filas:")
    print(df_goleadores.head())

print("\n🎉 ¡Descarga completada con éxito!")
print("Los archivos están listos en: datos/historicos/")