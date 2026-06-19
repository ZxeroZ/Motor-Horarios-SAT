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
    profesor_disponibilidad: List["ProfesorDisponibilidad"] = Relationship(back_populates="turno")
    profesor_preferencia: List["ProfesorPreferencia"] = Relationship(back_populates="turno")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="turno")
    bloques_reservados: List["BloqueReservado"] = Relationship(back_populates="turno")

class Grado(SQLModel, table=True):
    __tablename__ = "grado"
    id_grado: Optional[int] = Field(default=None, primary_key=True)
    numero: int
    
    secciones: List["Seccion"] = Relationship(back_populates="grado")
    grado_dia_configs: List["GradoDiaConfig"] = Relationship(back_populates="grado")
    planes_estudio: List["PlanEstudio"] = Relationship(back_populates="grado")
    grados_profesor: List["GradoProfesor"] = Relationship(back_populates="grado")
    bloques_grado: List["BloqueGrado"] = Relationship(back_populates="grado")

class Dias(SQLModel, table=True):
    __tablename__ = "dias"
    id_dia: Optional[int] = Field(default=None, primary_key=True)
    nombre_dia: str
    orden: int
    
    grado_dia_configs: List["GradoDiaConfig"] = Relationship(back_populates="dia")
    seccion_turnos: List["SeccionTurno"] = Relationship(back_populates="dia")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="dia")
    profesor_disponibilidad: List["ProfesorDisponibilidad"] = Relationship(back_populates="dia")
    profesor_preferencia: List["ProfesorPreferencia"] = Relationship(back_populates="dia")
    bloques_reservados: List["BloqueReservado"] = Relationship(back_populates="dia")

class Areas(SQLModel, table=True):
    __tablename__ = "areas"
    id_area: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    max_horas_dia: Optional[int] = None
    
    cursos: List["Cursos"] = Relationship(back_populates="area")

class Profesores(SQLModel, table=True):
    __tablename__ = "profesores"
    id_profesor: Optional[int] = Field(default=None, primary_key=True)
    nombre_profesor: str
    
    profesor_cursos: List["ProfesorCurso"] = Relationship(back_populates="profesor")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="profesor")
    tutorias: List["Tutoria"] = Relationship(back_populates="profesor")
    profesor_disponibilidad: List["ProfesorDisponibilidad"] = Relationship(back_populates="profesor")
    profesor_preferencia: List["ProfesorPreferencia"] = Relationship(back_populates="profesor")
    sedes_profesor: List["SedeProfesor"] = Relationship(back_populates="profesor")
    grados_profesor: List["GradoProfesor"] = Relationship(back_populates="profesor")


# --- 2. Tablas con Dependencias Simples ---
class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    nombre: str
    id_colegio: Optional[int] = Field(default=None, foreign_key="colegio.id_colegio")
    
    colegio: Optional[Colegio] = Relationship(back_populates="usuarios")

class Sedes(SQLModel, table=True):
    __tablename__ = "sedes"
    id_sede: Optional[int] = Field(default=None, primary_key=True)
    id_colegio: Optional[int] = Field(default=None, foreign_key="colegio.id_colegio")
    nombre_sede: str
    
    colegio: Optional[Colegio] = Relationship(back_populates="sedes")
    secciones: List["Seccion"] = Relationship(back_populates="sede")
    profesor_disponibilidad: List["ProfesorDisponibilidad"] = Relationship(back_populates="sede")
    profesor_preferencia: List["ProfesorPreferencia"] = Relationship(back_populates="sede")
    sedes_profesor: List["SedeProfesor"] = Relationship(back_populates="sede")
    bloques_reservados: List["BloqueReservado"] = Relationship(back_populates="sede")

class Bloque(SQLModel, table=True):
    __tablename__ = "bloque"
    id_bloque: Optional[int] = Field(default=None, primary_key=True)
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    numero_bloque: Optional[int] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    
    turno: Optional[Turno] = Relationship(back_populates="bloques")

