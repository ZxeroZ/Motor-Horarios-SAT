from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
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

# --- Endpoints Administrativos (Áreas y Cursos) ---
@app.get("/api/areas", response_model=List[Area])
def get_areas(session: Session = Depends(get_session)):
    return session.exec(select(Area)).all()

@app.post("/api/areas", response_model=Area)
def create_area(area: Area, session: Session = Depends(get_session)):
    session.add(area)
    session.commit()
    session.refresh(area)
    return area

@app.get("/api/cursos", response_model=List[Curso])
def get_cursos(session: Session = Depends(get_session)):
    return session.exec(select(Curso)).all()

@app.post("/api/cursos", response_model=Curso)
def create_curso(curso: Curso, session: Session = Depends(get_session)):
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso

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

