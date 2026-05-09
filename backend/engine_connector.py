from sqlmodel import Session, select
from backend.models import (
    Sedes, Dias, Areas, Cursos, Grado, Seccion, PlanEstudio, 
    Profesores, ProfesorCurso, GradoDiaConfig, SeccionTurno, Turno, Tutoria
)
from engine.preprocessor import preprocesar
from engine.model import construir_modelo
from engine.solver import resolver_modelo
from utils.validators import validar_todo

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
        "turnos": nombres_turnos
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
            "categoria_id": f"CAT_{c.id_area}"
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
    for p in profesores:
        pcs = session.exec(
            select(ProfesorCurso).where(ProfesorCurso.id_profesor == p.id_profesores)
        ).all()
        datos["profesores"].append({
            "id": f"PROF_{p.id_profesores}",
            "nombre": p.nombre_profesor,
            "cursos_habilitados": ["TUT1" if pc.id_curso == tutoria_id_bd else f"CUR_{pc.id_curso}" for pc in pcs],
            "max_horas_dia": 6,
            "disponibilidad": {d: list(nombres_turnos) for d in nombres_dias}
        })
    
    # --- Tutorías ---
    tutorias_db = session.exec(select(Tutoria)).all()
    for t in tutorias_db:
        datos["tutorias"][f"SEC_{t.id_seccion}"] = f"PROF_{t.id_profesor}"
        
    return datos

def generar_horario_engine(session: Session) -> dict:
    """Proceso completo: Extrae DB -> Valida -> Preprocesa -> Construye Modelo -> Resuelve -> Guarda."""
    try:
        datos = build_json_from_db(session)
        
        errores = validar_todo(datos)
        if errores:
            return {"status": "error", "errores": errores}
            
        datos_procesados = preprocesar(datos)
        modelo, variables_x = construir_modelo(datos_procesados)
        dict_resultado = resolver_modelo(modelo, variables_x)
        
        if dict_resultado.get("estado") in ("OPTIMAL", "FEASIBLE") and dict_resultado.get("asignaciones"):
            _guardar_horario(session, dict_resultado["asignaciones"])
        
        return {
            "status": "success", 
            "resultado": dict_resultado
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "errores": [str(e)]}


def _guardar_horario(session: Session, asignaciones: list):
    """Persiste las asignaciones del motor en la tabla horario_final."""
    from backend.models import HorarioFinal, Bloque
    
    old = session.exec(select(HorarioFinal)).all()
    for o in old:
        session.delete(o)
    session.commit()
    
    dias_db = session.exec(select(Dias)).all()
    dia_map = {d.nombre_dia: d.id_dia for d in dias_db}
    
    turnos_db = session.exec(select(Turno)).all()
    turno_map = {t.nombre: t.id_turno for t in turnos_db}
    
    bloques_db = session.exec(select(Bloque)).all()
    bloque_map = {}
    for b in bloques_db:
        bloque_map[(b.id_turno, b.numero_bloque)] = b.id_bloque
    
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
            id_bloque = bloque_map.get((id_turno, num_bloque))
            
            session.add(HorarioFinal(
                id_seccion=sec_id,
                id_dia=id_dia,
                id_bloque=id_bloque,
                id_curso=cur_id,
                id_profesor=prof_id
            ))
    
    session.commit()
