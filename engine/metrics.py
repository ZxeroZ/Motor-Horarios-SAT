import collections
import json
from pathlib import Path

def exportar_metricas(asignaciones: list, ruta_salida: str) -> None:
    """
    Toma la lista lineal de slots asignados y calcula estadísticas de negocio.
    """
    # 1. Sets transaccionales para identificar valores únicos
    profesor_secciones = collections.defaultdict(set)
    profesor_cursos = collections.defaultdict(set)
    curso_profesores = collections.defaultdict(set)
    
    # 1.b Nuevo agrupador de secciones por dia y por profesor
    profesor_carga_diaria = collections.defaultdict(lambda: collections.defaultdict(set))
    
    # 2. Conteo de slots independientes (1 slot = 1 hora)
    profesor_horas_semanales = collections.defaultdict(int)
    
    # Iterar cada slot unitario asignado
    for asig in asignaciones:
        p_id = asig.get("profesor_id")
        c_id = asig.get("curso_id")
        s_id = asig.get("seccion_id")
        dia = asig.get("dia")
        
        # Validar variables para evadir llaves muertas si las hubiera
        if not p_id or not c_id or not s_id or not dia:
            continue
            
        profesor_secciones[p_id].add(s_id)
        profesor_cursos[p_id].add(c_id)
        curso_profesores[c_id].add(p_id)
        profesor_carga_diaria[p_id][dia].add(s_id)
        
        # Cada registro en la lista plana representa 1 slot exacto
        profesor_horas_semanales[p_id] += 1

    # 3. Ensamblado final de la respuesta analítica
    metricas = {
        "profesores": {},
        "cursos": {}
    }
    
    # Rellenar Profesores
    DIAS_ORDEN = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    
    for p_id in profesor_secciones.keys():
        secciones_list = list(profesor_secciones[p_id])
        cursos_list = list(profesor_cursos[p_id])
        
        # Ordenamos las listas para legibilidad pura
        secciones_list.sort()
        cursos_list.sort()
        
        # Extraer carga diaria forzando orden cronologico de dias
        carga_diaria = {}
        for dia_key in DIAS_ORDEN:
            lista_sec_dia = list(profesor_carga_diaria[p_id].get(dia_key, set()))
            lista_sec_dia.sort()
            carga_diaria[dia_key] = lista_sec_dia
        
        metricas["profesores"][p_id] = {
            "total_horas_semanales": profesor_horas_semanales[p_id],
            "cantidad_secciones": len(secciones_list),
            "cantidad_cursos": len(cursos_list),
            "secciones_asignadas": secciones_list,
            "cursos_dictados": cursos_list,
            "carga_diaria": carga_diaria
        }
        
    # Rellenar Cursos
    for c_id in curso_profesores.keys():
        profesores_list = list(curso_profesores[c_id])
        profesores_list.sort()
        
        metricas["cursos"][c_id] = {
            "cantidad_profesores": len(profesores_list),
            "profesores_activos": profesores_list
        }
        
    # Ordenar los diccionarios maestros alfabéticamente (P001, P002...)
    metricas["profesores"] = dict(sorted(metricas["profesores"].items()))
    metricas["cursos"] = dict(sorted(metricas["cursos"].items()))

    # 4. Asegurar la ruta y guardar
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
