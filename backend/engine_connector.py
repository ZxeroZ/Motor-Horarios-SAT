import json
import logging
import uuid
import threading
from datetime import datetime
from collections import defaultdict
from sqlmodel import Session, select
from backend.models import (
    Sedes, Dias, Areas, Cursos, Grado, Seccion, PlanEstudio, 
    Profesores, ProfesorCurso, GradoDiaConfig, SeccionTurno, Turno, Tutoria,
    ProfesorDisponibilidad, ProfesorPreferencia, Bloque, SedeProfesor,
    GradoProfesor, BloqueReservado, BloqueGrado, BloqueOpcion, BloqueOpcionSlot, HorarioSnapshot,
    HorarioFinal
)
from engine.preprocessor import preprocesar
from engine.model import construir_modelo
from engine.solver import resolver_modelo
from engine.metrics import calcular_metricas as _calcular_metricas_motor
from utils.validators import validar_todo
from backend.exceptions import ValidationError, EngineError

logger = logging.getLogger(__name__)

# --- Progress Store ---
progress_store = {}

def get_progress(task_id: str) -> dict:
    return progress_store.get(task_id, {"status": "not_found"})

def _update_progress(task_id: str, step: str, percent: int, message: str):
    if task_id:
        progress_store[task_id] = {
            "status": "running",
            "step": step,
            "percent": percent,
            "message": message,
        }

def start_generation(db_engine) -> str:
    """Lanza la generación en un thread aparte y devuelve task_id."""
    task_id = str(uuid.uuid4())[:8]
    progress_store[task_id] = {"status": "starting", "step": "init", "percent": 0, "message": "Iniciando..."}

    def _run():
        from sqlmodel import Session
        with Session(db_engine) as session:
            try:
                generar_horario_engine(session, task_id)
            except Exception as e:
                progress_store[task_id] = {"status": "error", "message": str(e)}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return task_id

def start_diagnostico(db_engine) -> str:
    """Lanza el diagnóstico de infactibilidad en un thread aparte y devuelve task_id."""
    task_id = str(uuid.uuid4())[:8]
    progress_store[task_id] = {"status": "starting", "step": "init", "percent": 0, "message": "Iniciando diagnóstico..."}

    def _run():
        from sqlmodel import Session
        from engine.diagnostico import ejecutar_diagnostico

        with Session(db_engine) as session:
            try:
                _update_progress(task_id, "extracting", 10, "Leyendo base de datos...")
                datos = build_json_from_db(session)

                _update_progress(task_id, "validating", 20, "Validando integridad...")

                _update_progress(task_id, "preprocessing", 30, "Preprocesando estructuras...")
                datos_procesados = preprocesar(datos)

                def _on_progress(percent, message):
                    _update_progress(task_id, "diagnosing", percent, message)

                resultado = ejecutar_diagnostico(datos_procesados, datos, on_progress=_on_progress)

                progress_store[task_id] = {
                    "status": "done",
                    "step": "done",
                    "percent": 100,
                    "message": "Diagnóstico completado",
                    "resultado": resultado
                }
            except Exception as e:
                logger.exception("Error durante el diagnóstico")
                progress_store[task_id] = {"status": "error", "message": str(e)}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return task_id

