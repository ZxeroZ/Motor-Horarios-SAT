from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from backend.database import create_db_and_tables, get_session, engine

from backend.models import (
    Colegio, Turno, Grado, Dias, Areas, Sedes, Usuario, Bloque, 
    Cursos, Profesores, Seccion, GradoDiaConfig, PlanEstudio, 
    ProfesorCurso, SeccionTurno, HorarioFinal, Tutoria,
    SedeProfesor, ProfesorDisponibilidad, ProfesorPreferencia,
    GradoProfesor, BloqueReservado, BloqueGrado, BloqueOpcion, BloqueOpcionSlot
)
from fastapi.middleware.cors import CORSMiddleware

class LoginRequest(BaseModel):
    email: str
    password: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        admin = session.exec(select(Usuario).where(Usuario.email == "admin@colegio.com")).first()
        if not admin:
            session.add(Usuario(email="admin@colegio.com", nombre="Administrador"))
            session.commit()
    yield

app = FastAPI(
    title="Timetable Engine API",
    description="Backend refactorizado para el nuevo esquema de BD",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(Usuario).where(Usuario.email == req.email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {"status": "success", "user": {"nombre": user.nombre, "email": user.email}}

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Sistema Integral de Horarios V2"}

# --- Endpoints de Infraestructura Base ---
@app.get("/api/colegio", response_model=List[Colegio])
def get_colegio(session: Session = Depends(get_session)):
    return session.exec(select(Colegio)).all()

@app.put("/api/colegio/{id}", response_model=Colegio)
def update_colegio(id: int, col: Colegio, session: Session = Depends(get_session)):
    db_c = session.get(Colegio, id)
    if not db_c: raise HTTPException(status_code=404)
    db_c.nombre_colegio = col.nombre_colegio
    session.commit()
    return db_c

@app.get("/api/sedes", response_model=List[Sedes])
def get_sedes(session: Session = Depends(get_session)):
    return session.exec(select(Sedes)).all()
@app.post("/api/sedes", response_model=Sedes)
def create_sede(sede: Sedes, session: Session = Depends(get_session)):
    session.add(sede)
    session.commit()
    return sede

@app.put("/api/sedes/{id_sede}", response_model=Sedes)
def update_sede(id_sede: int, sede_in: Sedes, session: Session = Depends(get_session)):
    db_sede = session.get(Sedes, id_sede)
    if not db_sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    db_sede.nombre_sede = sede_in.nombre_sede
    session.add(db_sede)
    session.commit()
    session.refresh(db_sede)
    return db_sede

@app.delete("/api/sedes/{id_sede}")
def delete_sede(id_sede: int, session: Session = Depends(get_session)):
    db_sede = session.get(Sedes, id_sede)
    if not db_sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    # Chequear uso (Seccion y SedeProfesor)
    in_use_seccion = session.exec(select(Seccion).where(Seccion.id_sede == id_sede)).first()
    if in_use_seccion:
        raise HTTPException(status_code=400, detail="Sede en uso")
    in_use_prof = session.exec(select(SedeProfesor).where(SedeProfesor.id_sede == id_sede)).first()
    if in_use_prof:
        raise HTTPException(status_code=400, detail="Sede en uso")
    
    session.delete(db_sede)
    session.commit()
    return {"message": "Sede borrada"}

@app.get("/api/grados", response_model=List[Grado])
def get_grados(session: Session = Depends(get_session)):
    return session.exec(select(Grado)).all()

@app.post("/api/grados", response_model=Grado)
def create_grado(grado: Grado, session: Session = Depends(get_session)):
    session.add(grado)
    session.commit()
    return grado

@app.delete("/api/grados/{id_grado}")
def delete_grado(id_grado: int, session: Session = Depends(get_session)):
    db_grado = session.get(Grado, id_grado)
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    session.delete(db_grado)
    session.commit()
    return {"message": "Grado borrado"}

# --- Endpoints: Grado-Día Config ---
@app.get("/api/grado-dia-config", response_model=List[GradoDiaConfig])
def get_grado_dia_config(session: Session = Depends(get_session)):
    return session.exec(select(GradoDiaConfig)).all()

@app.post("/api/grado-dia-config", response_model=GradoDiaConfig)
def create_grado_dia_config(config: GradoDiaConfig, session: Session = Depends(get_session)):
    if config.bloques_dia is not None and config.bloques_dia <= 0:
        raise HTTPException(status_code=400, detail="otra vez no leiste los cambios no envies 0 >:/")
        
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

@app.put("/api/grado-dia-config/{id_config}", response_model=GradoDiaConfig)
def update_grado_dia_config(id_config: int, config_update: GradoDiaConfig, session: Session = Depends(get_session)):
    db_config = session.get(GradoDiaConfig, id_config)
    if not db_config: raise HTTPException(status_code=404, detail="Config no encontrada")
    
    if config_update.bloques_dia is not None and config_update.bloques_dia <= 0:
        raise HTTPException(status_code=400, detail="otra vez no leiste los cambios no envies 0 >:/")
        
    db_config.bloques_dia = config_update.bloques_dia
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

@app.delete("/api/grado-dia-config/{id_config}")
def delete_grado_dia_config(id_config: int, session: Session = Depends(get_session)):
    db = session.get(GradoDiaConfig, id_config)
    if not db: raise HTTPException(status_code=404, detail="Config no encontrada")
    session.delete(db)
    session.commit()
    return {"message": "Config borrada"}

@app.get("/api/dias", response_model=List[Dias])
def get_dias(session: Session = Depends(get_session)):
    return session.exec(select(Dias).order_by(Dias.orden)).all()
@app.post("/api/dias", response_model=Dias)
def create_dia(dia: Dias, session: Session = Depends(get_session)):
    session.add(dia)
    session.commit()
    return dia


@app.delete("/api/dias/{id_dia}")
def delete_dia(id_dia: int, session: Session = Depends(get_session)):
    db = session.get(Dias, id_dia)
    if not db:
        raise HTTPException(status_code=404, detail="Dia no encontrado")
    session.delete(db)
    session.commit()
    return {"message": "Día borrado"}

@app.get("/api/turnos", response_model=List[Turno])
def get_turnos(session: Session = Depends(get_session)):
    return session.exec(select(Turno)).all()
@app.post("/api/turnos", response_model=Turno)
def create_turno(turno: Turno, session: Session = Depends(get_session)):
    session.add(turno)
    session.commit()
    return turno

@app.put("/api/turnos/{id_turno}", response_model=Turno)
def update_turno(id_turno: int, turno_in: Turno, session: Session = Depends(get_session)):
    db_turno = session.get(Turno, id_turno)
    if not db_turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    db_turno.nombre = turno_in.nombre
    session.add(db_turno)
    session.commit()
    session.refresh(db_turno)
    return db_turno

@app.delete("/api/turnos/{id_turno}")
def delete_turno(id_turno: int, session: Session = Depends(get_session)):
    db_turno = session.get(Turno, id_turno)
    if not db_turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    # Chequear uso en SeccionTurno
    in_use_turno = session.exec(select(SeccionTurno).where(SeccionTurno.id_turno == id_turno)).first()
    if in_use_turno:
        raise HTTPException(status_code=400, detail="Turno en uso")
    
    session.delete(db_turno)
    session.commit()
    return {"message": "Turno borrado"}

@app.get("/api/bloques", response_model=List[Bloque])
def get_bloques(session: Session = Depends(get_session)):
    return session.exec(select(Bloque)).all()
@app.post("/api/bloques", response_model=Bloque)
def create_bloque(bloque: Bloque, session: Session = Depends(get_session)):
    session.add(bloque)
    session.commit()
    return bloque

# --- Endpoints Administrativos: Áreas ---
@app.get("/api/areas", response_model=List[Areas])
def get_areas(session: Session = Depends(get_session)):
    return session.exec(select(Areas)).all()

@app.post("/api/areas", response_model=Areas)
def create_area(area: Areas, session: Session = Depends(get_session)):
    session.add(area)
    session.commit()
    session.refresh(area)
    return area

@app.put("/api/areas/{id_area}", response_model=Areas)
def update_area(id_area: int, area_update: Areas, session: Session = Depends(get_session)):
    db_area = session.get(Areas, id_area)
    if not db_area: raise HTTPException(status_code=404, detail="Area no encontrada")
    db_area.nombre = area_update.nombre
    db_area.max_horas_dia = area_update.max_horas_dia
    session.add(db_area)
    session.commit()
    session.refresh(db_area)
    return db_area

@app.delete("/api/areas/{id_area}")
def delete_area(id_area: int, session: Session = Depends(get_session)):
    db_area = session.get(Areas, id_area)
    if not db_area: raise HTTPException(status_code=404, detail="Area no encontrada")
    session.delete(db_area)
    session.commit()
    return {"message": "Area borrada"}

# --- Endpoints Administrativos: Cursos ---
@app.get("/api/cursos", response_model=List[Cursos])
def get_cursos(session: Session = Depends(get_session)):
    return session.exec(select(Cursos)).all()

@app.post("/api/cursos", response_model=Cursos)
def create_curso(curso: Cursos, session: Session = Depends(get_session)):
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso

@app.put("/api/cursos/{id_curso}", response_model=Cursos)
def update_curso(id_curso: int, curso_update: Cursos, session: Session = Depends(get_session)):
    db_curso = session.get(Cursos, id_curso)
    if not db_curso: raise HTTPException(status_code=404, detail="Curso no encontrado")
    db_curso.nombre_curso = curso_update.nombre_curso
    db_curso.id_area = curso_update.id_area
    session.add(db_curso)
    session.commit()
    session.refresh(db_curso)
    return db_curso

@app.delete("/api/cursos/{id_curso}")
def delete_curso(id_curso: int, session: Session = Depends(get_session)):
    db_curso = session.get(Cursos, id_curso)
    if not db_curso: raise HTTPException(status_code=404, detail="Curso no encontrado")
    session.delete(db_curso)
    session.commit()
    return {"message": "Curso borrado"}

# --- Endpoints Administrativos: Profesores ---
@app.get("/api/profesores", response_model=List[Profesores])
def get_profesores(session: Session = Depends(get_session)):
    return session.exec(select(Profesores)).all()

@app.post("/api/profesores", response_model=Profesores)
def create_profesor(profesor: Profesores, session: Session = Depends(get_session)):
    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return profesor

@app.put("/api/profesores/{id_profesor}", response_model=Profesores)
def update_profesor(id_profesor: int, profesor_update: Profesores, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesores, id_profesor)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    db_profesor.nombre_profesor = profesor_update.nombre_profesor
    session.add(db_profesor)
    session.commit()
    session.refresh(db_profesor)
    return db_profesor

@app.delete("/api/profesores/{id_profesor}")
def delete_profesor(id_profesor: int, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesores, id_profesor)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    session.delete(db_profesor)
    session.commit()
    return {"message": "Profesor borrado"}

# --- Endpoints Administrativos: Asignación Profesor-Curso ---
@app.get("/api/profesor-curso", response_model=List[ProfesorCurso])
def get_profesor_curso(session: Session = Depends(get_session)):
    return session.exec(select(ProfesorCurso)).all()

@app.post("/api/profesor-curso", response_model=ProfesorCurso)
def create_profesor_curso(pc: ProfesorCurso, session: Session = Depends(get_session)):
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc

@app.delete("/api/profesor-curso/{id_profesor_curso}")
def delete_profesor_curso(id_profesor_curso: int, session: Session = Depends(get_session)):
    db = session.get(ProfesorCurso, id_profesor_curso)
    if not db: raise HTTPException(status_code=404, detail="ProfesorCurso no encontrado")
    session.delete(db)
    session.commit()
    return {"message": "ProfesorCurso borrado"}

# --- Endpoints Administrativos: Secciones ---
@app.get("/api/secciones", response_model=List[Seccion])
def get_secciones(session: Session = Depends(get_session)):
    return session.exec(select(Seccion)).all()

@app.post("/api/secciones", response_model=Seccion)
def create_seccion(seccion: Seccion, session: Session = Depends(get_session)):
    session.add(seccion)
    session.commit()
    session.refresh(seccion)
    return seccion

@app.put("/api/secciones/{id_seccion}", response_model=Seccion)
def update_seccion(id_seccion: int, seccion_update: Seccion, session: Session = Depends(get_session)):
    db_seccion = session.get(Seccion, id_seccion)
    if not db_seccion: raise HTTPException(status_code=404, detail="Seccion no encontrada")
    db_seccion.nombre = seccion_update.nombre
    db_seccion.id_grado = seccion_update.id_grado
    db_seccion.id_sede = seccion_update.id_sede
    session.add(db_seccion)
    session.commit()
    session.refresh(db_seccion)
    return db_seccion

@app.delete("/api/secciones/{id_seccion}")
def delete_seccion(id_seccion: int, session: Session = Depends(get_session)):
    db_seccion = session.get(Seccion, id_seccion)
    if not db_seccion: raise HTTPException(status_code=404, detail="Seccion no encontrada")
    session.delete(db_seccion)
    session.commit()
    return {"message": "Seccion borrada"}

# --- Endpoints Administrativos: Plan de Estudio ---
@app.get("/api/planes", response_model=List[PlanEstudio])
def get_planes(session: Session = Depends(get_session)):
    return session.exec(select(PlanEstudio)).all()

@app.post("/api/planes", response_model=PlanEstudio)
def create_plan(plan: PlanEstudio, session: Session = Depends(get_session)):
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan

@app.put("/api/planes/{id_plan}", response_model=PlanEstudio)
def update_plan(id_plan: int, plan_update: PlanEstudio, session: Session = Depends(get_session)):
    db_plan = session.get(PlanEstudio, id_plan)
    if not db_plan: raise HTTPException(status_code=404, detail="Plan de Estudio no encontrado")
    db_plan.id_grado = plan_update.id_grado
    db_plan.id_curso = plan_update.id_curso
    db_plan.horas_semanales = plan_update.horas_semanales
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return db_plan

@app.delete("/api/planes/{id_plan}")
def delete_plan(id_plan: int, session: Session = Depends(get_session)):
    db_plan = session.get(PlanEstudio, id_plan)
    if not db_plan: raise HTTPException(status_code=404, detail="Plan de Estudio no encontrado")
    session.delete(db_plan)
    session.commit()
    return {"message": "Plan de Estudio borrado"}

# --- Endpoints: Sección-Turno ---
@app.get("/api/seccion-turno", response_model=List[SeccionTurno])
def get_seccion_turno(session: Session = Depends(get_session)):
    return session.exec(select(SeccionTurno)).all()

@app.post("/api/seccion-turno", response_model=SeccionTurno)
def create_seccion_turno(st: SeccionTurno, session: Session = Depends(get_session)):
    session.add(st)
    session.commit()
    session.refresh(st)
    return st

@app.delete("/api/seccion-turno/{id_seccion_turno}")
def delete_seccion_turno(id_seccion_turno: int, session: Session = Depends(get_session)):
    db = session.get(SeccionTurno, id_seccion_turno)
    if not db: raise HTTPException(status_code=404)
    session.delete(db)
    session.commit()
    return {"message": "Borrado"}


# --- Endpoints: Horario Final ---
@app.get("/api/horario-final", response_model=List[HorarioFinal])
def get_horario_final(session: Session = Depends(get_session)):
    return session.exec(select(HorarioFinal)).all()

@app.post("/api/horario-final", response_model=HorarioFinal)
def create_horario_final(hf: HorarioFinal, session: Session = Depends(get_session)):
    session.add(hf)
    session.commit()
    session.refresh(hf)
    return hf

@app.delete("/api/horario-final/{id_horario_final}")
def delete_horario_final(id_horario_final: int, session: Session = Depends(get_session)):
    db = session.get(HorarioFinal, id_horario_final)
    if not db: raise HTTPException(status_code=404)
    session.delete(db)
    session.commit()
    return {"message": "Borrado"}

# --- Tutorías ---
@app.get("/api/tutorias")
def get_tutorias(session: Session = Depends(get_session)):
    return session.exec(select(Tutoria)).all()

@app.post("/api/tutorias")
def create_tutoria(tutoria: Tutoria, session: Session = Depends(get_session)):
    session.add(tutoria)
    session.commit()
    session.refresh(tutoria)
    return tutoria

@app.delete("/api/tutorias/{id_tutoria}")
def delete_tutoria(id_tutoria: int, session: Session = Depends(get_session)):
    db_tutoria = session.get(Tutoria, id_tutoria)
    if not db_tutoria: raise HTTPException(status_code=404, detail="Tutoría no encontrada")
    session.delete(db_tutoria)
    session.commit()
    return {"message": "Tutoría borrada"}


# --- Endpoints: Profesor-Sedes ---
@app.get("/api/profesor-sedes")
def get_profesor_sedes(session: Session = Depends(get_session)):
    return session.exec(select(SedeProfesor)).all()

@app.post("/api/profesor-sedes")
def create_profesor_sede(ps: SedeProfesor, session: Session = Depends(get_session)):
    session.add(ps)
    session.commit()
    session.refresh(ps)
    return ps

@app.delete("/api/profesor-sedes/{id_sede_profesor}")
def delete_profesor_sede(id_sede_profesor: int, session: Session = Depends(get_session)):
    db = session.get(SedeProfesor, id_sede_profesor)
    if not db: raise HTTPException(status_code=404, detail="Vínculo no encontrado")
    session.delete(db)
    session.commit()
    return {"message": "Vínculo profesor-sede borrado"}

# --- Endpoints: Grado-Profesor ---
@app.get("/api/grado-profesor")
def get_grado_profesor(session: Session = Depends(get_session)):
    return session.exec(select(GradoProfesor)).all()

@app.post("/api/grado-profesor")
def create_grado_profesor(gp: GradoProfesor, session: Session = Depends(get_session)):
    session.add(gp)
    session.commit()
    session.refresh(gp)
    return gp

@app.delete("/api/grado-profesor/{id_grado_profesor}")
def delete_grado_profesor(id_grado_profesor: int, session: Session = Depends(get_session)):
    db = session.get(GradoProfesor, id_grado_profesor)
    if not db: raise HTTPException(status_code=404, detail="Vínculo grado-profesor no encontrado")
    session.delete(db)
    session.commit()
    return {"message": "Vínculo grado-profesor borrado"}

# --- Endpoints: Bloques Reservados ---
@app.get("/api/bloque-reservado")
def get_bloques_reservados(session: Session = Depends(get_session)):
    reservas = session.exec(select(BloqueReservado)).all()
    resultado = []
    for r in reservas:
        grados = session.exec(select(BloqueGrado).where(BloqueGrado.id_bloque_reservado == r.id_bloque_reservado)).all()
        opciones = session.exec(select(BloqueOpcion).where(BloqueOpcion.id_bloque_reservado == r.id_bloque_reservado)).all()
        opciones_data = []
        for op in opciones:
            slots = session.exec(select(BloqueOpcionSlot).where(BloqueOpcionSlot.id_bloque_opcion == op.id_bloque_opcion)).all()
            opciones_data.append({
                "id_bloque_opcion": op.id_bloque_opcion,
                "nro_opcion": op.nro_opcion,
                "nombre": op.nombre,
                "slots": [s.nro_bloque for s in slots]
            })
        resultado.append({
            "id_bloque_reservado": r.id_bloque_reservado,
            "nombre": r.nombre,
            "id_sede": r.id_sede,
            "id_dia": r.id_dia,
            "id_turno": r.id_turno,
            "grados": [g.id_grado for g in grados],
            "opciones": opciones_data
        })
    return resultado

@app.post("/api/bloque-reservado-completo")
def create_bloque_reservado_completo(data: dict, session: Session = Depends(get_session)):
    """Crea una reserva completa: sede/dia/turno + grados + opciones con slots."""
    reserva = BloqueReservado(
        nombre=data.get("nombre"),
        id_sede=data["id_sede"],
        id_dia=data["id_dia"],
        id_turno=data["id_turno"]
    )
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    
    for grado_id in data.get("grados", []):
        session.add(BloqueGrado(id_bloque_reservado=reserva.id_bloque_reservado, id_grado=grado_id))
    
    # Soporta el nuevo formato 'opciones' o el formato antiguo 'opciones_slots'
    if "opciones" in data:
        for op_data in data["opciones"]:
            opcion = BloqueOpcion(
                id_bloque_reservado=reserva.id_bloque_reservado, 
                nro_opcion=op_data.get("nro_opcion", 1),
                nombre=op_data.get("nombre")
            )
            session.add(opcion)
            session.commit()
            session.refresh(opcion)
            for nro in op_data.get("slots", []):
                session.add(BloqueOpcionSlot(id_bloque_opcion=opcion.id_bloque_opcion, nro_bloque=nro))
    else:
        for idx, slots in enumerate(data.get("opciones_slots", [])):
            opcion = BloqueOpcion(id_bloque_reservado=reserva.id_bloque_reservado, nro_opcion=idx + 1)
            session.add(opcion)
            session.commit()
            session.refresh(opcion)
            for nro in slots:
                session.add(BloqueOpcionSlot(id_bloque_opcion=opcion.id_bloque_opcion, nro_bloque=nro))
    
    session.commit()
    return {"message": "Bloque reservado creado", "id": reserva.id_bloque_reservado}

@app.delete("/api/bloque-reservado/{id_bloque_reservado}")
def delete_bloque_reservado(id_bloque_reservado: int, session: Session = Depends(get_session)):
    reserva = session.get(BloqueReservado, id_bloque_reservado)
    if not reserva: raise HTTPException(status_code=404, detail="Bloque reservado no encontrado")
    # Borrar hijos en cascada
    for bg in session.exec(select(BloqueGrado).where(BloqueGrado.id_bloque_reservado == id_bloque_reservado)).all():
        session.delete(bg)
    for bo in session.exec(select(BloqueOpcion).where(BloqueOpcion.id_bloque_reservado == id_bloque_reservado)).all():
        for slot in session.exec(select(BloqueOpcionSlot).where(BloqueOpcionSlot.id_bloque_opcion == bo.id_bloque_opcion)).all():
            session.delete(slot)
        session.delete(bo)
    session.delete(reserva)
    session.commit()
    return {"message": "Bloque reservado y dependientes borrados"}

# --- Endpoints: Profesor-Disponibilidad ---
@app.get("/api/profesor-disponibilidad")
def get_profesor_disponibilidad(session: Session = Depends(get_session)):
    return session.exec(select(ProfesorDisponibilidad)).all()

@app.post("/api/profesor-disponibilidad")
def create_profesor_disponibilidad(pd: ProfesorDisponibilidad, session: Session = Depends(get_session)):
    session.add(pd)
    session.commit()
    session.refresh(pd)
    return pd

@app.delete("/api/profesor-disponibilidad/{id_disponibilidad}")
def delete_profesor_disponibilidad(id_disponibilidad: int, session: Session = Depends(get_session)):
    db = session.get(ProfesorDisponibilidad, id_disponibilidad)
    if not db: raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    session.delete(db)
    session.commit()
    return {"message": "Disponibilidad borrada"}

# --- Endpoints: Profesor-Preferencia ---
@app.get("/api/profesor-preferencia")
def get_profesor_preferencia(session: Session = Depends(get_session)):
    return session.exec(select(ProfesorPreferencia)).all()

@app.post("/api/profesor-preferencia")
def create_profesor_preferencia(pp: ProfesorPreferencia, session: Session = Depends(get_session)):
    session.add(pp)
    session.commit()
    session.refresh(pp)
    return pp

@app.delete("/api/profesor-preferencia/{id_preferencia}")
def delete_profesor_preferencia(id_preferencia: int, session: Session = Depends(get_session)):
    db = session.get(ProfesorPreferencia, id_preferencia)
    if not db: raise HTTPException(status_code=404, detail="Preferencia no encontrada")
    session.delete(db)
    session.commit()
    return {"message": "Preferencia borrada"}

# --- Endpoints del Motor ---
from backend.engine_connector import generar_horario_engine

@app.post("/api/generar-horario")
def desencadenar_motor(session: Session = Depends(get_session)):
    resultado = generar_horario_engine(session)
    return resultado

@app.get("/api/cargar-horario")
def cargar_horario_guardado(session: Session = Depends(get_session)):
    """Lee horario_final de la BD y lo devuelve en formato del motor."""
    rows = session.exec(select(HorarioFinal)).all()
    if not rows:
        return {"status": "empty", "resultado": None}
    
    # Lookups inversos
    dias_db = {d.id_dia: d.nombre_dia for d in session.exec(select(Dias)).all()}
    turnos_db = {t.id_turno: t.nombre for t in session.exec(select(Turno)).all()}
    
    # Agrupar slots en bloques contiguos: (seccion, curso, profesor, dia, turno) -> slots
    from collections import defaultdict
    grupos = defaultdict(list)
    for r in rows:
        turno_nombre = turnos_db.get(r.id_turno, "Mañana")
        key = (r.id_seccion, r.id_curso, r.id_profesor, r.id_dia, turno_nombre)
        grupos[key].append(r.num_bloque)
    
    asignaciones = []
    for (sec, cur, prof, dia_id, turno), slots in grupos.items():
        slots.sort()
        asignaciones.append({
            "seccion_id": f"SEC_{sec}",
            "curso_id": f"CUR_{cur}",
            "profesor_id": f"PROF_{prof}",
            "dia": dias_db.get(dia_id, ""),
            "turno": turno,
            "slot_inicio": slots[0] - 1,
            "horas": len(slots)
        })
    
    return {
        "status": "success",
        "resultado": {
            "estado": "GUARDADO",
            "mensaje": "Horario cargado desde la base de datos.",
            "estadisticas": {"tiempo_segundos": 0, "ramas_exploradas": 0, "conflictos": 0},
            "asignaciones": asignaciones
        }
    }
