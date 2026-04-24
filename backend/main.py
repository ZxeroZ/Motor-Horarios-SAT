from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

# Importar motor de bd y generador de tablas
from .database import create_db_and_tables, get_session

# Importar todos los modelos para asegurarnos que SQLModel los registre antes de crear la BD
from .models import (
    Colegio, Sede, Usuario, Area, Curso, Grado, Seccion, 
    PlanEstudio, Configuracion, Dia, DiaGrado, Bloque, 
    Profesor, ProfesorCurso, Restriccion, CargaAcademica, HorarioFinal
)

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="Timetable Engine API",
    description="Backend para el Sistema Integral de Horarios",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir frontend Vite local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Sistema Integral de Horarios"}

# --- Endpoints Administrativos: Áreas ---
@app.get("/api/areas", response_model=List[Area])
def get_areas(session: Session = Depends(get_session)):
    return session.exec(select(Area)).all()

@app.post("/api/areas", response_model=Area)
def create_area(area: Area, session: Session = Depends(get_session)):
    session.add(area)
    session.commit()
    session.refresh(area)
    return area

@app.put("/api/areas/{id_area}", response_model=Area)
def update_area(id_area: int, area_update: Area, session: Session = Depends(get_session)):
    db_area = session.get(Area, id_area)
    if not db_area: raise HTTPException(status_code=404, detail="Area no encontrada")
    db_area.nombre_area = area_update.nombre_area
    db_area.max_horas_dia = area_update.max_horas_dia
    session.add(db_area)
    session.commit()
    session.refresh(db_area)
    return db_area

@app.delete("/api/areas/{id_area}")
def delete_area(id_area: int, session: Session = Depends(get_session)):
    db_area = session.get(Area, id_area)
    if not db_area: raise HTTPException(status_code=404, detail="Area no encontrada")
    session.delete(db_area)
    session.commit()
    return {"message": "Area borrada"}

# --- Endpoints Administrativos: Cursos ---
@app.get("/api/cursos", response_model=List[Curso])
def get_cursos(session: Session = Depends(get_session)):
    return session.exec(select(Curso)).all()

@app.post("/api/cursos", response_model=Curso)
def create_curso(curso: Curso, session: Session = Depends(get_session)):
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso

@app.put("/api/cursos/{id_curso}", response_model=Curso)
def update_curso(id_curso: int, curso_update: Curso, session: Session = Depends(get_session)):
    db_curso = session.get(Curso, id_curso)
    if not db_curso: raise HTTPException(status_code=404, detail="Curso no encontrado")
    db_curso.nombre_curso = curso_update.nombre_curso
    db_curso.id_area = curso_update.id_area
    session.add(db_curso)
    session.commit()
    session.refresh(db_curso)
    return db_curso

@app.delete("/api/cursos/{id_curso}")
def delete_curso(id_curso: int, session: Session = Depends(get_session)):
    db_curso = session.get(Curso, id_curso)
    if not db_curso: raise HTTPException(status_code=404, detail="Curso no encontrado")
    session.delete(db_curso)
    session.commit()
    return {"message": "Curso borrado"}

# --- Endpoints Administrativos: Profesores ---
@app.get("/api/profesores", response_model=List[Profesor])
def get_profesores(session: Session = Depends(get_session)):
    return session.exec(select(Profesor)).all()

@app.post("/api/profesores", response_model=Profesor)
def create_profesor(profesor: Profesor, session: Session = Depends(get_session)):
    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return profesor

@app.put("/api/profesores/{id_profesor}", response_model=Profesor)
def update_profesor(id_profesor: int, profesor_update: Profesor, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesor, id_profesor)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    db_profesor.nombre_profesor = profesor_update.nombre_profesor
    db_profesor.max_horas_dia = profesor_update.max_horas_dia
    db_profesor.id_sede = profesor_update.id_sede
    session.add(db_profesor)
    session.commit()
    session.refresh(db_profesor)
    return db_profesor

@app.delete("/api/profesores/{id_profesor}")
def delete_profesor(id_profesor: int, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesor, id_profesor)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    session.delete(db_profesor)
    session.commit()
    return {"message": "Profesor borrado"}

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
    db_seccion.letra = seccion_update.letra
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

@app.put("/api/planes/{id_estudio}", response_model=PlanEstudio)
def update_plan(id_estudio: int, plan_update: PlanEstudio, session: Session = Depends(get_session)):
    db_plan = session.get(PlanEstudio, id_estudio)
    if not db_plan: raise HTTPException(status_code=404, detail="Plan de Estudio no encontrado")
    db_plan.id_grado = plan_update.id_grado
    db_plan.id_curso = plan_update.id_curso
    db_plan.horas_semanales = plan_update.horas_semanales
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return db_plan

@app.delete("/api/planes/{id_estudio}")
def delete_plan(id_estudio: int, session: Session = Depends(get_session)):
    db_plan = session.get(PlanEstudio, id_estudio)
    if not db_plan: raise HTTPException(status_code=404, detail="Plan de Estudio no encontrado")
    session.delete(db_plan)
    session.commit()
    return {"message": "Plan de Estudio borrado"}

# --- Endpoints de Ejemplo (Colegio) ---
@app.get("/api/colegios", response_model=List[Colegio])
def get_colegios(session: Session = Depends(get_session)):
    colegios = session.exec(select(Colegio)).all()
    return colegios

@app.post("/api/colegios", response_model=Colegio)
def create_colegio(colegio: Colegio, session: Session = Depends(get_session)):
    session.add(colegio)
    session.commit()
    session.refresh(colegio)
    return colegio

# --- Endpoints del Motor ---
from backend.engine_connector import generar_horario_engine

@app.post("/api/generar-horario")
def desencadenar_motor(session: Session = Depends(get_session)):
    resultado = generar_horario_engine(session)
    # Por ahora simplemente retornamos el json masivo hacia el front
    # En fase 2.5 este json se podria mapear devuelta a la tabla HorarioFinal
    return resultado

