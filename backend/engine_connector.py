from sqlmodel import Session, select
from backend.models import Sedes, Dias, Areas, Cursos, Grado, Seccion, PlanEstudio, Profesores, ProfesorCurso
from engine.preprocessor import preprocesar
from engine.model import construir_modelo
from engine.solver import resolver_modelo
from utils.validators import validar_todo

def build_json_from_db(session: Session) -> dict:
    """Extrae datos de SQLite y construye el formato exacto que CP-SAT espera."""
    datos = {
        "configuracion": {},
        "categorias": [],
        "cursos": [],
        "grados": [],
        "secciones": [],
        "profesores": []
    }
    
    # Configuracion
    sedes = session.exec(select(Sedes)).all()
    dias = session.exec(select(Dias).order_by(Dias.orden)).all()
    
    nombres_dias = [d.nombre_dia for d in dias]
    datos["configuracion"] = {
        "sedes": [s.nombre_sede for s in sedes],
        "dias": nombres_dias if nombres_dias else ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
        "turnos": ["Mañana", "Tarde"],
        "slots_por_turno": 6
    }
    
    # Categorias (Áreas)
    areas = session.exec(select(Areas)).all()
    for a in areas:
        datos["categorias"].append({
            "id": f"CAT_{a.id_area}",
            "nombre": a.nombre,
            "max_horas_dia": a.max_horas_dia
        })
        
    # Cursos
    cursos = session.exec(select(Cursos)).all()
    for c in cursos:
        datos["cursos"].append({
            "id": f"CUR_{c.id_curso}",
            "nombre": c.nombre_curso,
            "categoria_id": f"CAT_{c.id_area}"
        })
        
    # Grados y Plan de Estudio
    grados = session.exec(select(Grado)).all()
    for g in grados:
        planes = session.exec(select(PlanEstudio).where(PlanEstudio.id_grado == g.id_grado)).all()
        datos["grados"].append({
            "id": f"GRA_{g.id_grado}",
            "nombre": str(g.numero),
            "cursos_requeridos": [
                {
                    "curso_id": f"CUR_{p.id_curso}",
                    "horas_semanales": p.horas_semanales
                } for p in planes
            ]
        })
        
    # Secciones
    secciones = session.exec(select(Seccion)).all()
    for s in secciones:
        datos["secciones"].append({
            "id": f"SEC_{s.id_seccion}",
            "nombre": f"{s.grado.numero if s.grado else ''}° {s.nombre}".strip(),
            "grado": f"GRA_{s.id_grado}",
            "sede": s.sede.nombre_sede if s.sede else "Sede A",
            "disponibilidad": {d: ["Mañana", "Tarde"] for d in datos["configuracion"]["dias"]}
        })
        
    # Profesores
    profesores = session.exec(select(Profesores)).all()
    for p in profesores:
        pcs = session.exec(select(ProfesorCurso).where(ProfesorCurso.id_profesor == p.id_profesores)).all()
        datos["profesores"].append({
            "id": f"PROF_{p.id_profesores}",
            "nombre": p.nombre_profesor,
            "cursos_habilitados": [f"CUR_{pc.id_curso}" for pc in pcs],
            "max_horas_dia": p.max_horas_dia,
            "disponibilidad": {d: ["Mañana", "Tarde"] for d in datos["configuracion"]["dias"]}
        })
        
    return datos

def generar_horario_engine(session: Session) -> dict:
    """Proceso completo: Extrae DB -> Valida -> Preprocesa -> Construye Modelo -> Resuelve."""
    try:
        # 1. Construir Diccionario desde la BD
        datos = build_json_from_db(session)
        
        # 2. Validar
        errores = validar_todo(datos)
        if errores:
            return {"status": "error", "errores": errores}
            
        # 3. Flujo Motor
        datos_procesados = preprocesar(datos)
        modelo, variables_x = construir_modelo(datos_procesados)
        dict_resultado = resolver_modelo(modelo, variables_x)
        
        return {
            "status": "success", 
            "resultado": dict_resultado
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "errores": [str(e)]}