def build_json_from_db(session: Session) -> dict:
    """Extrae datos de SQLite y construye el formato EXACTO que el motor CP-SAT espera."""
    datos = {
        "configuracion": {},
        "categorias": [],
        "cursos": [],
        "grados": [],
        "secciones": [],
        "profesores": [],
        "tutorias": {}
    }
    
    # --- Configuracion ---
    sedes = session.exec(select(Sedes)).all()
    turnos_db = session.exec(select(Turno)).all()
    dias_db = session.exec(select(Dias).order_by(Dias.orden)).all()
    
    nombres_dias = [d.nombre_dia for d in dias_db]
    nombres_turnos = [t.nombre for t in turnos_db] if turnos_db else ["Mañana", "Tarde"]
    
    datos["configuracion"] = {
        "sedes": [s.nombre_sede for s in sedes],
        "turnos": nombres_turnos,
        "dia_id_to_nombre": {d.id_dia: d.nombre_dia for d in dias_db},
        "turno_id_to_nombre": {t.id_turno: t.nombre for t in turnos_db}
    }
    
    # --- Categorías (Áreas) ---
    areas = session.exec(select(Areas)).all()
    for a in areas:
        datos["categorias"].append({
            "id": f"CAT_{a.id_area}",
            "nombre": a.nombre,
            "max_horas_dia": a.max_horas_dia
        })
        
    # --- Cursos ---
    cursos = session.exec(select(Cursos)).all()
    tutoria_id_bd = None
    for c in cursos:
        # El motor hardcodea TUT1 como ID de Tutoría
        cid = "TUT1" if "Tutoría" in c.nombre_curso else f"CUR_{c.id_curso}"
        if cid == "TUT1": tutoria_id_bd = c.id_curso
        
        datos["cursos"].append({
            "id": cid,
            "nombre": c.nombre_curso,
            "categoria_id": f"CAT_{c.id_area}",
            "requiere_espacio_unico": c.requiere_espacio_unico or False
        })
    
    # --- Grados (con horario_plantilla y cursos_requeridos) ---
    grados = session.exec(select(Grado)).all()
    for g in grados:
        planes = session.exec(
            select(PlanEstudio).where(PlanEstudio.id_grado == g.id_grado)
        ).all()
        
        configs = session.exec(
            select(GradoDiaConfig).where(GradoDiaConfig.id_grado == g.id_grado)
        ).all()
        
        if configs:
            horario_plantilla = {}
            for cfg in configs:
                dia_obj = session.get(Dias, cfg.id_dia)
                if dia_obj:
                    horario_plantilla[dia_obj.nombre_dia] = cfg.bloques_dia
        else:
            horario_plantilla = {d: 6 for d in nombres_dias}
        
        datos["grados"].append({
            "id": f"GRA_{g.id_grado}",
            "nombre": f"{g.numero}°",
            "cursos_requeridos": [
                {
                    "curso_id": "TUT1" if p.id_curso == tutoria_id_bd else f"CUR_{p.id_curso}",
                    "horas_semanales": p.horas_semanales
                } for p in planes
            ],
            "horario_plantilla": horario_plantilla
        })
        
    # --- Secciones ---
    secciones = session.exec(select(Seccion)).all()
    for s in secciones:
        sec_turnos = session.exec(
            select(SeccionTurno).where(SeccionTurno.id_seccion == s.id_seccion)
        ).all()
        
        if sec_turnos:
            disponibilidad = {}
            for st in sec_turnos:
                dia_obj = session.get(Dias, st.id_dia)
                turno_obj = session.get(Turno, st.id_turno)
                if dia_obj and turno_obj:
                    dia_nombre = dia_obj.nombre_dia
                    if dia_nombre not in disponibilidad:
                        disponibilidad[dia_nombre] = []
                    if turno_obj.nombre not in disponibilidad[dia_nombre]:
                        disponibilidad[dia_nombre].append(turno_obj.nombre)
        else:
            disponibilidad = {d: list(nombres_turnos) for d in nombres_dias}
        
        sede_nombre = "Sede A"
        if s.id_sede:
            sede_obj = session.get(Sedes, s.id_sede)
            if sede_obj:
                sede_nombre = sede_obj.nombre_sede
        
        datos["secciones"].append({
            "id": f"SEC_{s.id_seccion}",
            "nombre": f"{s.nombre}",
            "grado": f"GRA_{s.id_grado}",
            "sede": sede_nombre,
            "disponibilidad": disponibilidad
        })
        
    # --- Profesores ---
    profesores = session.exec(select(Profesores)).all()
    todos_los_dias = session.exec(select(Dias).order_by(Dias.orden)).all()
    
    # Mapas de IDs a nombres para convertir formato BD → formato motor
    dia_id_to_nombre = {d.id_dia: d.nombre_dia for d in todos_los_dias}
    turno_id_to_nombre = {t.id_turno: t.nombre for t in turnos_db}
    
    # Máx bloques por día desde grado_dia_config (NO de la tabla Bloque que es visual)
    all_grado_configs = session.exec(select(GradoDiaConfig)).all()
    max_bloques_por_dia = {}
    for cfg in all_grado_configs:
        dia_nombre = dia_id_to_nombre.get(cfg.id_dia)
        if dia_nombre and cfg.bloques_dia:
            if cfg.bloques_dia > max_bloques_por_dia.get(dia_nombre, 0):
                max_bloques_por_dia[dia_nombre] = cfg.bloques_dia
    
    for p in profesores:
        pcs = session.exec(
            select(ProfesorCurso).where(ProfesorCurso.id_profesor == p.id_profesor)
        ).all()
        
        # Sedes del profesor
        prof_sedes_db = session.exec(
            select(SedeProfesor).where(SedeProfesor.id_profesor == p.id_profesor)
        ).all()
        sedes_del_prof = []
        for ps_obj in prof_sedes_db:
            sede_obj = session.get(Sedes, ps_obj.id_sede)
            if sede_obj:
                sedes_del_prof.append(sede_obj.nombre_sede)
        if not sedes_del_prof:
            sedes_del_prof = [s.nombre_sede for s in sedes]
        
        # Grados habilitados del profesor
        grados_prof_db = session.exec(
            select(GradoProfesor).where(GradoProfesor.id_profesor == p.id_profesor)
        ).all()
        grados_habilitados = [f"GRA_{gp.id_grado}" for gp in grados_prof_db]
        # Fallback: si no tiene grados asignados, habilitarlo para todos
        if not grados_habilitados:
            grados_habilitados = [f"GRA_{g.id_grado}" for g in grados]
        
        # --- Disponibilidad: formato motor {dia: {turno: {sede: [bloques]}}} ---
        disp_records = session.exec(
            select(ProfesorDisponibilidad).where(ProfesorDisponibilidad.id_profesor == p.id_profesor)
        ).all()
        
        disponibilidad = {}
        if disp_records:
            grouped = defaultdict(set)
            for dr in disp_records:
                dia_n = dia_id_to_nombre.get(dr.id_dia)
                turno_n = turno_id_to_nombre.get(dr.id_turno)
                sede_obj = session.get(Sedes, dr.id_sede) if dr.id_sede else None
                sede_n = sede_obj.nombre_sede if sede_obj else "Sede A"
                
                if dia_n and turno_n:
                    grouped[(dia_n, turno_n, sede_n)].add(dr.nro_bloque)
            
            for (dia_n, turno_n, sede_n), bloques in grouped.items():
                if dia_n not in disponibilidad:
                    disponibilidad[dia_n] = {}
                if turno_n not in disponibilidad[dia_n]:
                    disponibilidad[dia_n][turno_n] = {}
                disponibilidad[dia_n][turno_n][sede_n] = sorted(bloques)
        else:
            # Fallback: disponible todos los días/turnos/sedes
            # Usa grado_dia_config para saber cuántos bloques tiene cada día
            for dia in todos_los_dias:
                dia_nombre = dia.nombre_dia
                max_b = max_bloques_por_dia.get(dia_nombre)
                if max_b is None:
                    continue  # Día sin configuración de grado, no generar
                slots = list(range(1, max_b + 1))
                disponibilidad[dia_nombre] = {}
                for t in turnos_db:
                    disponibilidad[dia_nombre][t.nombre] = {
                        sede: list(slots) for sede in sedes_del_prof
                    }
        
        # --- Disponibilidad Preferente (clave que el preprocessor busca) ---
        pref_records = session.exec(
            select(ProfesorPreferencia).where(ProfesorPreferencia.id_profesor == p.id_profesor)
        ).all()
        
        prof_data = {
            "id": f"PROF_{p.id_profesor}",
            "nombre": p.nombre_profesor,
            "cursos_habilitados": ["TUT1" if pc.id_curso == tutoria_id_bd else f"CUR_{pc.id_curso}" for pc in pcs],
            "grados_habilitados": grados_habilitados,
            "disponibilidad": disponibilidad,
            "horas_minimas": p.horas_minimas or 6
        }
        
        if pref_records:
            grouped_pref = defaultdict(set)
            for pr in pref_records:
                dia_n = dia_id_to_nombre.get(pr.id_dia)
                turno_n = turno_id_to_nombre.get(pr.id_turno)
                sede_obj = session.get(Sedes, pr.id_sede) if pr.id_sede else None
                sede_n = sede_obj.nombre_sede if sede_obj else "Sede A"
                
                if dia_n and turno_n:
                    grouped_pref[(dia_n, turno_n, sede_n)].add(pr.nro_bloque)
            
            disponibilidad_preferente = {}
            for (dia_n, turno_n, sede_n), bloques in grouped_pref.items():
                if dia_n not in disponibilidad_preferente:
                    disponibilidad_preferente[dia_n] = {}
                if turno_n not in disponibilidad_preferente[dia_n]:
                    disponibilidad_preferente[dia_n][turno_n] = {}
                disponibilidad_preferente[dia_n][turno_n][sede_n] = sorted(bloques)
            prof_data["disponibilidad_preferente"] = disponibilidad_preferente
        
        datos["profesores"].append(prof_data)
    
    # --- Tutorías ---
    tutorias_db = session.exec(select(Tutoria)).all()
    for t in tutorias_db:
        datos["tutorias"][f"SEC_{t.id_seccion}"] = f"PROF_{t.id_profesor}"
    
    # --- Bloques Reservados ---
    reservas_db = session.exec(select(BloqueReservado)).all()
    bloques_reservados_lista = []
    for r in reservas_db:
        sede_obj = session.get(Sedes, r.id_sede)
        dia_obj = session.get(Dias, r.id_dia)
        turno_obj = session.get(Turno, r.id_turno)
        
        if not (sede_obj and dia_obj and turno_obj):
            continue
        
        # Grados afectados
        bg_list = session.exec(select(BloqueGrado).where(BloqueGrado.id_bloque_reservado == r.id_bloque_reservado)).all()
        grados_afectados = [f"GRA_{bg.id_grado}" for bg in bg_list] if bg_list else None
        
        # Opciones de slots
        opciones_db = session.exec(select(BloqueOpcion).where(BloqueOpcion.id_bloque_reservado == r.id_bloque_reservado)).all()
        opciones_slots = []
        for op in opciones_db:
            slots_db = session.exec(select(BloqueOpcionSlot).where(BloqueOpcionSlot.id_bloque_opcion == op.id_bloque_opcion)).all()
            opciones_slots.append([s.nro_bloque for s in slots_db])
        
        bloques_reservados_lista.append({
            "sede": sede_obj.nombre_sede,
            "dia": dia_obj.nombre_dia,
            "turno": turno_obj.nombre,
            "grados_afectados": grados_afectados,
            "opciones_slots": opciones_slots
        })
    
    datos["bloques_reservados"] = bloques_reservados_lista
        
    return datos

