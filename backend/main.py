import json
import logging
from contextlib import asynccontextmanager


from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, delete
from typing import List
from pydantic import BaseModel

from backend.config import settings
from backend.logging_config import setup_logging
from datetime import time, timedelta
from backend.exceptions import AppError
from backend.database import create_db_and_tables, get_session, engine

from backend.models import (
    Colegio, Turno, Grado, Dias, Areas, Sedes, Usuario, Bloque, 
    Cursos, Profesores, Seccion, GradoDiaConfig, PlanEstudio, 
    ProfesorCurso, SeccionTurno, HorarioFinal, Tutoria,
    SedeProfesor, ProfesorDisponibilidad, ProfesorPreferencia,
    GradoProfesor, BloqueReservado, BloqueGrado, BloqueOpcion, BloqueOpcionSlot,
    HorarioSnapshot, SnapshotUpdate
)


logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Iniciando %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    create_db_and_tables()
    with Session(engine) as session:
        admin = session.exec(select(Usuario).where(Usuario.email == "admin@colegio.com")).first()
        if not admin:
            session.add(Usuario(email="admin@colegio.com", nombre="Administrador", password="Administrador"))
            session.commit()
            logger.info("Usuario admin creado")
    yield
    logger.info("Aplicación finalizada")

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend refactorizado para el nuevo esquema de BD",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning("Error controlado [%s]: %s", exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.message, "errors": exc.errors}
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Error interno del servidor"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _reject_if_dependents(session: Session, parent_name: str, checks: list):
    """Si alguna dependencia existe, rechaza con 400 indicando qué borrar primero."""
    conflicts = []
    for query, label in checks:
        if query is not None and session.exec(query).first():
            conflicts.append(label)
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar {parent_name}. Primero elimina: {', '.join(conflicts)}"
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

@app.post("/api/colegio", response_model=Colegio)
def create_colegio(col: Colegio, session: Session = Depends(get_session)):
    session.add(col)
    session.commit()
    session.refresh(col)
    return col

@app.put("/api/colegio/{id}", response_model=Colegio)
def update_colegio(id: int, col: Colegio, session: Session = Depends(get_session)):
    db_c = session.get(Colegio, id)
    if not db_c: raise HTTPException(status_code=404)
    db_c.nombre_colegio = col.nombre_colegio
    session.commit()
    return db_c

@app.delete("/api/colegio/{id}")
def delete_colegio(id: int, session: Session = Depends(get_session)):
    db_c = session.get(Colegio, id)
    if not db_c: raise HTTPException(status_code=404, detail="Colegio no encontrado")
    _reject_if_dependents(session, "el Colegio", [
        (select(Sedes).where(Sedes.id_colegio == id), "Sedes"),
        (select(Usuario).where(Usuario.id_colegio == id), "Usuarios"),
    ])
    session.delete(db_c)
    session.commit()
    return {"message": "Colegio borrado"}

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
    _reject_if_dependents(session, "la Sede", [
        (select(Seccion).where(Seccion.id_sede == id_sede), "Secciones"),
        (select(ProfesorDisponibilidad).where(ProfesorDisponibilidad.id_sede == id_sede), "Disponibilidades"),
        (select(ProfesorPreferencia).where(ProfesorPreferencia.id_sede == id_sede), "Preferencias"),
        (select(SedeProfesor).where(SedeProfesor.id_sede == id_sede), "Vínculos Profesor-Sede"),
        (select(BloqueReservado).where(BloqueReservado.id_sede == id_sede), "Bloques Reservados"),
    ])
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

@app.put("/api/grados/{id_grado}", response_model=Grado)
def update_grado(id_grado: int, grado_update: Grado, session: Session = Depends(get_session)):
    db_grado = session.get(Grado, id_grado)
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    db_grado.numero = grado_update.numero
    session.add(db_grado)
    session.commit()
    session.refresh(db_grado)
    return db_grado

