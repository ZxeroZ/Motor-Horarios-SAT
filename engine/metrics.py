"""
Módulo de métricas del motor de horarios.

Calcula KPIs y estadísticas de negocio sobre los horarios generados.
Cada función de cálculo es pura (sin I/O), testeable de forma independiente,
y retorna un dict parcial que `calcular_metricas()` ensambla.
"""
import collections
import json
import math
from pathlib import Path


DIAS_ORDEN = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]


def _extraer_asignaciones_validas(asignaciones: list) -> list:
    """Filtra asignaciones que tengan todos los campos requeridos."""
    return [
        a for a in asignaciones
        if a.get("profesor_id") and a.get("curso_id") and a.get("seccion_id") and a.get("dia")
    ]


def _calcular_slots_reservados(seccion_info: dict, bloques_reservados: list, plantilla: dict) -> int:
    """Calcula cuántos slots están reservados para una sección dada."""
    slots_reservados = 0
    for r in bloques_reservados:
        if r.get("sede") == seccion_info.get("sede"):
            grados_afectados = r.get("grados_afectados")
            if not grados_afectados or seccion_info.get("grado") in grados_afectados:
                dia_reserva = r.get("dia")
                if dia_reserva in plantilla:
                    max_slots_dia = plantilla[dia_reserva]
                    opciones_slots = r.get("opciones_slots", [])
                    if opciones_slots:
                        bloqueos_por_opcion = [
                            sum(1 for s in opt if 1 <= s <= max_slots_dia)
                            for opt in opciones_slots
                        ]
                        # Asumimos el mejor escenario (la opción que bloquea menos)
                        slots_reservados += min(bloqueos_por_opcion)
    return slots_reservados


# ---------------------------------------------------------------------------
# Funciones de cálculo individuales (puras, sin I/O)
# ---------------------------------------------------------------------------

def calcular_metricas_profesores(asignaciones: list) -> dict:
    """
    Métricas por profesor: horas semanales, secciones asignadas,
    cursos dictados y carga diaria.
    """
    asigs = _extraer_asignaciones_validas(asignaciones)

    profesor_secciones = collections.defaultdict(set)
    profesor_cursos = collections.defaultdict(set)
    profesor_carga_diaria = collections.defaultdict(lambda: collections.defaultdict(set))
    profesor_horas_semanales = collections.defaultdict(int)

    for a in asigs:
        p_id = a["profesor_id"]
        profesor_secciones[p_id].add(a["seccion_id"])
        profesor_cursos[p_id].add(a["curso_id"])
        profesor_carga_diaria[p_id][a["dia"]].add(a["seccion_id"])
        profesor_horas_semanales[p_id] += 1

    profesores = {}
    for p_id in sorted(profesor_secciones.keys()):
        secciones_list = sorted(profesor_secciones[p_id])
        cursos_list = sorted(profesor_cursos[p_id])

        carga_diaria = {}
        for dia_key in DIAS_ORDEN:
            lista_sec_dia = sorted(profesor_carga_diaria[p_id].get(dia_key, set()))
            carga_diaria[dia_key] = lista_sec_dia

        profesores[p_id] = {
            "total_horas_semanales": profesor_horas_semanales[p_id],
            "cantidad_secciones": len(secciones_list),
            "cantidad_cursos": len(cursos_list),
            "secciones_asignadas": secciones_list,
            "cursos_dictados": cursos_list,
            "carga_diaria": carga_diaria
        }

    return profesores


def calcular_metricas_cursos(asignaciones: list) -> dict:
    """Métricas por curso: cantidad de profesores activos."""
    asigs = _extraer_asignaciones_validas(asignaciones)

    curso_profesores = collections.defaultdict(set)
    for a in asigs:
        curso_profesores[a["curso_id"]].add(a["profesor_id"])

    cursos = {}
    for c_id in sorted(curso_profesores.keys()):
        profesores_list = sorted(curso_profesores[c_id])
        cursos[c_id] = {
            "cantidad_profesores": len(profesores_list),
            "profesores_activos": profesores_list
        }

    return cursos


def calcular_metricas_slots(asignaciones: list, datos_procesados: dict) -> dict:
    """
    Slots ocupados, disponibles y huecos por sección,
    considerando bloques reservados.
    """
    secciones_info = datos_procesados.get("secciones", {})
    bloques_reservados = datos_procesados.get("bloques_reservados", [])

    ocupados_por_seccion = collections.defaultdict(int)
    for a in asignaciones:
        if "seccion_id" in a:
            ocupados_por_seccion[a["seccion_id"]] += 1

    metricas_slots = {
        "total_disponibles": 0,
        "total_ocupados": len(asignaciones),
        "total_huecos": 0,
        "detalle_secciones": {}
    }

    for s_id, s_info in secciones_info.items():
        plantilla = s_info.get("horario_plantilla", {})
        slots_totales = sum(plantilla.values())
        slots_reservados = _calcular_slots_reservados(s_info, bloques_reservados, plantilla)
        slots_efectivos = slots_totales - slots_reservados

        slots_ocupados = ocupados_por_seccion.get(s_id, 0)
        huecos = slots_efectivos - slots_ocupados

        metricas_slots["total_disponibles"] += slots_efectivos
        metricas_slots["total_huecos"] += huecos

        metricas_slots["detalle_secciones"][s_id] = {
            "slots_totales": slots_efectivos,
            "slots_ocupados": slots_ocupados,
            "huecos": huecos
        }

    metricas_slots["detalle_secciones"] = dict(sorted(metricas_slots["detalle_secciones"].items()))
    return metricas_slots