def _aplanar_asignaciones(asignaciones: list) -> list:
    """Convierte los bloques agrupados del solver en slots individuales (1 slot = 1 hora).
    El módulo engine/metrics.py espera este formato plano."""
    planas = []
    for bloque in asignaciones:
        start_slot = bloque.get("slot_inicio", 0)
        horas = bloque.get("horas", 1)
        for k in range(horas):
            planas.append({
                "seccion_id": bloque["seccion_id"],
                "curso_id": bloque["curso_id"],
                "profesor_id": bloque["profesor_id"],
                "dia": bloque["dia"],
                "turno": bloque.get("turno", "Mañana"),
                "slot": start_slot + k + 1
            })
    return planas


def generar_horario_engine(session: Session, task_id: str = None) -> dict:
    """Proceso completo con reporte de progreso."""
    logger.info("Iniciando generación de horario...")

    _update_progress(task_id, "extracting", 10, "Leyendo base de datos...")
    datos = build_json_from_db(session)

    _update_progress(task_id, "validating", 20, "Validando integridad...")

    try:
        _update_progress(task_id, "preprocessing", 35, "Construyendo estructuras...")
        datos_procesados = preprocesar(datos)

        _update_progress(task_id, "modeling", 50, "Generando restricciones CP-SAT...")
        modelo, variables_x, dict_diagnostico = construir_modelo(datos_procesados)

        _update_progress(task_id, "solving", 65, "Buscando solución óptima...")
        dict_resultado = resolver_modelo(modelo, variables_x)

        if dict_resultado.get("estado") in ("OPTIMAL", "FEASIBLE") and dict_resultado.get("asignaciones"):
            # --- Calcular métricas del motor (en memoria) ---
            _update_progress(task_id, "metrics", 80, "Calculando métricas del motor...")
            metricas_dict = None
            try:
                asignaciones_planas = _aplanar_asignaciones(dict_resultado["asignaciones"])
                metricas_dict = _calcular_metricas_motor(asignaciones_planas, datos_procesados)
                dict_resultado["metricas_motor"] = metricas_dict
                logger.info("Métricas del motor calculadas exitosamente")
            except Exception as e:
                logger.warning("No se pudieron calcular las métricas del motor: %s", str(e))
                dict_resultado["metricas_motor"] = None

            _update_progress(task_id, "saving", 90, "Persistiendo horario...")
            _guardar_horario(session, dict_resultado["asignaciones"])
            _guardar_snapshot(session, dict_resultado, metricas_dict=metricas_dict)
        else:
            logger.warning("Solver no encontró solución: %s", dict_resultado.get("estado"))

        # Escritura atómica: status + resultado juntos
        if task_id:
            progress_store[task_id] = {
                "status": "done",
                "step": "done",
                "percent": 100,
                "message": "¡Horario generado!",
                "resultado": dict_resultado
            }
            logger.info("progress_store[%s] = done (asignaciones=%d)", task_id, len(dict_resultado.get("asignaciones", [])))

        return {
            "status": "success",
            "resultado": dict_resultado
        }
    except ValidationError:
        raise
    except Exception as e:
        logger.exception("Error inesperado durante la generación")
        if task_id:
            progress_store[task_id] = {"status": "error", "message": str(e)}
        raise EngineError(message=f"Error durante la ejecución del motor: {str(e)}")

def _guardar_horario(session: Session, asignaciones: list):
    """Persiste las asignaciones del motor en la tabla horario_final."""
    from backend.models import HorarioFinal
    
    old = session.exec(select(HorarioFinal)).all()
    for o in old:
        session.delete(o)
    session.commit()
    
    dias_db = session.exec(select(Dias)).all()
    dia_map = {d.nombre_dia: d.id_dia for d in dias_db}
    
    turnos_db = session.exec(select(Turno)).all()
    turno_map = {t.nombre: t.id_turno for t in turnos_db}
    
    for asig in asignaciones:
        sec_id = int(asig["seccion_id"].replace("SEC_", ""))
        
        # Inversa del TUT1:
        if asig["curso_id"] == "TUT1":
            from backend.models import Cursos
            tut_curso = session.exec(select(Cursos).where(Cursos.nombre_curso.like("%Tutoría%"))).first()
            cur_id = tut_curso.id_curso if tut_curso else 18

        else:
            cur_id = int(asig["curso_id"].replace("CUR_", ""))
            
        prof_id = int(asig["profesor_id"].replace("PROF_", ""))
        id_dia = dia_map.get(asig["dia"])
        id_turno = turno_map.get(asig.get("turno", "Mañana"))
        
        slot_inicio = asig.get("slot_inicio", 0)
        horas = asig.get("horas", 1)
        
        for i in range(horas):
            num_bloque = slot_inicio + i + 1
            
            session.add(HorarioFinal(
                id_seccion=sec_id,
                id_dia=id_dia,
                num_bloque=num_bloque,
                id_turno=id_turno,
                id_curso=cur_id,
                id_profesor=prof_id
            ))
    
    session.commit()