class Cursos(SQLModel, table=True):
    __tablename__ = "cursos"
    id_curso: Optional[int] = Field(default=None, primary_key=True)
    id_area: Optional[int] = Field(default=None, foreign_key="areas.id_area")
    nombre_curso: str
    requiere_espacio_unico: Optional[bool] = Field(default=False)
    
    area: Optional[Areas] = Relationship(back_populates="cursos")
    planes_estudio: List["PlanEstudio"] = Relationship(back_populates="curso")
    profesor_cursos: List["ProfesorCurso"] = Relationship(back_populates="curso")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="curso")


# --- 3. Tablas de Configuración y Relaciones Intermedias ---
class Seccion(SQLModel, table=True):
    __tablename__ = "seccion"
    id_seccion: Optional[int] = Field(default=None, primary_key=True)
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    nombre: Optional[str] = None
    
    sede: Optional[Sedes] = Relationship(back_populates="secciones")
    grado: Optional[Grado] = Relationship(back_populates="secciones")
    seccion_turnos: List["SeccionTurno"] = Relationship(back_populates="seccion")
    horarios_finales: List["HorarioFinal"] = Relationship(back_populates="seccion")
    tutorias: List["Tutoria"] = Relationship(back_populates="seccion")

class GradoDiaConfig(SQLModel, table=True):
    __tablename__ = "grado_dia_config"
    id_config: Optional[int] = Field(default=None, primary_key=True)
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    bloques_dia: Optional[int] = None
    
    grado: Optional[Grado] = Relationship(back_populates="grado_dia_configs")
    dia: Optional[Dias] = Relationship(back_populates="grado_dia_configs")

class PlanEstudio(SQLModel, table=True):
    __tablename__ = "plan_estudio"
    id_plan: Optional[int] = Field(default=None, primary_key=True)
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    horas_semanales: Optional[int] = None
    
    grado: Optional[Grado] = Relationship(back_populates="planes_estudio")
    curso: Optional[Cursos] = Relationship(back_populates="planes_estudio")

class SedeProfesor(SQLModel, table=True):
    __tablename__ = "sedes_profesor"
    id_sede_profesor: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    
    profesor: Optional[Profesores] = Relationship(back_populates="sedes_profesor")
    sede: Optional[Sedes] = Relationship(back_populates="sedes_profesor")

class GradoProfesor(SQLModel, table=True):
    __tablename__ = "grado_profesor"
    id_grado_profesor: Optional[int] = Field(default=None, primary_key=True)
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    
    grado: Optional[Grado] = Relationship(back_populates="grados_profesor")
    profesor: Optional[Profesores] = Relationship(back_populates="grados_profesor")

class ProfesorDisponibilidad(SQLModel, table=True):
    __tablename__ = "profesor_disponibilidad"
    id_disponibilidad: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    nro_bloque: Optional[int] = None

    profesor: Optional[Profesores] = Relationship(back_populates="profesor_disponibilidad")
    dia: Optional[Dias] = Relationship(back_populates="profesor_disponibilidad")
    turno: Optional[Turno] = Relationship(back_populates="profesor_disponibilidad")
    sede: Optional[Sedes] = Relationship(back_populates="profesor_disponibilidad")

class ProfesorPreferencia(SQLModel, table=True):
    __tablename__ = "profesor_preferencia"
    id_preferencia: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    nro_bloque: Optional[int] = None

    profesor: Optional[Profesores] = Relationship(back_populates="profesor_preferencia")
    dia: Optional[Dias] = Relationship(back_populates="profesor_preferencia")
    turno: Optional[Turno] = Relationship(back_populates="profesor_preferencia")
    sede: Optional[Sedes] = Relationship(back_populates="profesor_preferencia")

class ProfesorCurso(SQLModel, table=True):
    __tablename__ = "profesor_curso"
    id_profesor_curso: Optional[int] = Field(default=None, primary_key=True)
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    
    profesor: Optional[Profesores] = Relationship(back_populates="profesor_cursos")
    curso: Optional[Cursos] = Relationship(back_populates="profesor_cursos")


