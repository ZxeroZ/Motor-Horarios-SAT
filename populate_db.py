import random
from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import (
    Colegio, Sedes, Grado, Dias, Turno, Bloque, Areas, 
    Cursos, Profesores, ProfesorCurso, Seccion, PlanEstudio
)

def poblar_bd():
    create_db_and_tables()
    with Session(engine) as session:
        # Check si ya hay secciones para no duplicar data tontamente
        if len(session.exec(select(Seccion)).all()) > 2:
            print("La BD ya tiene datos académicos. Borra la DB si quieres empezar de 0.")
            return

        sede = session.exec(select(Sedes)).first()
        if not sede:
            # Crear infraestructura básica si uvicorn no lo hizo a tiempo
            colegio = Colegio(nombre_colegio="Colegio Central")
            session.add(colegio)
            session.commit()
            session.refresh(colegio)
            sede = Sedes(id_colegio=colegio.id_colegio, nombre_sede="Sede Principal")
            session.add(sede)
            session.commit()
            session.refresh(sede)
            
        print("Poblando Base de Datos con esteroides...")

        # 1. Grados
        g1 = Grado(numero=1)
        g2 = Grado(numero=2)
        session.add_all([g1, g2])
        session.commit()

        # 2. Secciones (1A, 1B, 2A)
        sec1A = Seccion(id_grado=g1.id_grado, id_sede=sede.id_sede, nombre="A")
        sec1B = Seccion(id_grado=g1.id_grado, id_sede=sede.id_sede, nombre="B")
        sec2A = Seccion(id_grado=g2.id_grado, id_sede=sede.id_sede, nombre="A")
        session.add_all([sec1A, sec1B, sec2A])
        
        # 3. Áreas
        a_ciencias = Areas(nombre="Ciencias", max_horas_dia=4)
        a_letras = Areas(nombre="Letras", max_horas_dia=4)
        session.add_all([a_ciencias, a_letras])
        session.commit()

        # 4. Cursos
        c_mate = Cursos(id_area=a_ciencias.id_area, nombre_curso="Matemáticas")
        c_fisica = Cursos(id_area=a_ciencias.id_area, nombre_curso="Física")
        c_comu = Cursos(id_area=a_letras.id_area, nombre_curso="Comunicación")
        c_historia = Cursos(id_area=a_letras.id_area, nombre_curso="Historia")
        session.add_all([c_mate, c_fisica, c_comu, c_historia])
        session.commit()

        # 5. Profesores (Con suficientes horas para cubrir todo)
        p_alan = Profesores(id_sede=sede.id_sede, nombre_profesor="Alan Turing", max_horas_dia=8)
        p_isaac = Profesores(id_sede=sede.id_sede, nombre_profesor="Isaac Newton", max_horas_dia=6)
        p_marie = Profesores(id_sede=sede.id_sede, nombre_profesor="Marie Curie", max_horas_dia=8)
        session.add_all([p_alan, p_isaac, p_marie])
        session.commit()

        # 6. ProfesorCurso (Quien dicta que)
        session.add(ProfesorCurso(id_profesor=p_alan.id_profesores, id_curso=c_mate.id_curso))
        session.add(ProfesorCurso(id_profesor=p_isaac.id_profesores, id_curso=c_fisica.id_curso))
        session.add(ProfesorCurso(id_profesor=p_isaac.id_profesores, id_curso=c_mate.id_curso)) # Isaac dicta mate y fisica
        session.add(ProfesorCurso(id_profesor=p_marie.id_profesores, id_curso=c_comu.id_curso))
        session.add(ProfesorCurso(id_profesor=p_marie.id_profesores, id_curso=c_historia.id_curso))
        
        # 7. Plan de Estudio (Malla)
        # 1ro Secundaria (Total 20 horas)
        session.add(PlanEstudio(id_grado=g1.id_grado, id_curso=c_mate.id_curso, horas_semanales=6))
        session.add(PlanEstudio(id_grado=g1.id_grado, id_curso=c_fisica.id_curso, horas_semanales=4))
        session.add(PlanEstudio(id_grado=g1.id_grado, id_curso=c_comu.id_curso, horas_semanales=6))
        session.add(PlanEstudio(id_grado=g1.id_grado, id_curso=c_historia.id_curso, horas_semanales=4))
        
        # 2do Secundaria (Total 20 horas)
        session.add(PlanEstudio(id_grado=g2.id_grado, id_curso=c_mate.id_curso, horas_semanales=8))
        session.add(PlanEstudio(id_grado=g2.id_grado, id_curso=c_fisica.id_curso, horas_semanales=6))
        session.add(PlanEstudio(id_grado=g2.id_grado, id_curso=c_comu.id_curso, horas_semanales=4))
        session.add(PlanEstudio(id_grado=g2.id_grado, id_curso=c_historia.id_curso, horas_semanales=2))
        
        session.commit()
        print("¡Base de Datos Poblada con Éxito!")

if __name__ == "__main__":
    poblar_bd()