def _guardar_snapshot(session: Session, dict_resultado: dict, es_editada: bool = False, metricas_dict: dict = None):
    """Guarda un snapshot del horario generado, opcionalmente con métricas."""
    old_active = session.exec(select(HorarioSnapshot).where(HorarioSnapshot.is_active == True)).all()
    for o in old_active:
        o.is_active = False
        session.add(o)

    now = datetime.now()
    existing_count = len(session.exec(select(HorarioSnapshot)).all())
    version = existing_count + 1
    if es_editada:
        nombre = f"Horario Editado v{version} - {now.strftime('%d/%m %H:%M')}"
    else:
        nombre = f"Horario v{version} - {now.strftime('%d/%m %H:%M')}"

    snapshot = HorarioSnapshot(
        nombre=nombre,
        json_data=json.dumps(dict_resultado, ensure_ascii=False),
        json_metricas=json.dumps(metricas_dict, ensure_ascii=False) if metricas_dict else None,
        asignaciones_count=len(dict_resultado.get("asignaciones", [])),
        estado=dict_resultado.get("estado"),
        tiempo_segundos=dict_resultado.get("estadisticas", {}).get("tiempo_segundos"),
        is_active=True,
        es_editada=es_editada,
        created_at=now.isoformat()
    )
    session.add(snapshot)
    session.commit()
    logger.info("Snapshot guardado: %s", nombre)

    dict_resultado["version"] = version
    dict_resultado["nombre"] = nombre


def _detect_gaps(session: Session, seccion_id: int, dia_id: int, turno_id: int) -> list:
    """Detecta huecos (bloques vacíos entre ocupados) en un día para una sección."""
    rows = session.exec(
        select(HorarioFinal).where(
            HorarioFinal.id_seccion == seccion_id,
            HorarioFinal.id_dia == dia_id,
            HorarioFinal.id_turno == turno_id
        ).order_by(HorarioFinal.num_bloque)
    ).all()
    if not rows:
        return []
    bloques = sorted(set(r.num_bloque for r in rows))
    if len(bloques) < 2:
        return []
    gaps = []
    for i in range(bloques[0], bloques[-1] + 1):
        if i not in bloques:
            gaps.append(i)
    return gaps


def _get_profesor_name(session: Session, profesor_id: int) -> str:
    prof = session.get(Profesores, profesor_id)
    return prof.nombre_profesor if prof else f"Profesor {profesor_id}"


def _get_seccion_name(session: Session, seccion_id: int) -> str:
    sec = session.get(Seccion, seccion_id)
    return sec.nombre if sec else f"Sección {seccion_id}"


def _get_dia_name(session: Session, dia_id: int) -> str:
    dia = session.get(Dias, dia_id)
    return dia.nombre_dia if dia else f"Día {dia_id}"


def _get_turno_name(session: Session, turno_id: int) -> str:
    turno = session.get(Turno, turno_id)
    return turno.nombre if turno else f"Turno {turno_id}"


def _getCurso_name(session: Session, curso_id: int) -> str:
    if curso_id == 0:
        return "Tutoría"
    curso = session.get(Cursos, curso_id)
    return curso.nombre_curso if curso else f"Curso {curso_id}"


