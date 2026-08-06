"""
Módulo de diagnóstico integral del motor CP-SAT.

Ejecuta el solver en modo relajado (horas mínimas con holgura) y analiza
las causas subyacentes para cada profesor con déficit de horas.

Diseñado para ser ejecutado de forma asíncrona (en un Thread) desde el backend.
"""
import collections
import logging
from ortools.sat.python import cp_model

from engine.model import construir_modelo
from engine.solver import resolver_modelo

logger = logging.getLogger(__name__)


def ejecutar_diagnostico(datos_procesados: dict, datos_crudos: dict, on_progress=None) -> dict:
    """
    Flujo completo de diagnóstico:
    1. Construir modelo relajado (modo_diagnostico=True)
    2. Resolver con timeout de 60s
    3. Extraer profesores con déficit
    4. Analizar causas subyacentes en memoria
    5. Retornar JSON estructurado

    Args:
        datos_procesados: Salida de preprocesar()
        datos_crudos: JSON original (para nombres legibles)
        on_progress: Callback opcional (percent, message)
    """
    def _progress(percent, message):
        if on_progress:
            on_progress(percent, message)

    # --- Paso 1: Construir modelo relajado ---
    _progress(40, "Construyendo modelo relajado...")
    modelo, variables_z, dict_diagnostico = construir_modelo(datos_procesados, modo_diagnostico=True)

    if not dict_diagnostico:
        return {
            "estado": "sin_conflictos",
            "total_profesores_afectados": 0,
            "cuellos_de_botella": [],
            "mensaje": "No hay restricciones de horas mínimas activas para diagnosticar.",
            "estadisticas_solver": {}
        }

    # --- Paso 2: Resolver ---
    _progress(60, "Ejecutando solver diagnóstico (máx 60s)...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8
    status = solver.Solve(modelo)

    estadisticas = {
        "tiempo_segundos": round(solver.WallTime(), 2),
        "estado_solver": _status_name(status),
        "ramas_exploradas": solver.NumBranches(),
        "conflictos": solver.NumConflicts()
    }

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "estado": "solver_fallo",
            "total_profesores_afectados": 0,
            "cuellos_de_botella": [],
            "mensaje": f"El solver diagnóstico retornó {_status_name(status)}. "
                       "Incluso relajando horas mínimas, el modelo no converge.",
            "estadisticas_solver": estadisticas
        }

    # --- Paso 3: Extraer profesores con déficit ---
    _progress(80, "Analizando causas subyacentes...")
    profesores_con_deficit = []
    for p_id, var_falta in dict_diagnostico.items():
        faltan = solver.Value(var_falta)
        if faltan > 0:
            horas_min = datos_procesados["profesores"][p_id].get("horas_minimas", 0)
            profesores_con_deficit.append({
                "profesor_id": p_id,
                "horas_requeridas": horas_min,
                "horas_alcanzadas": horas_min - faltan,
                "deficit": faltan
            })

    if not profesores_con_deficit:
        return {
            "estado": "sin_conflictos",
            "total_profesores_afectados": 0,
            "cuellos_de_botella": [],
            "mensaje": "El modo diagnóstico no encontró cuellos de botella. "
                       "El INFEASIBLE puede deberse a timeout del solver. "
                       "Intente aumentar el tiempo límite de resolución.",
            "estadisticas_solver": estadisticas
        }

    # --- Paso 4: Analizar causas subyacentes para cada profesor ---
    # Extraer la solución completa para cruzar datos
    asignaciones_solucion = _extraer_asignaciones(solver, variables_z)

    # Lookups para nombres legibles
    nombres = _build_nombres(datos_crudos)

    cuellos = []
    for prof_info in profesores_con_deficit:
        p_id = prof_info["profesor_id"]
        causas = _analizar_causas_profesor(
            p_id, datos_procesados, asignaciones_solucion, solver, variables_z
        )
        cuellos.append({
            "profesor_id": p_id,
            "profesor_nombre": nombres.get("profesores", {}).get(p_id, p_id),
            "horas_requeridas": prof_info["horas_requeridas"],
            "horas_alcanzadas": prof_info["horas_alcanzadas"],
            "deficit": prof_info["deficit"],
            "causas": causas
        })

    _progress(95, "Empaquetando resultados...")
    return {
        "estado": "conflictos_detectados",
        "total_profesores_afectados": len(cuellos),
        "cuellos_de_botella": cuellos,
        "estadisticas_solver": estadisticas
    }