@app.delete("/api/grados/{id_grado}")
def delete_grado(id_grado: int, session: Session = Depends(get_session)):
    db_grado = session.get(Grado, id_grado)
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    _reject_if_dependents(session, "el Grado", [
        (select(Seccion).where(Seccion.id_grado == id_grado), "Secciones"),
        (select(GradoDiaConfig).where(GradoDiaConfig.id_grado == id_grado), "Configs Día-Grado"),
        (select(PlanEstudio).where(PlanEstudio.id_grado == id_grado), "Planes de Estudio"),
        (select(GradoProfesor).where(GradoProfesor.id_grado == id_grado), "Vínculos Grado-Profesor"),
        (select(BloqueGrado).where(BloqueGrado.id_grado == id_grado), "Bloques de Grado"),
    ])
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

@app.put("/api/dias/{id_dia}", response_model=Dias)
def update_dia(id_dia: int, dia_update: Dias, session: Session = Depends(get_session)):
    db_dia = session.get(Dias, id_dia)
    if not db_dia:
        raise HTTPException(status_code=404, detail="Día no encontrado")
    db_dia.nombre_dia = dia_update.nombre_dia
    db_dia.orden = dia_update.orden
    session.add(db_dia)
    session.commit()
    session.refresh(db_dia)
    return db_dia

@app.delete("/api/dias/{id_dia}")
def delete_dia(id_dia: int, session: Session = Depends(get_session)):
    db = session.get(Dias, id_dia)
    if not db:
        raise HTTPException(status_code=404, detail="Dia no encontrado")
    _reject_if_dependents(session, "el Día", [
        (select(GradoDiaConfig).where(GradoDiaConfig.id_dia == id_dia), "Configs Día-Grado"),
        (select(SeccionTurno).where(SeccionTurno.id_dia == id_dia), "Sección-Turnos"),
        (select(HorarioFinal).where(HorarioFinal.id_dia == id_dia), "Horarios Finales"),
        (select(ProfesorDisponibilidad).where(ProfesorDisponibilidad.id_dia == id_dia), "Disponibilidades"),
        (select(ProfesorPreferencia).where(ProfesorPreferencia.id_dia == id_dia), "Preferencias"),
        (select(BloqueReservado).where(BloqueReservado.id_dia == id_dia), "Bloques Reservados"),
    ])
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
    _reject_if_dependents(session, "el Turno", [
        (select(Bloque).where(Bloque.id_turno == id_turno), "Bloques"),
        (select(SeccionTurno).where(SeccionTurno.id_turno == id_turno), "Sección-Turnos"),
        (select(HorarioFinal).where(HorarioFinal.id_turno == id_turno), "Horarios Finales"),
        (select(ProfesorDisponibilidad).where(ProfesorDisponibilidad.id_turno == id_turno), "Disponibilidades"),
        (select(ProfesorPreferencia).where(ProfesorPreferencia.id_turno == id_turno), "Preferencias"),
        (select(BloqueReservado).where(BloqueReservado.id_turno == id_turno), "Bloques Reservados"),
    ])
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

@app.put("/api/bloques/{id_bloque}", response_model=Bloque)
def update_bloque(id_bloque: int, bloque_update: Bloque, session: Session = Depends(get_session)):
    db_bloque = session.get(Bloque, id_bloque)
    if not db_bloque:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    db_bloque.numero_bloque = bloque_update.numero_bloque
    db_bloque.hora_inicio = bloque_update.hora_inicio
    db_bloque.hora_final = bloque_update.hora_final
    db_bloque.id_turno = bloque_update.id_turno
    session.add(db_bloque)
    session.commit()
    session.refresh(db_bloque)
    return db_bloque

@app.delete("/api/bloques/{id_bloque}")
def delete_bloque(id_bloque: int, session: Session = Depends(get_session)):
    db_bloque = session.get(Bloque, id_bloque)
    if not db_bloque:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    session.delete(db_bloque)
    session.commit()
    return {"message": "Bloque borrado"}

class RecreoConfig(BaseModel):
    despuesDeBloque: int
    duracion: int

