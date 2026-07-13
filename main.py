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
from engine.metrics import exportar_metricas
 
 
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
    modelo, variables_x, _ = construir_modelo(datos_procesados, modo_diagnostico=False)
    print(f"  Número de variables declaradas: {len(variables_x)}")
    
    dict_resultado = resolver_modelo(modelo, variables_x)
    
    if dict_resultado["estado"] == "INFEASIBLE":
        print("\n[ALERTA] Estado INFEASIBLE detectado. El modelo choca estructuralmente.")
        print("Ejecutando el Validador de Cuellos de Botella Matemáticos (Modo Diagnóstico)...")
        
        modelo_diag, _, dict_diag = construir_modelo(datos_procesados, modo_diagnostico=True)
        from ortools.sat.python import cp_model
        solver_diag = cp_model.CpSolver()
        solver_diag.parameters.max_time_in_seconds = 60
        solver_diag.parameters.num_search_workers = 8
        status_diag = solver_diag.Solve(modelo_diag)
        
        print("\n" + "="*60)
        print(" REPORTE DE DIAGNÓSTICO: CUELLOS DE BOTELLA POR HORAS MÍNIMAS")
        print("="*60)
        if status_diag in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            problemas_encontrados = False
            for p_id, var_falta in dict_diag.items():
                faltan = solver_diag.Value(var_falta)
                if faltan > 0:
                    problemas_encontrados = True
                    nombre_prof = next(p["nombre"] for p in datos["profesores"] if p["id"] == p_id)
                    horas_req = next(p.get("horas_minimas", 1) for p in datos["profesores"] if p["id"] == p_id)
                    print(f" [x] {p_id} ({nombre_prof}):")
                    print(f"    - Exige: {horas_req} horas mínimas.")
                    print(f"    - Matemáticamente alcanzable: {horas_req - faltan} horas.")
                    print(f"    - Faltan: {faltan} horas.")
                    print(f"    -> Sugerencia: Bajar sus horas_minimas a {horas_req - faltan}, o aumentar su disponibilidad de turnos/días.\n")
            if not problemas_encontrados:
                print(" No se detectó un cuello de botella directo en profesores. Revise conflictos de unicidad o espacios.")
        else:
            print(" El conflicto es tan severo que ni siquiera flexibilizando las horas mínimas se resolvió.")
        print("="*60)
        sys.exit(1)

    print(f"  Estado del Solver: {dict_resultado['estado']}")
    print(f"  {dict_resultado['mensaje']}")
    print(f"  Clases asignadas exitosamente: {len(dict_resultado['asignaciones'])}")
    print(f"  Tiempo tomado: {dict_resultado['estadisticas']['tiempo_segundos']:.2f}s")
    
    ruta_salida = "data/output/horario_result.json"
    print(f"\nExportando resultados a: {ruta_salida}")
    asignaciones_planas = exportar_resultados(dict_resultado, ruta_salida)
    
    if asignaciones_planas:
        ruta_metricas = "data/output/metrics.json"
        print(f"Exportando analítica y métricas a: {ruta_metricas}")
        exportar_metricas(asignaciones_planas, datos_procesados, ruta_metricas)
    
    print("\n--- ¡Motor de Búsqueda Finalizado con Éxito! ---")
 
 
if __name__ == "__main__":
    main()