def validate_move(session: Session, data: dict) -> dict:
    """
    Valida un movimiento propuesto de una asignación.
    Soporta swaps: si el destino está ocupado, verifica si la asignación
    que está ahí puede ir al origen (intercambio).
    Retorna { valid, conflicts, warnings, isSwap, swapInfo }
    """
    sec_id = data["seccion_id"]
    cur_id = data["curso_id"]
    prof_id = data["profesor_id"]
    dia_origen_id = data["dia_origen_id"]
    turno_origen_id = data["turno_origen_id"]
    slot_origen = data["slot_inicio_origen"]
    horas_origen = data["horas_origen"]
    dia_destino_id = data["dia_destino_id"]
    turno_destino_id = data["turno_destino_id"]
    slot_destino = data["slot_inicio_destino"]
    horas_destino = data["horas_destino"]

    conflicts = []
    warnings = []
    is_swap = False
    swap_info = None

    prof_name = _get_profesor_name(session, prof_id)
    sec_name = _get_seccion_name(session, sec_id)
    dia_orig_name = _get_dia_name(session, dia_origen_id)
    dia_dest_name = _get_dia_name(session, dia_destino_id)
    turno_dest_name = _get_turno_name(session, turno_destino_id)

    existing_at_dest = []
    for i in range(horas_destino):
        bloque_dest = slot_destino + i + 1
        exist = session.exec(
            select(HorarioFinal).where(
                HorarioFinal.id_dia == dia_destino_id,
                HorarioFinal.id_turno == turno_destino_id,
                HorarioFinal.num_bloque == bloque_dest
            )
        ).all()
        for ex in exist:
            if ex.id_seccion == sec_id and ex.id_curso == cur_id and ex.id_profesor == prof_id:
                continue
            if ex.id_seccion != sec_id:
                continue
            existing_at_dest.append(ex)

    if existing_at_dest:
        dest_assignment = existing_at_dest[0]
        swap_sec = session.get(Seccion, dest_assignment.id_seccion)
        swap_curso = session.get(Cursos, dest_assignment.id_curso)
        swap_prof = session.get(Profesores, dest_assignment.id_profesor)
        swap_dia = session.get(Dias, dest_assignment.id_dia)
        swap_turno = session.get(Turno, dest_assignment.id_turno)

        swap_conflicts = []

        for i in range(horas_origen):
            bloque_orig = slot_origen + i + 1
            prof_swap_at_orig = session.exec(
                select(HorarioFinal).where(
                    HorarioFinal.id_profesor == dest_assignment.id_profesor,
                    HorarioFinal.id_dia == dia_origen_id,
                    HorarioFinal.id_turno == turno_origen_id,
                    HorarioFinal.num_bloque == bloque_orig
                )
            ).first()
            if prof_swap_at_orig and not (
                prof_swap_at_orig.id_seccion == sec_id and
                prof_swap_at_orig.id_curso == cur_id and
                prof_swap_at_orig.id_profesor == prof_id
            ):
                conflict_sec = session.get(Seccion, prof_swap_at_orig.id_seccion)
                conflict_curso = session.get(Cursos, prof_swap_at_orig.id_curso)
                swap_conflicts.append(
                    f"{swap_prof.nombre_profesor if swap_prof else '?'} ya tiene clase de "
                    f"{conflict_curso.nombre_curso if conflict_curso else '?'} con "
                    f"{conflict_sec.nombre if conflict_sec else '?'} en "
                    f"{dia_orig_name} Bloque {bloque_orig}"
                )

        sec_swap_at_orig = session.exec(
            select(HorarioFinal).where(
                HorarioFinal.id_seccion == dest_assignment.id_seccion,
                HorarioFinal.id_dia == dia_origen_id,
                HorarioFinal.id_turno == turno_origen_id,
                HorarioFinal.num_bloque >= slot_origen + 1,
                HorarioFinal.num_bloque <= slot_origen + horas_origen
            )
        ).first()
        if sec_swap_at_orig and not (
            sec_swap_at_orig.id_curso == cur_id and
            sec_swap_at_orig.id_profesor == prof_id
        ):
            conflict_curso_sec = session.get(Cursos, sec_swap_at_orig.id_curso)
            swap_conflicts.append(
                f"{swap_sec.nombre if swap_sec else '?'} ya tiene clase de "
                f"{conflict_curso_sec.nombre_curso if conflict_curso_sec else '?'} en "
                f"{dia_orig_name} Bloque {sec_swap_at_orig.num_bloque}"
            )

        for i in range(horas_destino):
            bloque_dest = slot_destino + i + 1
            prof_orig_at_dest = session.exec(
                select(HorarioFinal).where(
                    HorarioFinal.id_profesor == prof_id,
                    HorarioFinal.id_dia == dia_destino_id,
                    HorarioFinal.id_turno == turno_destino_id,
                    HorarioFinal.num_bloque == bloque_dest
                )
            ).first()
            if prof_orig_at_dest and not (
                prof_orig_at_dest.id_seccion == sec_id and
                prof_orig_at_dest.id_curso == cur_id and
                prof_orig_at_dest.id_profesor == prof_id
            ):
                conflict_sec_dest = session.get(Seccion, prof_orig_at_dest.id_seccion)
                conflict_curso_dest = session.get(Cursos, prof_orig_at_dest.id_curso)
                swap_conflicts.append(
                    f"{prof_name} ya tiene clase de "
                    f"{conflict_curso_dest.nombre_curso if conflict_curso_dest else '?'} con "
                    f"{conflict_sec_dest.nombre if conflict_sec_dest else '?'} en "
                    f"{dia_dest_name} Bloque {bloque_dest}"
                )

        if not swap_conflicts:
            is_swap = True
            swap_info = {
                "swap_seccion_id": dest_assignment.id_seccion,
                "swap_curso_id": dest_assignment.id_curso,
                "swap_profesor_id": dest_assignment.id_profesor,
                "swap_dia_id": dest_assignment.id_dia,
                "swap_turno_id": dest_assignment.id_turno,
                "swap_slot": dest_assignment.num_bloque - 1,
                "swap_horas": len(set(e.num_bloque for e in existing_at_dest)),
                "swap_seccion_nombre": swap_sec.nombre if swap_sec else "?",
                "swap_curso_nombre": swap_curso.nombre_curso if swap_curso else "?",
                "swap_profesor_nombre": swap_prof.nombre_profesor if swap_prof else "?",
                "swap_dia_nombre": swap_dia.nombre_dia if swap_dia else "?",
                "swap_turno_nombre": swap_turno.nombre if swap_turno else "?",
            }
        else:
            for c in swap_conflicts:
                conflicts.append(c)
    else:
        for i in range(horas_destino):
            bloque_dest = slot_destino + i + 1
            exist_prof = session.exec(
                select(HorarioFinal).where(
                    HorarioFinal.id_profesor == prof_id,
                    HorarioFinal.id_dia == dia_destino_id,
                    HorarioFinal.id_turno == turno_destino_id,
                    HorarioFinal.num_bloque == bloque_dest
                )
            ).first()
            if exist_prof and not (
                exist_prof.id_seccion == sec_id and
                exist_prof.id_curso == cur_id
            ):
                sec_orig = session.get(Seccion, exist_prof.id_seccion)
                curso_conflict = session.get(Cursos, exist_prof.id_curso)
                conflicts.append(
                    f"{prof_name} ya tiene clase de {curso_conflict.nombre_curso if curso_conflict else '?'} "
                    f"con {sec_orig.nombre if sec_orig else '?'} en "
                    f"{dia_dest_name} {turno_dest_name} Bloque {bloque_dest}"
                )

            exist_sec = session.exec(
                select(HorarioFinal).where(
                    HorarioFinal.id_seccion == sec_id,
                    HorarioFinal.id_dia == dia_destino_id,
                    HorarioFinal.id_turno == turno_destino_id,
                    HorarioFinal.num_bloque == bloque_dest
                )
            ).first()
            if exist_sec and not (
                exist_sec.id_curso == cur_id and
                exist_sec.id_profesor == prof_id
            ):
                curso_exist = session.get(Cursos, exist_sec.id_curso)
                conflicts.append(
                    f"{sec_name} ya tiene {curso_exist.nombre_curso if curso_exist else '?'} "
                    f"en {dia_dest_name} {turno_dest_name} Bloque {bloque_dest}"
                )

    disp = session.exec(
        select(ProfesorDisponibilidad).where(
            ProfesorDisponibilidad.id_profesor == prof_id,
            ProfesorDisponibilidad.id_dia == dia_destino_id,
            ProfesorDisponibilidad.id_turno == turno_destino_id
        )
    ).all()
    bloques_disp = set(d.nro_bloque for d in disp)
    for i in range(horas_destino):
        bloque_dest = slot_destino + i + 1
        if bloques_disp and bloque_dest not in bloques_disp:
            warnings.append(
                f"{prof_name} no tiene disponibilidad en {dia_dest_name} {turno_dest_name} Bloque {bloque_dest}"
            )
            break

    vinculo = session.exec(
        select(ProfesorCurso).where(
            ProfesorCurso.id_profesor == prof_id,
            ProfesorCurso.id_curso == cur_id
        )
    ).first()
    if not vinculo:
        curso_name = _getCurso_name(session, cur_id)
        warnings.append(f"{prof_name} no está vinculado al curso {curso_name}")

    gaps_origen = _detect_gaps(session, sec_id, dia_origen_id, turno_origen_id)
    if gaps_origen:
        warnings.append(
            f"Se detecta(n) hueco(s) en {dia_orig_name} para {sec_name}: Bloque(s) {', '.join(str(g) for g in gaps_origen)}"
        )

    if dia_destino_id != dia_origen_id:
        gaps_destino = _detect_gaps(session, sec_id, dia_destino_id, turno_destino_id)
        if gaps_destino:
            warnings.append(
                f"Se detecta(n) hueco(s) en {dia_dest_name} para {sec_name}: Bloque(s) {', '.join(str(g) for g in gaps_destino)}"
            )

    all_prof_rows = session.exec(
        select(HorarioFinal).where(HorarioFinal.id_profesor == prof_id)
    ).all()
    dias_db_map = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    carga_por_dia = {}
    for r in all_prof_rows:
        nombre_dia = dias_db_map.get(r.id_dia, f"Dia_{r.id_dia}")
        carga_por_dia[nombre_dia] = carga_por_dia.get(nombre_dia, 0) + 1
    carga_por_dia[dia_orig_name] = carga_por_dia.get(dia_orig_name, 0) - horas_origen
    carga_por_dia[dia_dest_name] = carga_por_dia.get(dia_dest_name, 0) + horas_destino
    carga_por_dia = {d: h for d, h in carga_por_dia.items() if h > 0}
    if carga_por_dia:
        promedio = sum(carga_por_dia.values()) / len(carga_por_dia)
        for dia_carga, horas_dia in carga_por_dia.items():
            if promedio > 0 and horas_dia > promedio * 1.5 and horas_dia > 3:
                warnings.append(
                    f"{prof_name} quedaría con {horas_dia}h en {dia_carga} "
                    f"(promedio: {promedio:.1f}h/día) — carga desbalanceada"
                )

    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings,
        "isSwap": is_swap,
        "swapInfo": swap_info
    }


