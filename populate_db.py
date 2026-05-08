"""
Poblar la BD con los MISMOS datos del datos.json que el motor resuelve exitosamente.
"""
from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import (
    Colegio, Sedes, Grado, Dias, Turno, Bloque, Areas, 
    Cursos, Profesores, ProfesorCurso, Seccion, PlanEstudio,
    GradoDiaConfig, SeccionTurno, Usuario
)
from datetime import time as pytime

def poblar_bd():
    create_db_and_tables()
    with Session(engine) as s:
        if s.exec(select(Cursos)).first():
            print("La BD ya tiene datos. Borra database.db primero.")
            return

        print("=== Poblando BD con datos del JSON de referencia ===")

        # --- Admin ---
        s.add(Usuario(email="admin@colegio.com", nombre="Administrador", password="123456"))

        # --- Colegio ---
        col = Colegio(nombre_colegio="Colegio Central")
        s.add(col)
        s.commit()
        s.refresh(col)

        # --- Sedes ---
        sede_a = Sedes(id_colegio=col.id_colegio, nombre_sede="Sede A")
        sede_b = Sedes(id_colegio=col.id_colegio, nombre_sede="Sede B")
        s.add_all([sede_a, sede_b])
        s.commit()
        s.refresh(sede_a)
        s.refresh(sede_b)

        # --- Días ---
        dias_nombres = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
        dias = []
        for i, nombre in enumerate(dias_nombres):
            d = Dias(nombre_dia=nombre, orden=i+1)
            s.add(d)
            dias.append(d)
        s.commit()
        for d in dias:
            s.refresh(d)

        # --- Turnos ---
        t_man = Turno(nombre="Mañana")
        t_tar = Turno(nombre="Tarde")
        s.add_all([t_man, t_tar])
        s.commit()
        s.refresh(t_man)
        s.refresh(t_tar)

        # --- Bloques (6 por turno) ---
        for i in range(1, 7):
            s.add(Bloque(id_turno=t_man.id_turno, numero_bloque=i, hora_inicio=pytime(7+i,0), hora_final=pytime(8+i,0)))
            s.add(Bloque(id_turno=t_tar.id_turno, numero_bloque=i, hora_inicio=pytime(13+i,0), hora_final=pytime(14+i,0)))
        s.commit()

        # --- Áreas (Categorías) ---
        areas_data = [
            ("Matemática", 4), ("Comunicación", 4), ("Ciencia y Tecnología", 4),
            ("Ciencias Sociales", 4), ("Idiomas", 4), ("Educación Física", 4), ("Tutoría", 4)
        ]
        areas = {}
        for nombre, max_h in areas_data:
            a = Areas(nombre=nombre, max_horas_dia=max_h)
            s.add(a)
            areas[nombre] = a
        s.commit()
        for a in areas.values():
            s.refresh(a)

        # --- Cursos (18 cursos del JSON) ---
        cursos_data = [
            ("Álgebra", "Matemática"), ("Aritmética", "Matemática"), ("Geometría", "Matemática"),
            ("Trigonometría", "Matemática"), ("Razonamiento Matemático", "Matemática"),
            ("Literatura", "Comunicación"), ("Razonamiento Verbal", "Comunicación"),
            ("Anatomía", "Ciencia y Tecnología"), ("Biología", "Ciencia y Tecnología"),
            ("Química", "Ciencia y Tecnología"), ("Física Elemental", "Ciencia y Tecnología"),
            ("Historia y Geografía", "Ciencias Sociales"), ("Economía", "Ciencias Sociales"),
            ("Filosofía", "Ciencias Sociales"), ("DPCC", "Ciencias Sociales"),
            ("Inglés", "Idiomas"), ("Educación Física", "Educación Física"), ("Tutoría", "Tutoría")
        ]
        cursos = {}
        for nombre, area_nombre in cursos_data:
            c = Cursos(id_area=areas[area_nombre].id_area, nombre_curso=nombre)
            s.add(c)
            cursos[nombre] = c
        s.commit()
        for c in cursos.values():
            s.refresh(c)

        # --- Grados (5 grados) ---
        # Plan de estudio por grado: [("nombre_curso", horas_semanales), ...]
        grados_plan = {
            1: [("Álgebra",3),("Aritmética",2),("Geometría",2),("Trigonometría",1),("Razonamiento Matemático",2),
                ("Literatura",2),("Razonamiento Verbal",3),("Biología",2),("Química",2),("Física Elemental",2),
                ("Historia y Geografía",2),("DPCC",2),("Inglés",2),("Educación Física",2),("Tutoría",1)],
            2: [("Álgebra",3),("Aritmética",2),("Geometría",2),("Trigonometría",1),("Razonamiento Matemático",2),
                ("Literatura",2),("Razonamiento Verbal",3),("Biología",2),("Química",2),("Física Elemental",2),
                ("Historia y Geografía",2),("DPCC",2),("Inglés",2),("Educación Física",2),("Tutoría",1)],
            3: [("Álgebra",3),("Aritmética",2),("Geometría",2),("Trigonometría",1),("Razonamiento Matemático",2),
                ("Literatura",2),("Razonamiento Verbal",3),("Biología",2),("Química",2),("Física Elemental",2),
                ("Historia y Geografía",2),("DPCC",2),("Inglés",2),("Educación Física",2),("Tutoría",1)],
            4: [("Álgebra",3),("Geometría",2),("Trigonometría",1),("Razonamiento Matemático",3),
                ("Literatura",2),("Razonamiento Verbal",3),("Anatomía",2),("Biología",2),("Química",2),
                ("Física Elemental",2),("Historia y Geografía",2),("Economía",2),("Inglés",1),
                ("Educación Física",2),("Tutoría",1)],
            5: [("Álgebra",3),("Geometría",2),("Trigonometría",1),("Razonamiento Matemático",3),
                ("Literatura",2),("Razonamiento Verbal",3),("Anatomía",2),("Biología",3),("Química",3),
                ("Física Elemental",3),("Historia y Geografía",2),("Economía",2),("Tutoría",1)]
        }

        grados = {}
        for num, plan in grados_plan.items():
            g = Grado(numero=num)
            s.add(g)
            s.commit()
            s.refresh(g)
            grados[num] = g
            
            # Plan de Estudio
            for curso_nombre, horas in plan:
                s.add(PlanEstudio(id_grado=g.id_grado, id_curso=cursos[curso_nombre].id_curso, horas_semanales=horas))
            
            # GradoDiaConfig: 6 bloques cada día
            for dia in dias:
                s.add(GradoDiaConfig(id_grado=g.id_grado, id_dia=dia.id_dia, bloques_dia=6))
        
        s.commit()

        # --- Profesores (25 del JSON) ---
        profes_data = [
            ("Juan Perez", ["Aritmética","Geometría","Trigonometría","Razonamiento Matemático"]),
            ("Maria Lopez", ["Literatura","Razonamiento Verbal"]),
            ("Carlos Rios", ["Anatomía","Biología","Química","Física Elemental"]),
            ("Ana Torres", ["Historia y Geografía","Economía"]),
            ("Luis Mendoza", ["Filosofía","DPCC"]),
            ("Sofia Vargas", ["Inglés"]),
            ("Roberto Chavez", ["Educación Física"]),
            ("Carmen Diaz", ["Tutoría"]),
            ("Jorge Ramirez", ["Álgebra","Aritmética"]),
            ("Patricia Flores", ["Geometría","Trigonometría"]),
            ("Andres Castillo", ["Razonamiento Matemático","Álgebra"]),
            ("Valeria Gutierrez", ["Literatura","Razonamiento Verbal"]),
            ("Ricardo Morales", ["Literatura","Razonamiento Verbal"]),
            ("Claudia Herrera", ["Anatomía","Biología"]),
            ("Miguel Sanchez", ["Química","Física Elemental"]),
            ("Daniela Vega", ["Anatomía","Química"]),
            ("Fernando Paredes", ["Historia y Geografía","Economía"]),
            ("Gabriela Quispe", ["Filosofía","DPCC"]),
            ("Eduardo Mamani", ["Historia y Geografía","Filosofía"]),
            ("Lucia Condori", ["Inglés"]),
            ("Kevin Soto", ["Inglés"]),
            ("Diana Pinto", ["Educación Física"]),
            ("Hector Medina", ["Educación Física"]),
            ("Silvia Ramos", ["Tutoría"]),
            ("Oscar Huanca", ["Tutoría"]),
        ]
        
        profesores = {}
        for nombre, cursos_lista in profes_data:
            p = Profesores(id_sede=sede_a.id_sede, nombre_profesor=nombre, max_horas_dia=6)
            s.add(p)
            s.commit()
            s.refresh(p)
            profesores[nombre] = p
            for curso_nombre in cursos_lista:
                s.add(ProfesorCurso(id_profesor=p.id_profesores, id_curso=cursos[curso_nombre].id_curso))
        s.commit()

        # --- Secciones (14 del JSON) ---
        # (nombre, grado_num, sede, turno_disponible)
        secciones_data = [
            ("1° A", 1, sede_a, t_man), ("1° B", 1, sede_a, t_man),
            ("2° A", 2, sede_a, t_man), ("2° B", 2, sede_a, t_man),
            ("3°",   3, sede_a, t_man),
            ("4°",   4, sede_a, t_tar),
            ("5° A", 5, sede_a, t_tar), ("5° B", 5, sede_a, t_tar),
            ("1° A", 1, sede_b, t_man), ("1° B", 1, sede_b, t_man),
            ("2°",   2, sede_b, t_man),
            ("3°",   3, sede_b, t_man),
            ("4°",   4, sede_b, t_man),
            ("5°",   5, sede_b, t_man),
        ]
        
        for nombre, grado_num, sede, turno in secciones_data:
            sec = Seccion(id_sede=sede.id_sede, id_grado=grados[grado_num].id_grado, nombre=nombre)
            s.add(sec)
            s.commit()
            s.refresh(sec)
            # SeccionTurno: disponibilidad por día
            for dia in dias:
                s.add(SeccionTurno(id_seccion=sec.id_seccion, id_turno=turno.id_turno, id_dia=dia.id_dia))
        
        s.commit()
        print("=== ¡BD Poblada Exitosamente con datos de referencia! ===")

if __name__ == "__main__":
    poblar_bd()