class ConfigurarTiemposRequest(BaseModel):
    horaInicio: str
    duracionBloque: int
    recreos: List[RecreoConfig] = []

def _parse_time_td(t_str: str) -> timedelta:
    h, m = map(int, t_str.split(':'))
    return timedelta(hours=h, minutes=m)

def _format_time_td(td: timedelta) -> time:
    total_seconds = int(td.total_seconds())
    hours = (total_seconds // 3600) % 24
    minutes = (total_seconds % 3600) // 60
    return time(hour=hours, minute=minutes)

@app.post("/api/configurar-tiempos/{id_turno}")
def configurar_tiempos(id_turno: int, req: ConfigurarTiemposRequest, session: Session = Depends(get_session)):
    bloques_existentes = session.exec(select(Bloque).where(Bloque.id_turno == id_turno)).all()
    for b in bloques_existentes:
        session.delete(b)
    
    MAX_BLOQUES = 12
    current_time = _parse_time_td(req.horaInicio)
    duracion_td = timedelta(minutes=req.duracionBloque)
    
    for i in range(1, MAX_BLOQUES + 1):
        hora_inicio = current_time
        current_time += duracion_td
        hora_final = current_time
        
        b = Bloque(
            id_turno=id_turno,
            numero_bloque=i,
            hora_inicio=_format_time_td(hora_inicio),
            hora_final=_format_time_td(hora_final),
            es_recreo=False,
            duracion_minutos=req.duracionBloque
        )
        session.add(b)
        
        recreo = next((r for r in req.recreos if r.despuesDeBloque == i), None)
        if recreo:
            recreo_td = timedelta(minutes=recreo.duracion)
            r_inicio = current_time
            current_time += recreo_td
            r_final = current_time
            
            r_b = Bloque(
                id_turno=id_turno,
                numero_bloque=None,
                hora_inicio=_format_time_td(r_inicio),
                hora_final=_format_time_td(r_final),
                es_recreo=True,
                despues_de_bloque=i,
                duracion_minutos=recreo.duracion
            )
            session.add(r_b)
            
    session.commit()
    return {"message": "Tiempos configurados correctamente"}


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
    _reject_if_dependents(session, "el Área", [
        (select(Cursos).where(Cursos.id_area == id_area), "Cursos"),
    ])
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
    db_curso.requiere_espacio_unico = curso_update.requiere_espacio_unico
    session.add(db_curso)
    session.commit()
    session.refresh(db_curso)
    return db_curso

@app.delete("/api/cursos/{id_curso}")
def delete_curso(id_curso: int, session: Session = Depends(get_session)):
    db_curso = session.get(Cursos, id_curso)
    if not db_curso: raise HTTPException(status_code=404, detail="Curso no encontrado")
    _reject_if_dependents(session, "el Curso", [
        (select(PlanEstudio).where(PlanEstudio.id_curso == id_curso), "Planes de Estudio"),
        (select(ProfesorCurso).where(ProfesorCurso.id_curso == id_curso), "Vínculos Profesor-Curso"),
        (select(HorarioFinal).where(HorarioFinal.id_curso == id_curso), "Horarios Finales"),
    ])
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
    if hasattr(profesor_update, 'horas_minimas'):
        db_profesor.horas_minimas = profesor_update.horas_minimas
    session.add(db_profesor)
    session.commit()
    session.refresh(db_profesor)
    return db_profesor

@app.delete("/api/profesores/{id_profesor}")
def delete_profesor(id_profesor: int, session: Session = Depends(get_session)):
    db_profesor = session.get(Profesores, id_profesor)
    if not db_profesor: raise HTTPException(status_code=404, detail="Profesor no encontrado")
    try:
        session.exec(delete(ProfesorCurso).where(ProfesorCurso.id_profesor == id_profesor))
        session.exec(delete(HorarioFinal).where(HorarioFinal.id_profesor == id_profesor))
        session.exec(delete(Tutoria).where(Tutoria.id_profesor == id_profesor))
        session.exec(delete(ProfesorDisponibilidad).where(ProfesorDisponibilidad.id_profesor == id_profesor))
        session.exec(delete(ProfesorPreferencia).where(ProfesorPreferencia.id_profesor == id_profesor))
        session.exec(delete(SedeProfesor).where(SedeProfesor.id_profesor == id_profesor))
        session.exec(delete(GradoProfesor).where(GradoProfesor.id_profesor == id_profesor))
        
        session.delete(db_profesor)
        session.commit()
        return {"message": "Profesor borrado exitosamente junto con sus dependencias"}
    except Exception as e:
        session.rollback()
        raise AppError([f"Error al eliminar el profesor: {str(e)}"])

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

@app.put("/api/profesor-curso/{id_profesor_curso}", response_model=ProfesorCurso)
def update_profesor_curso(id_profesor_curso: int, pc_update: ProfesorCurso, session: Session = Depends(get_session)):
    db = session.get(ProfesorCurso, id_profesor_curso)
    if not db: raise HTTPException(status_code=404, detail="ProfesorCurso no encontrado")
    db.id_profesor = pc_update.id_profesor
    db.id_curso = pc_update.id_curso
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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
    _reject_if_dependents(session, "la Sección", [
        (select(SeccionTurno).where(SeccionTurno.id_seccion == id_seccion), "Sección-Turnos"),
        (select(HorarioFinal).where(HorarioFinal.id_seccion == id_seccion), "Horarios Finales"),
        (select(Tutoria).where(Tutoria.id_seccion == id_seccion), "Tutorías"),
    ])
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

@app.put("/api/seccion-turno/{id_seccion_turno}", response_model=SeccionTurno)
def update_seccion_turno(id_seccion_turno: int, st_update: SeccionTurno, session: Session = Depends(get_session)):
    db = session.get(SeccionTurno, id_seccion_turno)
    if not db: raise HTTPException(status_code=404, detail="SeccionTurno no encontrado")
    db.id_seccion = st_update.id_seccion
    db.id_turno = st_update.id_turno
    db.id_dia = st_update.id_dia
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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

@app.put("/api/horario-final/{id_horario_final}", response_model=HorarioFinal)
def update_horario_final(id_horario_final: int, hf_update: HorarioFinal, session: Session = Depends(get_session)):
    db = session.get(HorarioFinal, id_horario_final)
    if not db: raise HTTPException(status_code=404, detail="HorarioFinal no encontrado")
    db.id_seccion = hf_update.id_seccion
    db.id_dia = hf_update.id_dia
    db.num_bloque = hf_update.num_bloque
    db.id_curso = hf_update.id_curso
    db.id_profesor = hf_update.id_profesor
    db.id_turno = hf_update.id_turno
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

@app.delete("/api/horario-final/{id_horario_final}")
def delete_horario_final(id_horario_final: int, session: Session = Depends(get_session)):
    db = session.get(HorarioFinal, id_horario_final)
    if not db: raise HTTPException(status_code=404)
    session.delete(db)
    session.commit()
    return {"message": "Borrado"}

# --- Endpoints: Edición de Horarios ---
class MoveAssignmentRequest(BaseModel):
    seccion_id: int
    curso_id: int
    profesor_id: int
    dia_origen_id: int
    turno_origen_id: int
    slot_inicio_origen: int
    horas_origen: int
    dia_destino_id: int
    turno_destino_id: int
    slot_inicio_destino: int
    horas_destino: int

@app.post("/api/horario-final/validate-move")
def api_validate_move(req: MoveAssignmentRequest, session: Session = Depends(get_session)):
    """Valida un movimiento propuesto sin aplicarlo."""
    result = validate_move(session, req.model_dump())
    return result

@app.post("/api/horario-final/apply-move")
def api_apply_move(req: MoveAssignmentRequest, session: Session = Depends(get_session)):
    """Aplica un movimiento validado sin crear snapshot."""
    validation = validate_move(session, req.model_dump())
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={"conflicts": validation["conflicts"], "warnings": validation["warnings"]})
    move_data = req.model_dump()
    move_data["isSwap"] = validation.get("isSwap", False)
    move_data["swapInfo"] = validation.get("swapInfo")
    resultado = apply_move(session, move_data)
    return {"success": True, "resultado": resultado, "isSwap": validation.get("isSwap", False)}