def build_horario_summary(session: Session) -> dict:
    """Genera un resumen condensado del horario activo, consumiendo métricas del motor."""
    engine_metrics = calcular_metricas_motor(session)
    if "error" in engine_metrics:
        return {"error": engine_metrics["error"]}
        
    all_rows = session.exec(select(HorarioFinal)).all()
    if not all_rows:
        return {"error": "No hay horario generado"}

    dias_db = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    turnos_db = {t.id_turno: t.nombre for t in session.exec(select(Turno)).all()}
    cursos_db = {c.id_curso: c.nombre_curso for c in session.exec(select(Cursos)).all()}
    profs_db = {p.id_profesor: p.nombre_profesor for p in session.exec(select(Profesores)).all()}
    secs_db = {s.id_seccion: s.nombre for s in session.exec(select(Seccion)).all()}

    snapshot = session.exec(select(HorarioSnapshot).where(HorarioSnapshot.is_active == True)).first()
    metricas = {"estado": "N/A", "tiempo_segundos": 0, "ramas_exploradas": 0, "conflictos": 0}
    if snapshot and snapshot.json_data:
        try:
            snap = json.loads(snapshot.json_data)
            metricas = snap.get("estadisticas", metricas)
            metricas["estado"] = snap.get("estado", snapshot.estado or "N/A")
        except Exception:
            metricas["estado"] = snapshot.estado or "N/A"
            metricas["tiempo_segundos"] = snapshot.tiempo_segundos or 0

    from collections import defaultdict
    carga_sec = defaultdict(lambda: {"total": 0, "dias": defaultdict(int), "cursos": set()})
    carga_turno = defaultdict(int)

    # Solo agrupamos secciones y turnos desde DB, profesores y dias vienen del engine
    for r in all_rows:
        d_name = dias_db.get(r.id_dia, f"D{r.id_dia}")
        t_name = turnos_db.get(r.id_turno, f"T{r.id_turno}")
        c_name = cursos_db.get(r.id_curso, f"C{r.id_curso}")
        s_name = secs_db.get(r.id_seccion, f"S{r.id_seccion}")

        carga_sec[s_name]["total"] += 1
        carga_sec[s_name]["dias"][d_name] += 1
        carga_sec[s_name]["cursos"].add(c_name)
        carga_turno[t_name] += 1

    # Construir resumen de profesores desde las métricas del motor
    resumen_profesores = []
    for p_id_str, p_data in engine_metrics.get("profesores", {}).items():
        try:
            p_id = int(p_id_str.split('_')[1])
            p_name = profs_db.get(p_id, p_id_str)
        except Exception:
            p_name = p_id_str

        dias = {d: len(secs) for d, secs in p_data.get("carga_diaria", {}).items() if len(secs) > 0}
        
        cursos_nombres = []
        for c in p_data.get("cursos_dictados", []):
            if c == "TUT1":
                cursos_nombres.append("Tutoría")
            elif c.startswith("CUR_"):
                try:
                    cursos_nombres.append(cursos_db.get(int(c.split('_')[1]), c))
                except Exception:
                    cursos_nombres.append(c)

        secciones_nombres = []
        for s in p_data.get("secciones_asignadas", []):
            try:
                secciones_nombres.append(secs_db.get(int(s.split('_')[1]), s))
            except Exception:
                secciones_nombres.append(s)

        resumen_profesores.append({
            "nombre": p_name,
            "horas_semana": p_data.get("total_horas_semanales", 0),
            "dias": dias,
            "cursos": cursos_nombres,
            "secciones": secciones_nombres
        })
        
    resumen_profesores.sort(key=lambda x: -x["horas_semana"])

    resumen_secciones = []
    for s_name, data in sorted(carga_sec.items(), key=lambda x: -x[1]["total"]):
        resumen_secciones.append({
            "nombre": s_name,
            "clases": data["total"],
            "dias": dict(data["dias"]),
            "cursos": list(data["cursos"])
        })

    carga_dia = {}
    if "kpis" in engine_metrics and "utilizacion" in engine_metrics["kpis"]:
        for d, data in engine_metrics["kpis"]["utilizacion"]["densidad_diaria"].items():
            if data["slots_ocupados"] > 0:
                carga_dia[d] = data["slots_ocupados"]

    return {
        "metricas": {
            "estado": metricas.get("estado", "N/A"),
            "tiempo_segundos": round(metricas.get("tiempo_segundos", 0), 2),
            "ramas_exploradas": metricas.get("ramas_exploradas", 0),
            "conflictos": metricas.get("conflictos", 0),
            "total_clases": engine_metrics.get("resumen_slots", {}).get("total_ocupados", len(all_rows)),
            "total_profesores": len(resumen_profesores),
            "total_secciones": len(resumen_secciones)
        },
        "carga_por_dia": carga_dia,
        "carga_por_turno": dict(carga_turno),
        "profesores": resumen_profesores,
        "secciones": resumen_secciones
    }


