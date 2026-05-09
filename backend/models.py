from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import time

# --- 1. Tablas Maestras (Independientes) ---
class Colegio(SQLModel, table=True):
    __tablename__ = "colegio"
    id_colegio: Optional[int] = Field(default=None, primary_key=True)
    nombre_colegio: str
    
    sedes: List["Sedes"] = Relationship(back_populates="colegio")
    usuarios: List["Usuario"] = Relationship(back_populates="colegio")

class Turno(SQLModel, table=True):
    __tablename__ = "turno"
    id_turno: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    
    bloques: List["Bloque"] = Relationship(back_populates="turno")
    seccion_turnos: List["SeccionTurno"] = Relationship(back_populates="turno")

class Grado(SQLModel, table=True):
    __tablename__ = "grado"
    id_grado: Optional[int] = Field(default=None, primary_key=True)
    numero: int
    
    secciones: List["Seccion"] = Relationship(back_populates="grado")
    grado_dia_configs: List["GradoDiaConfig"] = Relationship(back_populates="grado")
    planes_estudio: List["PlanEstudio"] = Relationship(back_populates="grado")

class Dias(SQLModel, table=True):
    __tablename__ = "dias"
    id_dia: Optional[int] = Field(default=None, primary_key=True)
    nombre_dia: str
    orden: int
    
    grado_dia_configs: List["GradoDiaConfig"] = Relationship(back_populates="dia")
    seccion_turnos: List["SeccionTurno"] = Relationship(back_populates="dia")
    restricciones: List["Restricciones"] = Relationship(back_populates="dia")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="dia")

class Areas(SQLModel, table=True):
    __tablename__ = "areas"
    id_area: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    max_horas_dia: int
    
    cursos: List["Cursos"] = Relationship(back_populates="area")

# --- 2. Tablas con Dependencias de Nivel 1 ---
class Sedes(SQLModel, table=True):
    __tablename__ = "sedes"
    id_sede: Optional[int] = Field(default=None, primary_key=True)
    id_colegio: Optional[int] = Field(default=None, foreign_key="colegio.id_colegio")
    nombre_sede: str
    
    colegio: Optional[Colegio] = Relationship(back_populates="sedes")
    profesores: List["Profesores"] = Relationship(back_populates="sede")
    secciones: List["Seccion"] = Relationship(back_populates="sede")

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    nombre: str
    id_colegio: Optional[int] = Field(default=None, foreign_key="colegio.id_colegio")
    
    colegio: Optional[Colegio] = Relationship(back_populates="usuarios")

class Bloque(SQLModel, table=True):
    __tablename__ = "bloque"
    id_bloque: Optional[int] = Field(default=None, primary_key=True)
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    numero_bloque: int
    hora_inicio: time
    hora_final: time
    
    turno: Optional[Turno] = Relationship(back_populates="bloques")
    restricciones: List["Restricciones"] = Relationship(back_populates="bloque")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="bloque")

class Cursos(SQLModel, table=True):
    __tablename__ = "cursos"
    id_curso: Optional[int] = Field(default=None, primary_key=True)
    id_area: Optional[int] = Field(default=None, foreign_key="areas.id_area")
    nombre_curso: str
    
    area: Optional[Areas] = Relationship(back_populates="cursos")
    planes_estudio: List["PlanEstudio"] = Relationship(back_populates="curso")
    profesor_cursos: List["ProfesorCurso"] = Relationship(back_populates="curso")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="curso")

class Profesores(SQLModel, table=True):
    __tablename__ = "profesores"
    id_profesores: Optional[int] = Field(default=None, primary_key=True)
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    nombre_profesor: str
    
    sede: Optional[Sedes] = Relationship(back_populates="profesores")
    profesor_cursos: List["ProfesorCurso"] = Relationship(back_populates="profesor")
    restricciones: List["Restricciones"] = Relationship(back_populates="profesor")
    cargas_academicas: List["CargaAcademica"] = Relationship(back_populates="profesor")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="profesor")
    tutorias: List["Tutoria"] = Relationship(back_populates="profesor")

