import json
from pathlib import Path
import collections

def exportar_resultados(resultados_solver: dict, ruta_salida: str) -> None:
    """
    Toma los resultados puros de los bloques Z del solver y los desempaqueta para
    serializarlos en formato plano a un archivo JSON (manteniendo la misma estructura
    compatible previamente construida, slot por slot).
    """
    # 1. Recuperamos los bloques maestros
    bloques_planos = resultados_solver.get("asignaciones", [])
    
    ORDEN_DIAS = {
        "Lunes": 1,
        "Martes": 2,
        "Miercoles": 3,
        "Jueves": 4,
        "Viernes": 5
    }

    # Desempaquetamos los bloques en slots individuales lineales (0-indexed base)
    asignaciones_planas = []
    for bloque in bloques_planos:
        start_slot = bloque["slot_inicio"]
        H = bloque["horas"]
        for k in range(H):
            # Clonamos la info base del bloque
            slot_individual = {
                "seccion_id": bloque["seccion_id"],
                "curso_id": bloque["curso_id"],
                "profesor_id": bloque["profesor_id"],
                "dia": bloque["dia"],
                "turno": bloque["turno"],
                "slot": start_slot + k + 1  # Ajustado a 1-indexed directo
            }
            asignaciones_planas.append(slot_individual)

    # Función de ordenamiento cronológico
    def _sort_key_plana(clase):
        sec = clase.get("seccion_id", "")
        dia_idx = ORDEN_DIAS.get(clase.get("dia", ""), 99)
        return (sec, dia_idx, clase.get("slot", 0))
        
    asignaciones_planas.sort(key=_sort_key_plana)
    
    # Agrupación 1: Por Sección
    horario_por_seccion = collections.defaultdict(list)
    # Agrupación 2: Por Profesor
    horario_por_profesor = collections.defaultdict(list)

    def _clase_sort_key(clase):
        dia_idx = ORDEN_DIAS.get(clase.get("dia", ""), 99)
        return (dia_idx, clase.get("slot", 0))

    for clase in asignaciones_planas:
        # Guardamos en la vista de Seccion
        horario_por_seccion[clase["seccion_id"]].append(clase)
        
        # Guardamos en la vista de Profesor
        horario_por_profesor[clase["profesor_id"]].append(clase)
        
    # Ordenar las clases de cada profesor 
    for clases_prof in horario_por_profesor.values():
        clases_prof.sort(key=_clase_sort_key)
        
    
    # Estructuramos el payload final
    payload = {
        "metadata": {
            "estado": resultados_solver.get("estado"),
            "mensaje": resultados_solver.get("mensaje"),
            "estadisticas_solver": resultados_solver.get("estadisticas")
        },
        "asignaciones_lista": asignaciones_planas,
        "vista_secciones": dict(horario_por_seccion),
        "vista_profesores": dict(horario_por_profesor)
    }
    
    # 2. Asegurar el path y escribir a disco
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