def build_horario_analysis(session: Session) -> dict:
    """Genera análisis del horario con métricas explicadas, problemas y sugerencias."""
    summary = build_horario_summary(session)
    if "error" in summary:
        return {"error": summary["error"]}

    metricas = summary["metricas"]
    explicaciones_metricas = []

    if metricas["estado"] == "OPTIMAL":
        explicaciones_metricas.append(
            "OPTIMAL: El solver encontró la mejor solución posible. "
            "No existe otro horario que satisfaga mejor todas las restricciones."
        )
    elif metricas["estado"] == "FEASIBLE":
        explicaciones_metricas.append(
            "FEASIBLE: Se encontró una solución válida, pero no se puede garantizar "
            "que sea la mejor posible. El solver podría mejorarla con más tiempo."
        )
    elif metricas["estado"] == "INFEASIBLE":
        explicaciones_metricas.append(
            "INFEASIBLE: Las restricciones son contradictorias. "
            "No es posible generar un horario válido con las condiciones actuales."
        )
    elif metricas["estado"] == "UNKNOWN":
        explicaciones_metricas.append(
            "UNKNOWN: El solver no encontró solución antes del límite de tiempo."
        )

    if metricas["tiempo_segundos"] > 0:
        explicaciones_metricas.append(
            f"Tiempo de cálculo: {metricas['tiempo_segundos']}s. "
            f"{'Rápido' if metricas['tiempo_segundos'] < 5 else 'Moderado' if metricas['tiempo_segundos'] < 30 else 'Lento'} "
            f"para el tamaño del problema."
        )

    if metricas["ramas_exploradas"] > 0:
        explicaciones_metricas.append(
            f"El algoritmo exploró {metricas['ramas_exploradas']:,} alternativas antes de encontrar la solución. "
            f"{'Pocas alternativas (problema simple)' if metricas['ramas_exploradas'] < 100 else 'Cantidad moderada' if metricas['ramas_exploradas'] < 1000 else 'Muchas alternativas (problema complejo)'}."
        )

    problemas = []
    sugerencias = []

    for prof in summary["profesores"]:
        dias = prof["dias"]
        if dias:
            promedio = prof["horas_semana"] / len(dias)
            for dia, horas in dias.items():
                if promedio > 0 and horas > promedio * 1.5 and horas > 3:
                    problemas.append(
                        f"{prof['nombre']}: {horas}h en {dia} (promedio {promedio:.1f}h/día)"
                    )
                    sugerencias.append(
                        f"Mover 1-2 horas de {prof['nombre']} desde {dia} a otro día con menos carga"
                    )

    for sec in summary["secciones"]:
        dias = sec["dias"]
        if dias:
            promedio_sec = sec["clases"] / len(dias)
            for dia, horas in dias.items():
                if promedio_sec > 0 and horas > promedio_sec * 1.3 and horas > 8:
                    problemas.append(
                        f"{sec['nombre']}: {horas}h en {dia} (promedio {promedio_sec:.1f}h/día)"
                    )
                    sugerencias.append(
                        f"Redistribuir materias de {sec['nombre']} en {dia} a otros días"
                    )

    if len(summary["profesores"]) > 0:
        max_prof = summary["profesores"][0]
        min_prof = summary["profesores"][-1]
        if max_prof["horas_semana"] > min_prof["horas_semana"] * 2.5:
            problemas.append(
                f"Desequilibrio entre profesores: {max_prof['nombre']} ({max_prof['horas_semana']}h) "
                f"vs {min_prof['nombre']} ({min_prof['horas_semana']}h)"
            )
            sugerencias.append(
                f"Evaluar si se pueden redistribuir clases de {max_prof['nombre']} "
                f"a otros profesores disponibles"
            )

    return {
        "metricas": metricas,
        "explicaciones_metricas": explicaciones_metricas,
        "problemas_detectados": problemas,
        "sugerencias": list(dict.fromkeys(sugerencias)),
        "resumen_rapido": {
            "total_clases": metricas["total_clases"],
            "profesor_mas_cargado": summary["profesores"][0]["nombre"] if summary["profesores"] else "N/A",
            "seccion_con_mas_clases": summary["secciones"][0]["nombre"] if summary["secciones"] else "N/A",
            "dia_mas_ocupado": max(summary["carga_por_dia"], key=summary["carga_por_dia"].get) if summary["carga_por_dia"] else "N/A"
        }
    }


def build_current_state(session: Session) -> dict:
    """Lee horario_final de la BD y construye el dict resultado actual."""
    all_rows = session.exec(select(HorarioFinal)).all()
    dias_db = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    turnos_db = {t.id_turno: t.nombre for t in session.exec(select(Turno)).all()}

    from collections import defaultdict
    grupos = defaultdict(list)
    for r in all_rows:
        key = (r.id_seccion, r.id_curso, r.id_profesor, r.id_dia, r.id_turno)
        grupos[key].append(r.num_bloque)

    asignaciones = []
    for (s_id, c_id, p_id, d_id, t_id), bloques in grupos.items():
        bloques_ord = sorted(bloques)
        if not bloques_ord:
            continue
        groups = []
        current_group = [bloques_ord[0]]
        for i in range(1, len(bloques_ord)):
            if bloques_ord[i] == current_group[-1] + 1:
                current_group.append(bloques_ord[i])
            else:
                groups.append(current_group)
                current_group = [bloques_ord[i]]
        groups.append(current_group)

        for group in groups:
            slot_inicio = group[0] - 1
            horas = len(group)
            cid_str = "TUT1" if c_id == 0 else f"CUR_{c_id}"
            asignaciones.append({
                "seccion_id": f"SEC_{s_id}",
                "curso_id": cid_str,
                "profesor_id": f"PROF_{p_id}",
                "dia": dias_db.get(d_id, f"Dia_{d_id}"),
                "turno": turnos_db.get(t_id, "Manana"),
                "slot_inicio": slot_inicio,
                "horas": horas
            })

    return {
        "estado": "EDITADO",
        "mensaje": "Horario editado manualmente",
        "estadisticas": {"tiempo_segundos": 0, "ramas_exploradas": 0, "conflictos": 0},
        "asignaciones": asignaciones
    }


