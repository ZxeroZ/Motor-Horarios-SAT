from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import time

# --- Módulo Administrativo ---
class Colegio(SQLModel, table=True):
    id_colegio: Optional[int] = Field(default=None, primary_key=True)
    nombre: str

    sedes: List["Sede"] = Relationship(back_populates="colegio")

class Sede(SQLModel, table=True):
    id_sede: Optional[int] = Field(default=None, primary_key=True)
    nombre_sede: str
    id_colegio: Optional[int] = Field(default=None, foreign_key="colegio.id_colegio")
    
    colegio: Optional[Colegio] = Relationship(back_populates="sedes")
    secciones: List["Seccion"] = Relationship(back_populates="sede")
    profesores: List["Profesor"] = Relationship(back_populates="sede")

class Usuario(SQLModel, table=True):
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    rol: str

# --- Módulo Curricular ---
class Area(SQLModel, table=True):
    __tablename__ = "areas"
    id_area: Optional[int] = Field(default=None, primary_key=True)
    nombre_area: str
    max_horas_dia: int = Field(default=4) # Agregado basado en json

    cursos: List["Curso"] = Relationship(back_populates="area")

class Curso(SQLModel, table=True):
    __tablename__ = "cursos"
    id_curso: Optional[int] = Field(default=None, primary_key=True)
    nombre_curso: str
    id_area: Optional[int] = Field(default=None, foreign_key="areas.id_area")

    area: Optional[Area] = Relationship(back_populates="cursos")

class Grado(SQLModel, table=True):
    id_grado: Optional[int] = Field(default=None, primary_key=True)
    numero: int # Ej 1, 2, 3
    nombre_grado: str = Field(default="") # Ej "1° Secundaria"

    secciones: List["Seccion"] = Relationship(back_populates="grado")
    planes_estudio: List["PlanEstudio"] = Relationship(back_populates="grado")

class Seccion(SQLModel, table=True):
    id_seccion: Optional[int] = Field(default=None, primary_key=True)
    letra: str # Ej "A", "B"
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_sede: Optional[int] = Field(default=None, foreign_key="sede.id_sede")

    grado: Optional[Grado] = Relationship(back_populates="secciones")
    sede: Optional[Sede] = Relationship(back_populates="secciones")

class PlanEstudio(SQLModel, table=True):
    __tablename__ = "plan_estudio"
    id_estudio: Optional[int] = Field(default=None, primary_key=True)
    id_grado: int = Field(foreign_key="grado.id_grado")
    id_curso: int = Field(foreign_key="cursos.id_curso")
    horas_semanales: int

    grado: Optional[Grado] = Relationship(back_populates="planes_estudio")

# --- Módulo Temporal y Configuración ---
class Configuracion(SQLModel, table=True):
    id_configuracion: Optional[int] = Field(default=None, primary_key=True)
    nombre_turno: str # Ej Mañana, Tarde
    hora_inicio: time
    hora_final: time
    duracion_bloque: int # En minutos

class Dia(SQLModel, table=True):
    __tablename__ = "dias"
    id_dia: Optional[int] = Field(default=None, primary_key=True)
    nombre_dia: str
    orden: int

class DiaGrado(SQLModel, table=True):
    __tablename__ = "dia_grado"
    id_dia_grado: Optional[int] = Field(default=None, primary_key=True)
    id_dia: int = Field(foreign_key="dias.id_dia")
    id_grado: int = Field(foreign_key="grado.id_grado")
    habilitado: bool

class Bloque(SQLModel, table=True):
    __tablename__ = "bloques"
    id_bloque: Optional[int] = Field(default=None, primary_key=True)
    id_turno: int = Field(foreign_key="configuracion.id_configuracion") # turnos son config en el diagrama
    nombre_bloque: str # E.g Slot 1
    hora_inicio: time
    hora_final: time

# --- Módulo Docente y Restricciones ---
class Profesor(SQLModel, table=True):
    __tablename__ = "profesores"
    id_profesor: Optional[int] = Field(default=None, primary_key=True)
    nombre_profesor: str
    id_sede: Optional[int] = Field(default=None, foreign_key="sede.id_sede")
    max_horas_dia: int = Field(default=6) # Agregado basado en json

    sede: Optional[Sede] = Relationship(back_populates="profesores")
    cursos_habilitados: List["ProfesorCurso"] = Relationship(back_populates="profesor")

class ProfesorCurso(SQLModel, table=True):
    __tablename__ = "profesor_curso"
    id_profesor_curso: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: int = Field(foreign_key="profesores.id_profesor")
    id_curso: int = Field(foreign_key="cursos.id_curso")

    profesor: Optional[Profesor] = Relationship(back_populates="cursos_habilitados")

class Restriccion(SQLModel, table=True):
    __tablename__ = "restricciones"
    id_restricciones: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: int = Field(foreign_key="profesores.id_profesor")
    id_dia: int = Field(foreign_key="dias.id_dia")
    id_bloque: int = Field(foreign_key="bloques.id_bloque")

class CargaAcademica(SQLModel, table=True):
    __tablename__ = "carga_academica"
    id_carga: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: int = Field(foreign_key="seccion.id_seccion")
    id_profesor: int = Field(foreign_key="profesores.id_profesor")
    id_plan: int = Field(foreign_key="plan_estudio.id_estudio")

class HorarioFinal(SQLModel, table=True):
    __tablename__ = "horario_final"
    id_horario_final: Optional[int] = Field(default=None, primary_key=True)
    id_carga: int = Field(foreign_key="carga_academica.id_carga")
    id_bloque: int = Field(foreign_key="bloques.id_bloque")
    id_dia: int = Field(foreign_key="dias.id_dia")
