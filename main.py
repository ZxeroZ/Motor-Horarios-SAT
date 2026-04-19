import sys
from engine.loader import (
    cargar_datos,
    extraer_configuracion,
    extraer_categorias,
    extraer_cursos,
    extraer_profesores,
    extraer_secciones,
    extraer_grados,
)
from utils.validators import validar_todo
from engine.preprocessor import preprocesar
from engine.model import construir_modelo
from engine.solver import resolver_modelo
from engine.exporter import exportar_resultados
 
 
def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <ruta_al_json>")
        print("Ejemplo: python main.py data/input/datos.json")
        sys.exit(1)
 
    ruta_json = sys.argv[1]
 
    # --- Carga ---
    print(f"Cargando datos desde: {ruta_json}")
    try:
        datos = cargar_datos(ruta_json)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error al cargar el archivo: {e}")
        sys.exit(1)
 
    configuracion = extraer_configuracion(datos)
    categorias    = extraer_categorias(datos)
    cursos        = extraer_cursos(datos)
    profesores    = extraer_profesores(datos)
    secciones     = extraer_secciones(datos)
    grados        = extraer_grados(datos)
 
    print(f"  Categorías cargadas : {len(categorias)}")
    print(f"  Cursos cargados     : {len(cursos)}")
    print(f"  Profesores cargados : {len(profesores)}")
    print(f"  Secciones cargadas  : {len(secciones)}")
    print(f"  Grados cargados     : {len(grados)}")
 
    # --- Validación ---
    print("\nValidando integridad de los datos...")
    errores = validar_todo(datos)
 
    if errores:
        print(f"\nSe encontraron {len(errores)} error(es):\n")
        for error in errores:
            print(f"  • {error}")
        sys.exit(1)
 
    print("Validación exitosa. Datos listos para el preprocessor.")
 
    print("\nEjecutando el preprocessor...")
    datos_procesados = preprocesar(datos)
    
    print(f"  Total requerimientos (secciones): {len(datos_procesados['requerimientos_seccion'])}")
    
    print("\nConstruyendo el modelo CP-SAT...")
    modelo, variables_x = construir_modelo(datos_procesados)
    print(f"  Número de variables declaradas: {len(variables_x)}")
    
    dict_resultado = resolver_modelo(modelo, variables_x)
    print(f"  Estado del Solver: {dict_resultado['estado']}")
    print(f"  {dict_resultado['mensaje']}")
    print(f"  Clases asignadas exitosamente: {len(dict_resultado['asignaciones'])}")
    print(f"  Tiempo tomado: {dict_resultado['estadisticas']['tiempo_segundos']:.2f}s")
    
    ruta_salida = "data/output/horario_result.json"
    print(f"\nExportando resultados a: {ruta_salida}")
    exportar_resultados(dict_resultado, ruta_salida)
    
    print("\n--- ¡Motor de Búsqueda Finalizado con Éxito! ---")
 
 
if __name__ == "__main__":
    main()