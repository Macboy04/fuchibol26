"""
ejecutar_todo.py
----------------
RESPONSABILIDAD: Script maestro que ejecuta TODO el flujo de Fuchibol26.

FLUJO COMPLETO:
  1. Descargar datos historicos (actualizar_datos.py)
  2. Calcular estadisticas por seleccion (generar_estadisticas.py)
  3. Calcular ranking ELO (generar_elo.py)
  3b. Generar historial ELO por anio (generar_elo_history.py)
  4. Generar predicciones Poisson (generar_poisson.py)
  5. Simular el Mundial completo (simular_mundial.py)
  6. Generar archivos JSON para la web (generar_json.py)

COMO USARLO:
  python scripts/ejecutar_todo.py

  Opciones:
  python scripts/ejecutar_todo.py --sin-descarga   -> salta el paso 1 (mas rapido)
  python scripts/ejecutar_todo.py --solo-json      -> solo regenera los JSON
"""

import sys
import os
import time

# Agregar la carpeta scripts al path para poder importar los modulos
sys.path.insert(0, os.path.dirname(__file__))

# Importar las funciones principales de cada modulo
from actualizar_datos import descargar_datos
from generar_estadisticas import generar_estadisticas
from generar_elo import generar_elo
from generar_elo_history import generar_elo_history
from generar_poisson import generar_predicciones
from simular_mundial import simular_mundial_n_veces
from generar_json import generar_json


def ejecutar_paso(numero, nombre, funcion):
    """
    Ejecuta un paso del flujo con manejo de errores.

    El exito se determina por la ausencia de excepcion, no por el valor
    de retorno. Esto permite que funciones que retornan None (sin return
    explicito) sean correctamente marcadas como exitosas.

    Args:
        numero: Numero del paso (int o str como '3b')
        nombre (str): Descripcion del paso
        funcion: La funcion a ejecutar

    Returns:
        bool: True si tuvo exito, False si hubo error
    """
    print(f"\n{'=' * 60}")
    print(f"PASO {numero}: {nombre}")
    print('=' * 60)

    inicio = time.time()

    try:
        funcion()
        tiempo = round(time.time() - inicio, 2)
        print(f"\nPaso {numero} completado en {tiempo}s")
        return True

    except Exception as error:
        tiempo = round(time.time() - inicio, 2)
        print(f"\nERROR en paso {numero} ({tiempo}s): {error}")
        return False


def main():
    print("=" * 30)
    print("    FUCHIBOL26 - SISTEMA DE PREDICCION MUNDIAL 2026")
    print("=" * 30)

    inicio_total = time.time()

    # Leer argumentos de linea de comandos
    args = sys.argv[1:]
    sin_descarga = '--sin-descarga' in args
    solo_json = '--solo-json' in args

    resultados = {}

    if solo_json:
        # Solo regenerar los JSON sin recalcular nada
        print("\nModo: Solo JSON (regenerando archivos web)")
        resultados[6] = ejecutar_paso(6, "Generar JSON para la web", generar_json)

    else:
        # Flujo completo

        # Paso 1: Descargar datos (opcional)
        if not sin_descarga:
            resultados[1] = ejecutar_paso(1, "Actualizar datos historicos", descargar_datos)
        else:
            print("\nPaso 1 omitido (--sin-descarga)")
            resultados[1] = True

        # Paso 2: Estadisticas
        resultados[2] = ejecutar_paso(2, "Calcular estadisticas por seleccion", generar_estadisticas)

        # Paso 3: ELO
        resultados[3] = ejecutar_paso(3, "Calcular ranking ELO", generar_elo)

        # Paso 3b: Historial ELO
        resultados['3b'] = ejecutar_paso('3b', "Generar historial ELO por anio", generar_elo_history)

        # Paso 4: Predicciones Poisson
        resultados[4] = ejecutar_paso(4, "Generar predicciones Poisson", generar_predicciones)

        # Paso 5: Simular Mundial
        resultados[5] = ejecutar_paso(5, "Simular Mundial 2026 (1000 veces)", simular_mundial_n_veces)

        # Paso 6: Generar JSON
        resultados[6] = ejecutar_paso(6, "Generar JSON para la web", generar_json)

    # -- RESUMEN FINAL -------------------------------------------------------
    tiempo_total = round(time.time() - inicio_total, 2)

    print(f"\n{'=' * 60}")
    print("RESUMEN DE EJECUCION")
    print('=' * 60)

    exitosos = sum(1 for v in resultados.values() if v)
    totales = len(resultados)

    for paso, exito in resultados.items():
        estado = "OK" if exito else "ERROR"
        print(f"  Paso {paso}: {estado}")

    print(f"\n{exitosos}/{totales} pasos exitosos — {tiempo_total}s total")

    if exitosos == totales:
        print("\nFuchibol26 actualizado correctamente.")
    else:
        print("\nAlgunos pasos fallaron. Revisa los mensajes de error arriba.")


# -- PUNTO DE ENTRADA --------------------------------------------------------
if __name__ == "__main__":
    main()