def apply_move(session: Session, data: dict) -> dict:
    """
    Aplica un movimiento validado: borra filas viejas, crea filas nuevas, crea snapshot.
    Soporta swaps.
    """
    sec_id = data["seccion_id"]
    cur_id = data["curso_id"]
    prof_id = data["profesor_id"]
    dia_origen_id = data["dia_origen_id"]
    turno_origen_id = data["turno_origen_id"]
    slot_origen = data["slot_inicio_origen"]
    horas_origen = data["horas_origen"]
    dia_destino_id = data["dia_destino_id"]
    turno_destino_id = data["turno_destino_id"]
    slot_destino = data["slot_inicio_destino"]
    horas_destino = data["horas_destino"]

    old_rows = session.exec(
        select(HorarioFinal).where(
            HorarioFinal.id_seccion == sec_id,
            HorarioFinal.id_dia == dia_origen_id,
            HorarioFinal.id_turno == turno_origen_id,
            HorarioFinal.id_curso == cur_id,
            HorarioFinal.id_profesor == prof_id,
            HorarioFinal.num_bloque >= slot_origen + 1,
            HorarioFinal.num_bloque <= slot_origen + horas_origen
        )
    ).all()
    for row in old_rows:
        session.delete(row)

    if data.get("isSwap") and data.get("swapInfo"):
        sw = data["swapInfo"]
        swap_rows = session.exec(
            select(HorarioFinal).where(
                HorarioFinal.id_seccion == sw["swap_seccion_id"],
                HorarioFinal.id_dia == sw["swap_dia_id"],
                HorarioFinal.id_turno == sw["swap_turno_id"],
                HorarioFinal.id_curso == sw["swap_curso_id"],
                HorarioFinal.id_profesor == sw["swap_profesor_id"],
                HorarioFinal.num_bloque >= sw["swap_slot"] + 1,
                HorarioFinal.num_bloque <= sw["swap_slot"] + sw["swap_horas"]
            )
        ).all()
        for row in swap_rows:
            session.delete(row)
        session.flush()

        for i in range(sw["swap_horas"]):
            num_bloque = slot_origen + i + 1
            session.add(HorarioFinal(
                id_seccion=sw["swap_seccion_id"],
                id_dia=dia_origen_id,
                num_bloque=num_bloque,
                id_curso=sw["swap_curso_id"],
                id_profesor=sw["swap_profesor_id"],
                id_turno=turno_origen_id
            ))
    else:
        session.flush()

    for i in range(horas_destino):
        num_bloque = slot_destino + i + 1
        session.add(HorarioFinal(
            id_seccion=sec_id,
            id_dia=dia_destino_id,
            num_bloque=num_bloque,
            id_curso=cur_id,
            id_profesor=prof_id,
            id_turno=turno_destino_id
        ))
    session.commit()

    all_rows = session.exec(select(HorarioFinal)).all()
    dias_db = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    turnos_db = {t.id_turno: t.nombre for t in session.exec(select(Turno)).all()}

    from collections import defaultdict
    grupos = defaultdict(list)
    for r in all_rows:
        key = (r.id_seccion, r.id_curso, r.id_profesor, r.id_dia, r.id_turno)
        grupos[key].append(r.num_bloque)

    asignaciones = []
    for (s_id, c_id, p_id, d_id, t_id), bloques in grupos.items():
        bloques_ord = sorted(bloques)
        if not bloques_ord:
            continue
        groups = []
        current_group = [bloques_ord[0]]
        for i in range(1, len(bloques_ord)):
            if bloques_ord[i] == current_group[-1] + 1:
                current_group.append(bloques_ord[i])
            else:
                groups.append(current_group)
                current_group = [bloques_ord[i]]
        groups.append(current_group)

        for group in groups:
            slot_inicio = group[0] - 1
            horas = len(group)
            cid_str = "TUT1" if c_id == 0 else f"CUR_{c_id}"
            asignaciones.append({
                "seccion_id": f"SEC_{s_id}",
                "curso_id": cid_str,
                "profesor_id": f"PROF_{p_id}",
                "dia": dias_db.get(d_id, f"Dia_{d_id}"),
                "turno": turnos_db.get(t_id, "Manana"),
                "slot_inicio": slot_inicio,
                "horas": horas
            })

    dict_resultado = {
        "estado": "EDITADO",
        "mensaje": "Horario editado manualmente",
        "estadisticas": {"tiempo_segundos": 0, "ramas_exploradas": 0, "conflictos": 0},
        "asignaciones": asignaciones
    }

    return dict_resultado


def calcular_metricas_motor(session: Session) -> dict:
    """Obtiene las métricas del motor sobre el horario activo actual.
    Primero intenta leer del snapshot persistido (json_metricas).
    Si no existe (snapshots pre-migración), recalcula en memoria."""
    
    # 1. Intentar leer del snapshot activo
    snapshot = session.exec(select(HorarioSnapshot).where(HorarioSnapshot.is_active == True)).first()
    if snapshot and snapshot.json_metricas:
        try:
            return json.loads(snapshot.json_metricas)
        except Exception:
            logger.warning("json_metricas corrupto en snapshot %s, recalculando...", snapshot.id_snapshot)
    
    # 2. Fallback: recalcular en memoria (snapshots antiguos sin json_metricas)
    all_rows = session.exec(select(HorarioFinal)).all()
    if not all_rows:
        return {"error": "No hay horario generado para calcular métricas"}
    
    dias_db = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    turnos_db = {t.id_turno: t.nombre for t in session.exec(select(Turno)).all()}
    
    grupos = defaultdict(list)
    for r in all_rows:
        key = (r.id_seccion, r.id_curso, r.id_profesor, r.id_dia, r.id_turno)
        grupos[key].append(r.num_bloque)
    
    asignaciones_bloques = []
    for (s_id, c_id, p_id, d_id, t_id), bloques in grupos.items():
        bloques_ord = sorted(bloques)
        if not bloques_ord:
            continue
        groups = []
        current_group = [bloques_ord[0]]
        for i in range(1, len(bloques_ord)):
            if bloques_ord[i] == current_group[-1] + 1:
                current_group.append(bloques_ord[i])
            else:
                groups.append(current_group)
                current_group = [bloques_ord[i]]
        groups.append(current_group)
        
        for group in groups:
            cid_str = "TUT1" if c_id == 0 else f"CUR_{c_id}"
            asignaciones_bloques.append({
                "seccion_id": f"SEC_{s_id}",
                "curso_id": cid_str,
                "profesor_id": f"PROF_{p_id}",
                "dia": dias_db.get(d_id, f"Dia_{d_id}"),
                "turno": turnos_db.get(t_id, "Manana"),
                "slot_inicio": group[0] - 1,
                "horas": len(group)
            })
    
    asignaciones_planas = _aplanar_asignaciones(asignaciones_bloques)
    
    try:
        datos = build_json_from_db(session)
        datos_procesados = preprocesar(datos)
    except Exception as e:
        logger.warning("No se pudo reconstruir datos_procesados: %s", str(e))
        return {"error": f"No se pudieron reconstruir los datos procesados: {str(e)}"}
    
    try:
        metricas = _calcular_metricas_motor(asignaciones_planas, datos_procesados)
        return metricas
    except Exception as e:
        logger.exception("Error calculando métricas del motor")
        return {"error": f"Error calculando métricas: {str(e)}"}