# --- 4. Tablas con Dependencias de Nivel 3 ---
class SeccionTurno(SQLModel, table=True):
    __tablename__ = "seccion_turno"
    id_seccion_turno: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    
    seccion: Optional[Seccion] = Relationship(back_populates="seccion_turnos")
    turno: Optional[Turno] = Relationship(back_populates="seccion_turnos")
    dia: Optional[Dias] = Relationship(back_populates="seccion_turnos")

class Tutoria(SQLModel, table=True):
    __tablename__ = "tutoria"
    id_tutoria: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    
    seccion: Optional[Seccion] = Relationship(back_populates="tutorias")
    profesor: Optional[Profesores] = Relationship(back_populates="tutorias")


# --- 5. Bloques Reservados ---
class BloqueReservado(SQLModel, table=True):
    __tablename__ = "bloque_reservado"
    id_bloque_reservado: Optional[int] = Field(default=None, primary_key=True)
    nombre: Optional[str] = None
    id_sede: Optional[int] = Field(default=None, foreign_key="sedes.id_sede")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    
    sede: Optional[Sedes] = Relationship(back_populates="bloques_reservados")
    dia: Optional[Dias] = Relationship(back_populates="bloques_reservados")
    turno: Optional[Turno] = Relationship(back_populates="bloques_reservados")
    bloques_grado: List["BloqueGrado"] = Relationship(back_populates="bloque_reservado")
    bloques_opcion: List["BloqueOpcion"] = Relationship(back_populates="bloque_reservado")

class BloqueGrado(SQLModel, table=True):
    __tablename__ = "bloque_grado"
    id_bloque_grado: Optional[int] = Field(default=None, primary_key=True)
    id_bloque_reservado: Optional[int] = Field(default=None, foreign_key="bloque_reservado.id_bloque_reservado")
    id_grado: Optional[int] = Field(default=None, foreign_key="grado.id_grado")
    
    bloque_reservado: Optional[BloqueReservado] = Relationship(back_populates="bloques_grado")
    grado: Optional[Grado] = Relationship(back_populates="bloques_grado")

class BloqueOpcion(SQLModel, table=True):
    __tablename__ = "bloque_opcion"
    id_bloque_opcion: Optional[int] = Field(default=None, primary_key=True)
    id_bloque_reservado: Optional[int] = Field(default=None, foreign_key="bloque_reservado.id_bloque_reservado")
    nro_opcion: Optional[int] = None
    nombre: Optional[str] = None
    
    bloque_reservado: Optional[BloqueReservado] = Relationship(back_populates="bloques_opcion")
    slots: List["BloqueOpcionSlot"] = Relationship(back_populates="bloque_opcion")

class BloqueOpcionSlot(SQLModel, table=True):
    __tablename__ = "bloque_opcion_slot"
    id_bloque_opcion_slot: Optional[int] = Field(default=None, primary_key=True)
    id_bloque_opcion: Optional[int] = Field(default=None, foreign_key="bloque_opcion.id_bloque_opcion")
    nro_bloque: Optional[int] = None
    
    bloque_opcion: Optional[BloqueOpcion] = Relationship(back_populates="slots")


# --- 6. Resultado Final ---
class HorarioFinal(SQLModel, table=True):
    __tablename__ = "horario_final"
    id_horario_final: Optional[int] = Field(default=None, primary_key=True)
    id_seccion: Optional[int] = Field(default=None, foreign_key="seccion.id_seccion")
    id_dia: Optional[int] = Field(default=None, foreign_key="dias.id_dia")
    num_bloque: Optional[int] = None
    id_curso: Optional[int] = Field(default=None, foreign_key="cursos.id_curso")
    id_profesor: Optional[int] = Field(default=None, foreign_key="profesores.id_profesor")
    id_turno: Optional[int] = Field(default=None, foreign_key="turno.id_turno")
    
    seccion: Optional[Seccion] = Relationship(back_populates="horarios_finales")
    dia: Optional[Dias] = Relationship(back_populates="horarios_finales")
    curso: Optional[Cursos] = Relationship(back_populates="horarios_finales")
    profesor: Optional[Profesores] = Relationship(back_populates="horarios_finales")
    turno: Optional[Turno] = Relationship(back_populates="horarios_finales")
