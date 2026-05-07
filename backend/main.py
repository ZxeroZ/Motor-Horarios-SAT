from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from .database import create_db_and_tables, get_session, engine

from .models import (
    Colegio, Turno, Grado, Dias, Areas, Sedes, Usuario, Bloque, 
    Cursos, Profesores, Seccion, GradoDiaConfig, PlanEstudio, 
    ProfesorCurso, SeccionTurno, Restricciones, CargaAcademica, HorarioFinal
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
            session.add(Usuario(email="admin@colegio.com", nombre="Administrador", password="123456"))
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
    if not user or user.password != req.password:
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

@app.get("/api/grados", response_model=List[Grado])
def get_grados(session: Session = Depends(get_session)):
    return session.exec(select(Grado)).all()
@app.post("/api/grados", response_model=Grado)
def create_grado(grado: Grado, session: Session = Depends(get_session)):
    session.add(grado)
    session.commit()
    return grado

# --- Endpoints: Grado-Día Config ---
@app.get("/api/grado-dia-config", response_model=List[GradoDiaConfig])
def get_grado_dia_config(session: Session = Depends(get_session)):
    return session.exec(select(GradoDiaConfig)).all()

@app.post("/api/grado-dia-config", response_model=GradoDiaConfig)
def create_grado_dia_config(config: GradoDiaConfig, session: Session = Depends(get_session)):
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

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

@app.get("/api/turnos", response_model=List[Turno])
def get_turnos(session: Session = Depends(get_session)):
    return session.exec(select(Turno)).all()
@app.post("/api/turnos", response_model=Turno)
def create_turno(turno: Turno, session: Session = Depends(get_session)):
    session.add(turno)
    session.commit()
    return turno

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

@app.put("/api/profesores/{id_profesores}", response_model=Profesores)
def update_profesor(id_profesores: int, profesor_update: Profesores, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesores, id_profesores)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    db_profesor.nombre_profesor = profesor_update.nombre_profesor
    db_profesor.id_sede = profesor_update.id_sede
    db_profesor.max_horas_dia = profesor_update.max_horas_dia
    session.add(db_profesor)
    session.commit()
    session.refresh(db_profesor)
    return db_profesor

@app.delete("/api/profesores/{id_profesores}")
def delete_profesor(id_profesores: int, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesores, id_profesores)
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

# --- Endpoints: Restricciones ---
@app.get("/api/restricciones", response_model=List[Restricciones])
def get_restricciones(session: Session = Depends(get_session)):
    return session.exec(select(Restricciones)).all()

@app.post("/api/restricciones", response_model=Restricciones)
def create_restriccion(r: Restricciones, session: Session = Depends(get_session)):
    session.add(r)
    session.commit()
    session.refresh(r)
    return r

@app.delete("/api/restricciones/{id_restricciones}")
def delete_restriccion(id_restricciones: int, session: Session = Depends(get_session)):
    db = session.get(Restricciones, id_restricciones)
    if not db: raise HTTPException(status_code=404)
    session.delete(db)
    session.commit()
    return {"message": "Borrado"}

# --- Endpoints: Carga Académica ---
@app.get("/api/carga-academica", response_model=List[CargaAcademica])
def get_carga_academica(session: Session = Depends(get_session)):
    return session.exec(select(CargaAcademica)).all()

@app.post("/api/carga-academica", response_model=CargaAcademica)
def create_carga_academica(ca: CargaAcademica, session: Session = Depends(get_session)):
    session.add(ca)
    session.commit()
    session.refresh(ca)
    return ca

@app.delete("/api/carga-academica/{id_carga}")
def delete_carga_academica(id_carga: int, session: Session = Depends(get_session)):
    db = session.get(CargaAcademica, id_carga)
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

# --- Endpoints del Motor ---
from backend.engine_connector import generar_horario_engine

@app.post("/api/generar-horario")
def desencadenar_motor(session: Session = Depends(get_session)):
    resultado = generar_horario_engine(session)
    return resultado