# ---------------------------------------------------------------------------
# Funciones auxiliares de análisis
# ---------------------------------------------------------------------------

def _analizar_causas_profesor(p_id, datos_procesados, asignaciones, solver, variables_z):
    """
    Para un profesor con déficit, identifica las causas subyacentes
    analizando la solución relajada en memoria. No re-ejecuta el solver.
    """
    causas = []

    config = datos_procesados["configuracion"]
    profesores_dict = datos_procesados["profesores"]
    secciones_dict = datos_procesados["secciones"]
    categorias = datos_procesados["categorias"]
    cursos = datos_procesados["cursos"]
    requerimientos = datos_procesados["requerimientos_seccion"]
    bloques_reservados = datos_procesados.get("bloques_reservados", [])
    disp_profesor_slots = datos_procesados.get("disp_profesor_slots", {})
    turnos = config["turnos"]

    p_info = profesores_dict[p_id]
    p_disp_slots = disp_profesor_slots.get(p_id, {})
    cursos_hab = set(p_info.get("cursos_habilitados", []))
    grados_hab = set(p_info.get("grados_habilitados", []))

    # Slots donde el profesor está disponible
    slots_disponibles = set()
    for key, slots in p_disp_slots.items():
        if len(key) == 3:
            dia, turno, sede = key
            for s in slots:
                slots_disponibles.add((dia, turno, s, sede))
        elif len(key) == 2:
            dia, turno = key
            for s in slots:
                slots_disponibles.add((dia, turno, s, None))

    # --- Causa: Reservas que bloquean slots ---
    slots_bloqueados_por_reserva = 0
    detalles_reservas = []
    for r_idx, r in enumerate(bloques_reservados):
        r_sede = r.get("sede")
        r_dia = r.get("dia")
        r_turno = r.get("turno")
        r_opciones = r.get("opciones_slots", [])
        r_grados = r.get("grados_afectados")

        # Verificar si alguna sección accesible al profesor pertenece a esta reserva
        profesor_afectado = False
        for s_id, s_info in secciones_dict.items():
            if s_info.get("sede") == r_sede:
                grado_id = s_info.get("grado")
                if grado_id in grados_hab:
                    if not r_grados or grado_id in r_grados:
                        profesor_afectado = True
                        break

        if not profesor_afectado:
            continue

        # Contar slots que el profesor tenía disponibles y fueron bloqueados
        for opt in r_opciones:
            for slot_fisico in opt:
                if (r_dia, r_turno, slot_fisico, r_sede) in slots_disponibles or \
                   (r_dia, r_turno, slot_fisico, None) in slots_disponibles:
                    slots_bloqueados_por_reserva += 1

    if slots_bloqueados_por_reserva > 0:
        causas.append({
            "tipo": "reserva_bloqueo",
            "descripcion": f"{slots_bloqueados_por_reserva} slot(s) de disponibilidad bloqueados por reservas de bloques horarios",
            "slots_afectados": slots_bloqueados_por_reserva
        })

    # --- Causa: Traslado inter-sedes ---
    sedes_config = config.get("sedes", [])
    if len(sedes_config) > 1:
        slots_perdidos_viaje = _contar_slots_viaje(p_id, asignaciones, secciones_dict)
        if slots_perdidos_viaje > 0:
            causas.append({
                "tipo": "traslado_intersedes",
                "descripcion": f"{slots_perdidos_viaje} slot(s) perdidos como buffer de traslado entre sedes distintas",
                "slots_afectados": slots_perdidos_viaje
            })

    # --- Causa: Competencia de slots con otros profesores ---
    slots_competidos = _contar_competencia_slots(
        p_id, asignaciones, datos_procesados
    )
    if slots_competidos["total"] > 0:
        causas.append({
            "tipo": "competencia_slots",
            "descripcion": f"Compite por {slots_competidos['total']} slot(s) con otros profesores en las mismas secciones",
            "slots_afectados": slots_competidos["total"],
            "detalle": {
                "profesores_competidores": slots_competidos["competidores"][:5]
            }
        })

    # --- Causa: Tope de categoría ---
    dias_topados = _detectar_tope_categoria(p_id, asignaciones, datos_procesados)
    if dias_topados:
        total_slots = sum(d["slots_no_disponibles"] for d in dias_topados)
        causas.append({
            "tipo": "tope_categoria",
            "descripcion": f"En {len(dias_topados)} día(s), las categorías de sus cursos alcanzaron el límite max_horas_dia, impidiendo {total_slots} asignación(es) adicional(es)",
            "slots_afectados": total_slots,
            "detalle": {
                "dias_afectados": dias_topados
            }
        })

    # Si no se detectó ninguna causa concreta
    if not causas:
        causas.append({
            "tipo": "indeterminado",
            "descripcion": "El déficit se debe a una combinación compleja de restricciones que no se pudo aislar automáticamente",
            "slots_afectados": 0
        })

    return causas