# --- 3. Tablas con Dependencias de Nivel 2 ---
class Seccion(SQLModel, table=True):
    __tablename__ = "seccion"
    id_seccion: Optional[int] = Field(default=None, primary_key=True)
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    nombre: str
    
    sede: Optional[Sedes] = Relationship(back_populates="secciones")
    grado: Optional[Grado] = Relationship(back_populates="secciones")
    seccion_turnos: List["SeccionTurno"] = Relationship(back_populates="seccion")
    cargas_academicas: List["CargaAcademica"] = Relationship(back_populates="seccion")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="seccion")
    tutorias: List["Tutoria"] = Relationship(back_populates="seccion")

class GradoDiaConfig(SQLModel, table=True):
    __tablename__ = "grado_dia_config"
    id_config: Optional[int] = Field(default=None, primary_key=True)
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    bloques_dia: int
    
    grado: Optional[Grado] = Relationship(back_populates="grado_dia_configs")
    dia: Optional[Dias] = Relationship(back_populates="grado_dia_configs")

class PlanEstudio(SQLModel, table=True):
    __tablename__ = "plan_estudio"
    id_plan: Optional[int] = Field(default=None, primary_key=True)
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    horas_semanales: int
    
    grado: Optional[Grado] = Relationship(back_populates="planes_estudio")
    curso: Optional[Cursos] = Relationship(back_populates="planes_estudio")
    cargas_academicas: List["CargaAcademica"] = Relationship(back_populates="plan")

class ProfesorCurso(SQLModel, table=True):
    __tablename__ = "profesor_curso"
    id_profesor_curso: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesores")
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    
    profesor: Optional[Profesores] = Relationship(back_populates="profesor_cursos")
    curso: Optional[Cursos] = Relationship(back_populates="profesor_cursos")

# --- 4. Tablas con Dependencias de Nivel 3 (Relacionales/Configuración) ---
class SeccionTurno(SQLModel, table=True):
    __tablename__ = "seccion_turno"
    id_seccion_turno: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    
    seccion: Optional[Seccion] = Relationship(back_populates="seccion_turnos")
    turno: Optional[Turno] = Relationship(back_populates="seccion_turnos")
    dia: Optional[Dias] = Relationship(back_populates="seccion_turnos")

class Restricciones(SQLModel, table=True):
    __tablename__ = "restricciones"
    id_restricciones: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesores")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    id_bloque: Optional[int] = Field(default=None, foreign_key="bloque.id_bloque")
    
    profesor: Optional[Profesores] = Relationship(back_populates="restricciones")
    dia: Optional[Dias] = Relationship(back_populates="restricciones")
    bloque: Optional[Bloque] = Relationship(back_populates="restricciones")

class CargaAcademica(SQLModel, table=True):
    __tablename__ = "carga_academica"
    id_carga: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesores")
    id_plan: Optional[int] = Field(default=None, foreign_key="plan_estudio.id_plan")
    
    seccion: Optional[Seccion] = Relationship(back_populates="cargas_academicas")
    profesor: Optional[Profesores] = Relationship(back_populates="cargas_academicas")
    plan: Optional[PlanEstudio] = Relationship(back_populates="cargas_academicas")

class Tutoria(SQLModel, table=True):
    __tablename__ = "tutoria"
    id_tutoria: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesores")
    
    seccion: Optional[Seccion] = Relationship(back_populates="tutorias")
    profesor: Optional[Profesores] = Relationship(back_populates="tutorias")

# --- 5. Resultado Final ---
class HorarioFinal(SQLModel, table=True):
    __tablename__ = "horario_final"
    id_horario_final: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    id_bloque: Optional[int] = Field(default=None, foreign_key="bloque.id_bloque")
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesores")
    
    seccion: Optional[Seccion] = Relationship(back_populates="horarios_finales")
    dia: Optional[Dias] = Relationship(back_populates="horarios_finales")
    bloque: Optional[Bloque] = Relationship(back_populates="horarios_finales")
    curso: Optional[Cursos] = Relationship(back_populates="horarios_finales")
    profesor: Optional[Profesores] = Relationship(back_populates="horarios_finales")