@app.post("/api/horario-final/save-edits")
def api_save_edits(session: Session = Depends(get_session)):
    """Guarda el estado actual del horario como un snapshot editado."""
    from backend.engine_connector import build_current_state, _guardar_snapshot
    dict_resultado = build_current_state(session)
    _guardar_snapshot(session, dict_resultado, es_editada=True)
    return {"success": True, "snapshot": dict_resultado}

@app.get("/api/horario-summary")
def api_horario_summary(session: Session = Depends(get_session)):
    """Retorna un resumen condensado del horario activo (~50-100 líneas)."""
    from backend.engine_connector import build_horario_summary
    return build_horario_summary(session)

@app.get("/api/horario-analysis")
def api_horario_analysis(session: Session = Depends(get_session)):
    """Retorna análisis del horario: métricas explicadas, problemas y sugerencias."""
    from backend.engine_connector import build_horario_analysis
    return build_horario_analysis(session)

@app.get("/api/horario-metricas-motor")
def api_horario_metricas_motor(session: Session = Depends(get_session)):
    """Retorna las métricas calculadas por el motor (resumen_slots, profesores, cursos)."""
    from backend.engine_connector import calcular_metricas_motor
    return calcular_metricas_motor(session)

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

@app.put("/api/tutorias/{id_tutoria}", response_model=Tutoria)
def update_tutoria(id_tutoria: int, tutoria_update: Tutoria, session: Session = Depends(get_session)):
    db = session.get(Tutoria, id_tutoria)
    if not db: raise HTTPException(status_code=404, detail="Tutoría no encontrada")
    db.id_seccion = tutoria_update.id_seccion
    db.id_profesor = tutoria_update.id_profesor
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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