def _contar_slots_viaje(p_id, asignaciones, secciones_dict):
    """Cuenta slots que el profesor pierde como buffer de traslado inter-sedes."""
    # Agrupar asignaciones del profesor por (dia, turno)
    slots_por_dia = collections.defaultdict(list)
    for asig in asignaciones:
        if asig["profesor_id"] == p_id:
            sede = secciones_dict.get(asig["seccion_id"], {}).get("sede")
            slots_por_dia[(asig["dia"], asig["turno"])].append({
                "slot": asig["slot_inicio"],
                "horas": asig["horas"],
                "sede": sede
            })

    slots_perdidos = 0
    for (dia, turno), bloques in slots_por_dia.items():
        # Expandir bloques a slots individuales con su sede
        slot_sede = {}
        for b in bloques:
            for k in range(b["horas"]):
                slot_sede[b["slot"] + k] = b["sede"]

        # Buscar pares consecutivos en sedes distintas
        slots_ordenados = sorted(slot_sede.keys())
        for i in range(len(slots_ordenados) - 1):
            s1 = slots_ordenados[i]
            s2 = slots_ordenados[i + 1]
            if s2 == s1 + 1 and slot_sede[s1] != slot_sede[s2]:
                # Ya viola la restricción de viaje (en modo relajado esto se permite)
                # pero indica que se necesitaría un buffer
                slots_perdidos += 1

    return slots_perdidos


def _contar_competencia_slots(p_id, asignaciones, datos_procesados):
    """
    Cuenta slots donde otro profesor fue asignado a una sección/grado que
    el profesor con déficit también podría haber cubierto.
    """
    profesores_dict = datos_procesados["profesores"]
    secciones_dict = datos_procesados["secciones"]
    requerimientos = datos_procesados["requerimientos_seccion"]

    p_info = profesores_dict[p_id]
    cursos_hab = set(p_info.get("cursos_habilitados", []))
    grados_hab = set(p_info.get("grados_habilitados", []))

    # Secciones donde el profesor podría enseñar
    secciones_potenciales = set()
    for s_id, s_info in secciones_dict.items():
        if s_info.get("grado") in grados_hab:
            for c_id in requerimientos.get(s_id, {}).keys():
                if c_id in cursos_hab:
                    secciones_potenciales.add(s_id)
                    break

    # Contar asignaciones de otros profesores en esas secciones
    competidores = collections.Counter()
    total = 0
    for asig in asignaciones:
        if asig["profesor_id"] != p_id and asig["seccion_id"] in secciones_potenciales:
            if asig["curso_id"] in cursos_hab:
                competidores[asig["profesor_id"]] += asig["horas"]
                total += asig["horas"]

    return {
        "total": total,
        "competidores": [pid for pid, _ in competidores.most_common()]
    }