def calcular_cobertura(asignaciones: list, datos_procesados: dict) -> dict:
    """
    Tasa de cobertura: cursos efectivamente asignados vs requeridos por sección.
    Retorna ratio 0.0-1.0 por sección y global.
    """
    requerimientos = datos_procesados.get("requerimientos_seccion", {})
    asigs = _extraer_asignaciones_validas(asignaciones)

    cursos_asignados_por_seccion = collections.defaultdict(set)
    for a in asigs:
        cursos_asignados_por_seccion[a["seccion_id"]].add(a["curso_id"])

    detalle = {}
    total_requeridos = 0
    total_cubiertos = 0

    for s_id, reqs in requerimientos.items():
        requeridos = set(reqs.keys())
        asignados = cursos_asignados_por_seccion.get(s_id, set())
        cubiertos = requeridos & asignados

        total_requeridos += len(requeridos)
        total_cubiertos += len(cubiertos)

        tasa = len(cubiertos) / len(requeridos) if requeridos else 1.0
        detalle[s_id] = {
            "cursos_requeridos": len(requeridos),
            "cursos_asignados": len(cubiertos),
            "cursos_sin_asignar": sorted(requeridos - asignados),
            "tasa": round(tasa, 4)
        }

    tasa_global = total_cubiertos / total_requeridos if total_requeridos > 0 else 1.0

    return {
        "tasa_global": round(tasa_global, 4),
        "detalle_secciones": dict(sorted(detalle.items()))
    }


def calcular_saturacion_cursos(asignaciones: list, datos_procesados: dict) -> dict:
    """
    Saturación de cada curso: ratio de profesores que lo dictan
    vs profesores habilitados para dictarlo.
    """
    profesores_por_curso = datos_procesados.get("profesores_por_curso", {})
    asigs = _extraer_asignaciones_validas(asignaciones)

    curso_profesores_activos = collections.defaultdict(set)
    for a in asigs:
        curso_profesores_activos[a["curso_id"]].add(a["profesor_id"])

    detalle = {}
    for c_id, habilitados in profesores_por_curso.items():
        activos = curso_profesores_activos.get(c_id, set())
        total_hab = len(habilitados)
        total_act = len(activos)
        ratio = total_act / total_hab if total_hab > 0 else 0.0

        detalle[c_id] = {
            "profesores_habilitados": total_hab,
            "profesores_activos": total_act,
            "ratio": round(ratio, 4)
        }

    return dict(sorted(detalle.items()))


def calcular_utilizacion_sedes(asignaciones: list, datos_procesados: dict) -> dict:
    """
    Utilización por sede (slots ocupados / disponibles)
    y densidad horaria por día.
    """
    secciones_info = datos_procesados.get("secciones", {})
    bloques_reservados = datos_procesados.get("bloques_reservados", [])
    asigs = _extraer_asignaciones_validas(asignaciones)

    # Mapear sección → sede
    seccion_sede = {s_id: s_info.get("sede", "Sin sede") for s_id, s_info in secciones_info.items()}

    # Slots ocupados por sede
    ocupados_por_sede = collections.defaultdict(int)
    for a in asigs:
        sede = seccion_sede.get(a["seccion_id"], "Sin sede")
        ocupados_por_sede[sede] += 1

    # Slots disponibles por sede (sumando plantillas efectivas de sus secciones)
    disponibles_por_sede = collections.defaultdict(int)
    for s_id, s_info in secciones_info.items():
        sede = s_info.get("sede", "Sin sede")
        plantilla = s_info.get("horario_plantilla", {})
        slots_totales = sum(plantilla.values())
        slots_reservados = _calcular_slots_reservados(s_info, bloques_reservados, plantilla)
        disponibles_por_sede[sede] += (slots_totales - slots_reservados)

    todas_sedes = sorted(set(list(ocupados_por_sede.keys()) + list(disponibles_por_sede.keys())))
    utilizacion_sedes = {}
    for sede in todas_sedes:
        ocupados = ocupados_por_sede.get(sede, 0)
        disponibles = disponibles_por_sede.get(sede, 0)
        ratio = ocupados / disponibles if disponibles > 0 else 0.0
        utilizacion_sedes[sede] = {
            "slots_ocupados": ocupados,
            "slots_disponibles": disponibles,
            "utilizacion": round(ratio, 4)
        }

    # Densidad horaria por día
    ocupados_por_dia = collections.defaultdict(int)
    disponibles_por_dia = collections.defaultdict(int)

    for a in asigs:
        ocupados_por_dia[a["dia"]] += 1

    for s_id, s_info in secciones_info.items():
        plantilla = s_info.get("horario_plantilla", {})
        for dia, slots in plantilla.items():
            disponibles_por_dia[dia] += slots

    densidad_diaria = {}
    for dia in DIAS_ORDEN:
        ocupados = ocupados_por_dia.get(dia, 0)
        disponibles = disponibles_por_dia.get(dia, 0)
        ratio = ocupados / disponibles if disponibles > 0 else 0.0
        densidad_diaria[dia] = {
            "slots_ocupados": ocupados,
            "slots_disponibles": disponibles,
            "densidad": round(ratio, 4)
        }

    return {
        "por_sede": utilizacion_sedes,
        "densidad_diaria": densidad_diaria
    }