@app.put("/api/profesor-sedes/{id_sede_profesor}", response_model=SedeProfesor)
def update_profesor_sede(id_sede_profesor: int, ps_update: SedeProfesor, session: Session = Depends(get_session)):
    db = session.get(SedeProfesor, id_sede_profesor)
    if not db: raise HTTPException(status_code=404, detail="Vínculo no encontrado")
    db.id_profesor = ps_update.id_profesor
    db.id_sede = ps_update.id_sede
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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

@app.put("/api/grado-profesor/{id_grado_profesor}", response_model=GradoProfesor)
def update_grado_profesor(id_grado_profesor: int, gp_update: GradoProfesor, session: Session = Depends(get_session)):
    db = session.get(GradoProfesor, id_grado_profesor)
    if not db: raise HTTPException(status_code=404, detail="Vínculo no encontrado")
    db.id_grado = gp_update.id_grado
    db.id_profesor = gp_update.id_profesor
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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

@app.put("/api/profesor-disponibilidad/{id_disponibilidad}", response_model=ProfesorDisponibilidad)
def update_profesor_disponibilidad(id_disponibilidad: int, pd_update: ProfesorDisponibilidad, session: Session = Depends(get_session)):
    db = session.get(ProfesorDisponibilidad, id_disponibilidad)
    if not db: raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    db.id_profesor = pd_update.id_profesor
    db.id_dia = pd_update.id_dia
    db.id_turno = pd_update.id_turno
    db.id_sede = pd_update.id_sede
    db.nro_bloque = pd_update.nro_bloque
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

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

@app.put("/api/profesor-preferencia/{id_preferencia}", response_model=ProfesorPreferencia)
def update_profesor_preferencia(id_preferencia: int, pp_update: ProfesorPreferencia, session: Session = Depends(get_session)):
    db = session.get(ProfesorPreferencia, id_preferencia)
    if not db: raise HTTPException(status_code=404, detail="Preferencia no encontrada")
    db.id_profesor = pp_update.id_profesor
    db.id_dia = pp_update.id_dia
    db.id_turno = pp_update.id_turno
    db.id_sede = pp_update.id_sede
    db.nro_bloque = pp_update.nro_bloque
    session.add(db)
    session.commit()
    session.refresh(db)
    return db