def _detectar_tope_categoria(p_id, asignaciones, datos_procesados):
    """
    Para cada día, verifica si las categorías de los cursos que el profesor
    podría dictar ya alcanzaron max_horas_dia en las secciones disponibles.
    """
    categorias = datos_procesados["categorias"]
    cursos = datos_procesados["cursos"]
    secciones_dict = datos_procesados["secciones"]
    profesores_dict = datos_procesados["profesores"]

    p_info = profesores_dict[p_id]
    cursos_hab = set(p_info.get("cursos_habilitados", []))
    grados_hab = set(p_info.get("grados_habilitados", []))

    # Categorías que el profesor podría dictar
    cats_del_profesor = set()
    for c_id in cursos_hab:
        if c_id in cursos:
            cats_del_profesor.add(cursos[c_id]["categoria_id"])

    # Agrupar horas asignadas por (seccion, dia, categoria)
    carga_cat = collections.defaultdict(int)
    for asig in asignaciones:
        c_id = asig["curso_id"]
        if c_id in cursos:
            cat_id = cursos[c_id]["categoria_id"]
            carga_cat[(asig["seccion_id"], asig["dia"], cat_id)] += asig["horas"]

    dias_topados = []
    secciones_relevantes = {
        s_id for s_id, s_info in secciones_dict.items()
        if s_info.get("grado") in grados_hab
    }

    checked = set()
    for (s_id, dia, cat_id), horas_usadas in carga_cat.items():
        if s_id not in secciones_relevantes or cat_id not in cats_del_profesor:
            continue
        if (s_id, dia, cat_id) in checked:
            continue
        checked.add((s_id, dia, cat_id))

        max_dia = categorias.get(cat_id, {}).get("max_horas_dia", 99)
        if horas_usadas >= max_dia:
            dias_topados.append({
                "seccion_id": s_id,
                "dia": dia,
                "categoria_id": cat_id,
                "horas_usadas": horas_usadas,
                "max_permitidas": max_dia,
                "slots_no_disponibles": 1  # Al menos 1 slot extra no cabe
            })

    return dias_topados


def _extraer_asignaciones(solver, variables_z):
    """Extrae la solución del solver relajado como lista de asignaciones."""
    asignaciones = []
    for llave, variable in variables_z.items():
        if solver.BooleanValue(variable):
            s_id, c_id, p_id, dia, turno, start, H, sub_idx = llave
            asignaciones.append({
                "seccion_id": s_id,
                "curso_id": c_id,
                "profesor_id": p_id,
                "dia": dia,
                "turno": turno,
                "slot_inicio": start,
                "horas": H
            })
    return asignaciones


def _build_nombres(datos_crudos):
    """Construye lookup de nombres legibles desde el JSON crudo."""
    nombres = {"profesores": {}, "cursos": {}, "secciones": {}}
    for p in datos_crudos.get("profesores", []):
        nombres["profesores"][p["id"]] = p.get("nombre", p["id"])
    for c in datos_crudos.get("cursos", []):
        nombres["cursos"][c["id"]] = c.get("nombre", c["id"])
    for s in datos_crudos.get("secciones", []):
        nombres["secciones"][s["id"]] = s.get("nombre", s["id"])
    return nombres


def _status_name(status):
    """Convierte el status numérico de CP-SAT a nombre legible."""
    mapping = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN"
    }
    return mapping.get(status, f"STATUS_{status}")