def calcular_balance_docente(asignaciones: list) -> dict:
    """
    Balance de carga docente (coeficiente de variación de horas)
    e índice de fragmentación de cursos.
    """
    asigs = _extraer_asignaciones_validas(asignaciones)

    # --- Balance de carga ---
    horas_por_profesor = collections.defaultdict(int)
    for a in asigs:
        horas_por_profesor[a["profesor_id"]] += 1

    horas_list = list(horas_por_profesor.values())

    if len(horas_list) > 1:
        promedio = sum(horas_list) / len(horas_list)
        varianza = sum((h - promedio) ** 2 for h in horas_list) / len(horas_list)
        desv_estandar = math.sqrt(varianza)
        coef_variacion = desv_estandar / promedio if promedio > 0 else 0.0
    elif len(horas_list) == 1:
        promedio = float(horas_list[0])
        desv_estandar = 0.0
        coef_variacion = 0.0
    else:
        promedio = 0.0
        desv_estandar = 0.0
        coef_variacion = 0.0

    profesor_max = max(horas_por_profesor.items(), key=lambda x: x[1]) if horas_por_profesor else ("N/A", 0)
    profesor_min = min(horas_por_profesor.items(), key=lambda x: x[1]) if horas_por_profesor else ("N/A", 0)

    # --- Fragmentación ---
    # Para cada (sección, curso), contar en cuántos días distintos aparece
    curso_seccion_dias = collections.defaultdict(set)
    for a in asigs:
        curso_seccion_dias[(a["seccion_id"], a["curso_id"])].add(a["dia"])

    total_asignaciones_unicas = len(curso_seccion_dias)
    fragmentados = sum(1 for dias in curso_seccion_dias.values() if len(dias) > 1)
    indice_fragmentacion = fragmentados / total_asignaciones_unicas if total_asignaciones_unicas > 0 else 0.0

    return {
        "balance_carga": {
            "promedio_horas": round(promedio, 2),
            "desviacion_estandar": round(desv_estandar, 2),
            "coeficiente_variacion": round(coef_variacion, 4),
            "profesor_mas_cargado": {"id": profesor_max[0], "horas": profesor_max[1]},
            "profesor_menos_cargado": {"id": profesor_min[0], "horas": profesor_min[1]},
            "total_profesores": len(horas_por_profesor)
        },
        "fragmentacion": {
            "cursos_fragmentados": fragmentados,
            "cursos_totales": total_asignaciones_unicas,
            "indice": round(indice_fragmentacion, 4)
        }
    }


# ---------------------------------------------------------------------------
# Funciones orquestadoras
# ---------------------------------------------------------------------------

def calcular_metricas(asignaciones: list, datos_procesados: dict) -> dict:
    """
    Orquestador principal. Calcula todas las métricas y retorna
    el dict completo en memoria (sin I/O).
    """
    return {
        "resumen_slots": calcular_metricas_slots(asignaciones, datos_procesados),
        "profesores": calcular_metricas_profesores(asignaciones),
        "cursos": calcular_metricas_cursos(asignaciones),
        "kpis": {
            "cobertura": calcular_cobertura(asignaciones, datos_procesados),
            "saturacion_cursos": calcular_saturacion_cursos(asignaciones, datos_procesados),
            "utilizacion": calcular_utilizacion_sedes(asignaciones, datos_procesados),
            "balance_docente": calcular_balance_docente(asignaciones),
        }
    }


def exportar_metricas(asignaciones: list, datos_procesados: dict, ruta_salida: str) -> None:
    """
    Calcula todas las métricas y las escribe a disco en formato JSON.
    Wrapper de `calcular_metricas()` para uso desde CLI.
    """
    metricas = calcular_metricas(asignaciones, datos_procesados)

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
