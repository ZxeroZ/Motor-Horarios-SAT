from ortools.sat.python import cp_model

def resolver_modelo(modelo: cp_model.CpModel, bloques_z: dict, max_tiempo_segundos: int = 60) -> dict:
    """
    Ejecuta el resolver CP-SAT sobre el modelo modificado (basado en bloques contiguos) y extrae los resultados.
    """
    solver = cp_model.CpSolver()
    
    # Parámetros del solver
    solver.parameters.max_time_in_seconds = max_tiempo_segundos
    # Permite que intente encontrar múltiples soluciones en paralelo
    solver.parameters.num_search_workers = 8
    
    print("\n--- Ejecutando Solver CP-SAT ---")
    status = solver.Solve(modelo)
    
    resultado = {
        "estado": "",
        "mensaje": "",
        "estadisticas": {
            "tiempo_segundos": solver.WallTime(),
            "ramas_exploradas": solver.NumBranches(),
            "conflictos": solver.NumConflicts()
        },
        "asignaciones": []
    }
    
    if status == cp_model.OPTIMAL:
        resultado["estado"] = "OPTIMAL"
        resultado["mensaje"] = "Se encontró la solución óptima del horario."
    elif status == cp_model.FEASIBLE:
        resultado["estado"] = "FEASIBLE"
        resultado["mensaje"] = "Se encontró una solución válida, pero no está comprobado que sea la óptima absoluta."
    elif status == cp_model.INFEASIBLE:
        resultado["estado"] = "INFEASIBLE"
        resultado["mensaje"] = "El modelo es irresoluble. Las restricciones actuales chocan irremediablemente."
        return resultado
    else:
        resultado["estado"] = "UNKNOWN"
        resultado["mensaje"] = "No se encontró solución antes de agotar el límite de tiempo."
        return resultado

    # Extraer la solución en base a las variables "Z" (inicio de bloque)
    asignaciones_exitosas = []
    
    # bloques_z llave: (s_id, c_id, p_id, dia, turno, start, H)
    for llave, variable in bloques_z.items():
        if solver.BooleanValue(variable):
            s_id, c_id, p_id, dia, turno, start, H = llave
            asignaciones_exitosas.append({
                "seccion_id": s_id,
                "curso_id": c_id,
                "profesor_id": p_id,
                "dia": dia,
                "turno": turno,
                "slot_inicio": start,
                "horas": H
            })
            
    resultado["asignaciones"] = asignaciones_exitosas
    return resultado