@app.delete("/api/profesor-preferencia/{id_preferencia}")
def delete_profesor_preferencia(id_preferencia: int, session: Session = Depends(get_session)):
    db = session.get(ProfesorPreferencia, id_preferencia)
    if not db: raise HTTPException(status_code=404, detail="Preferencia no encontrada")
    session.delete(db)
    session.commit()
    return {"message": "Preferencia borrada"}

# --- Endpoints del Motor ---
from backend.engine_connector import generar_horario_engine, start_generation, get_progress, validate_move, apply_move

@app.post("/api/generar-horario")
def desencadenar_motor(session: Session = Depends(get_session)):
    try:
        resultado = generar_horario_engine(session)
        return resultado
    except AppError as e:
        return {"status": "error", "errores": e.errors}

@app.post("/api/generar-horario/start")
def start_generar_horario():
    """Lanza la generación en background y devuelve task_id."""
    from backend.database import engine
    task_id = start_generation(engine)
    return {"task_id": task_id}

@app.get("/api/horario-progress/{task_id}")
def horario_progress(task_id: str):
    """Devuelve el progreso actual de la generación."""
    return get_progress(task_id)

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
        groups = []
        current_group = [slots[0]]
        for i in range(1, len(slots)):
            if slots[i] == current_group[-1] + 1:
                current_group.append(slots[i])
            else:
                groups.append(current_group)
                current_group = [slots[i]]
        groups.append(current_group)

        for group in groups:
            asignaciones.append({
                "seccion_id": f"SEC_{sec}",
                "curso_id": f"CUR_{cur}",
                "profesor_id": f"PROF_{prof}",
                "dia": dias_db.get(dia_id, ""),
                "turno": turno,
                "slot_inicio": group[0] - 1,
                "horas": len(group)
            })
    
    snapshot = session.exec(select(HorarioSnapshot).where(HorarioSnapshot.is_active == True)).first()
    if snapshot:
        estado = snapshot.estado or "GUARDADO"
        estadisticas = {
            "tiempo_segundos": snapshot.tiempo_segundos or 0,
            "ramas_exploradas": 0,
            "conflictos": 0
        }
        if snapshot.json_data:
            try:
                snap_data = json.loads(snapshot.json_data)
                if "estadisticas" in snap_data:
                    estadisticas = snap_data["estadisticas"]
            except Exception:
                pass
        all_snapshots = session.exec(select(HorarioSnapshot).order_by(HorarioSnapshot.created_at.asc())).all()
        version = next((i + 1 for i, s in enumerate(all_snapshots) if s.id_snapshot == snapshot.id_snapshot), 1)
        nombre_snapshot = snapshot.nombre
    else:
        estado = "GUARDADO"
        estadisticas = {"tiempo_segundos": 0, "ramas_exploradas": 0, "conflictos": 0}
        version = 0
        nombre_snapshot = None

    return {
        "status": "success",
        "resultado": {
            "estado": estado,
            "mensaje": "Horario cargado desde la base de datos.",
            "estadisticas": estadisticas,
            "version": version,
            "nombre": nombre_snapshot,
            "asignaciones": asignaciones
        }
    }


# --- Snapshots (Historial) ---
@app.get("/api/horario-snapshots")
def get_snapshots(session: Session = Depends(get_session)):
    snapshots = session.exec(select(HorarioSnapshot).order_by(HorarioSnapshot.created_at.desc())).all()
    all_snapshots_asc = session.exec(select(HorarioSnapshot).order_by(HorarioSnapshot.created_at.asc())).all()
    version_map = {s.id_snapshot: i + 1 for i, s in enumerate(all_snapshots_asc)}
    return [
        {
            "id_snapshot": s.id_snapshot,
            "nombre": s.nombre,
            "version": version_map.get(s.id_snapshot, 0),
            "descripcion": s.descripcion,
            "asignaciones_count": s.asignaciones_count,
            "estado": s.estado,
            "tiempo_segundos": s.tiempo_segundos,
            "is_active": s.is_active,
            "es_editada": s.es_editada,
            "created_at": s.created_at,
        }
        for s in snapshots
    ]

