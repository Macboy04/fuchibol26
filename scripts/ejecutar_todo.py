"""
ejecutar_todo.py
----------------
RESPONSABILIDAD: Script maestro que ejecuta TODO el flujo de Fuchibol26.

FLUJO COMPLETO:
  1. Descargar datos históricos (actualizar_datos.py)
  2. Calcular estadísticas por selección (generar_estadisticas.py)
  3. Calcular ranking ELO (generar_elo.py)
  4. Generar predicciones Poisson (generar_poisson.py)
  5. Simular el Mundial completo (simular_mundial.py)
  6. Generar archivos JSON para la web (generar_json.py)

CÓMO USARLO:
  python scripts/ejecutar_todo.py

  Opciones:
  python scripts/ejecutar_todo.py --sin-descarga   → salta el paso 1 (más rápido)
  python scripts/ejecutar_todo.py --solo-json      → solo regenera los JSON
"""

import sys
import os
import time

# Agregar la carpeta scripts al path para poder importar los módulos
sys.path.insert(0, os.path.dirname(__file__))

# Importar las funciones principales de cada módulo
from actualizar_datos import descargar_datos
from generar_estadisticas import generar_estadisticas
from generar_elo import generar_elo
from generar_poisson import generar_predicciones
from simular_mundial import simular_mundial_n_veces
from generar_json import generar_json


def ejecutar_paso(numero, nombre, funcion):
    """
    Ejecuta un paso del flujo con manejo de errores.

    El éxito se determina por la ausencia de excepción, no por el valor
    de retorno. Esto permite que funciones que retornan None (sin return
    explícito) sean correctamente marcadas como exitosas.

    Args:
        numero (int): Número del paso
        nombre (str): Descripción del paso
        funcion: La función a ejecutar

    Returns:
        bool: True si tuvo éxito, False si hubo error
    """
    print(f"\n{'=' * 60}")
    print(f"PASO {numero}/6: {nombre}")
    print('=' * 60)

    inicio = time.time()

    try:
        funcion()
        tiempo = round(time.time() - inicio, 2)
        print(f"\n✅ Paso {numero} completado en {tiempo}s")
        return True

    except Exception as error:
        tiempo = round(time.time() - inicio, 2)
        print(f"\n❌ ERROR en paso {numero} (después de {tiempo}s):")
        print(f"   {type(error).__name__}: {error}")
        return False


def main():
    """Función principal: ejecuta todos los pasos en orden."""

    print("\n" + "🌍" * 30)
    print("    FUCHIBOL26 - SISTEMA DE PREDICCIÓN MUNDIAL 2026")
    print("🌍" * 30)

    inicio_total = time.time()

    # Leer argumentos de línea de comandos
    args = sys.argv[1:]
    sin_descarga = '--sin-descarga' in args
    solo_json = '--solo-json' in args

    resultados = {}

    if solo_json:
        # Solo regenerar los JSON sin recalcular nada
        print("\n⚡ Modo: Solo JSON (regenerando archivos web)")
        resultados[6] = ejecutar_paso(6, "Generar JSON para la web", generar_json)

    else:
        # Flujo completo

        # Paso 1: Descargar datos (opcional)
        if not sin_descarga:
            resultados[1] = ejecutar_paso(1, "Actualizar datos históricos", descargar_datos)
        else:
            print("\n⚡ Paso 1 omitido (--sin-descarga)")
            resultados[1] = True

        # Paso 2: Estadísticas
        resultados[2] = ejecutar_paso(2, "Calcular estadísticas por selección", generar_estadisticas)

        # Paso 3: ELO
        resultados[3] = ejecutar_paso(3, "Calcular ranking ELO", generar_elo)

        # Paso 4: Predicciones Poisson
        resultados[4] = ejecutar_paso(4, "Generar predicciones Poisson", generar_predicciones)

        # Paso 5: Simular Mundial
        resultados[5] = ejecutar_paso(5, "Simular Mundial 2026 (1000 veces)", simular_mundial_n_veces)

        # Paso 6: Generar JSON
        resultados[6] = ejecutar_paso(6, "Generar JSON para la web", generar_json)

    # ── RESUMEN FINAL ─────────────────────────────────────────────────────────
    tiempo_total = round(time.time() - inicio_total, 2)

    print(f"\n{'=' * 60}")
    print("RESUMEN DE EJECUCIÓN")
    print('=' * 60)

    exitosos = sum(1 for v in resultados.values() if v)
    totales = len(resultados)

    for paso, exito in resultados.items():
        estado = "✅" if exito else "❌"
        print(f"  {estado} Paso {paso}")

    print(f"\n  Resultado: {exitosos}/{totales} pasos exitosos")
    print(f"  Tiempo total: {tiempo_total}s")

    if exitosos == totales:
        print("\n🎉 ¡Todo listo! Abre web/index.html en tu navegador")
        print("   (o usa: python -m http.server 8000 en la carpeta Fuchibol26/)")
    else:
        print("\n⚠ Algunos pasos fallaron. Revisa los errores arriba.")

    print()


# ── PUNTO DE ENTRADA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