@app.get("/api/horario-snapshots/{id_snapshot}")
def get_snapshot(id_snapshot: int, session: Session = Depends(get_session)):
    snapshot = session.get(HorarioSnapshot, id_snapshot)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    return {
        "id_snapshot": snapshot.id_snapshot,
        "nombre": snapshot.nombre,
        "descripcion": snapshot.descripcion,
        "json_data": json.loads(snapshot.json_data),
        "asignaciones_count": snapshot.asignaciones_count,
        "estado": snapshot.estado,
        "tiempo_segundos": snapshot.tiempo_segundos,
        "is_active": snapshot.is_active,
        "created_at": snapshot.created_at,
    }

@app.put("/api/horario-snapshots/{id_snapshot}")
def update_snapshot(id_snapshot: int, update: SnapshotUpdate, session: Session = Depends(get_session)):
    snapshot = session.get(HorarioSnapshot, id_snapshot)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    if update.nombre is not None:
        snapshot.nombre = update.nombre
    if update.descripcion is not None:
        snapshot.descripcion = update.descripcion
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return {"message": "Snapshot actualizado"}

@app.delete("/api/horario-snapshots/{id_snapshot}")
def delete_snapshot(id_snapshot: int, session: Session = Depends(get_session)):
    snapshot = session.get(HorarioSnapshot, id_snapshot)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    session.delete(snapshot)
    session.commit()
    return {"message": "Snapshot eliminado"}

@app.post("/api/horario-snapshots/{id_snapshot}/load")
def load_snapshot(id_snapshot: int, session: Session = Depends(get_session)):
    """Carga un snapshot como horario activo (reescribe horario_final)."""
    snapshot = session.get(HorarioSnapshot, id_snapshot)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")

    data = json.loads(snapshot.json_data)
    asignaciones = data.get("asignaciones", [])
    if not asignaciones:
        raise HTTPException(status_code=400, detail="El snapshot no tiene asignaciones")

    old = session.exec(select(HorarioFinal)).all()
    for o in old:
        session.delete(o)
    session.commit()

    all_snapshots = session.exec(select(HorarioSnapshot)).all()
    for s in all_snapshots:
        s.is_active = False
        session.add(s)

    snapshot.is_active = True
    session.add(snapshot)

    dias_db = {d.nombre_dia: d.id_dia for d in session.exec(select(Dias)).all()}
    turno_db = {t.nombre: t.id_turno for t in session.exec(select(Turno)).all()}

    for asig in asignaciones:
        sec_id = int(asig["seccion_id"].replace("SEC_", ""))
        if asig["curso_id"] == "TUT1":
            tut_curso = session.exec(select(Cursos).where(Cursos.nombre_curso.like("%Tutoría%"))).first()
            cur_id = tut_curso.id_curso if tut_curso else 18
        else:
            cur_id = int(asig["curso_id"].replace("CUR_", ""))
        prof_id = int(asig["profesor_id"].replace("PROF_", ""))
        id_dia = dias_db.get(asig["dia"])
        id_turno = turno_db.get(asig.get("turno", "Mañana"))
        slot_inicio = asig.get("slot_inicio", 0)
        horas = asig.get("horas", 1)

        for i in range(horas):
            session.add(HorarioFinal(
                id_seccion=sec_id,
                id_dia=id_dia,
                num_bloque=slot_inicio + i + 1,
                id_turno=id_turno,
                id_curso=cur_id,
                id_profesor=prof_id
            ))

    session.commit()
    return {"message": f"Snapshot '{snapshot.nombre}' cargado como horario activo"}
