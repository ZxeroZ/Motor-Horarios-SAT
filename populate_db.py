"""Pobla la BD con datos idénticos al datos.json de referencia (v2 - con Sábado y Tutorías)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import (
    Colegio, Sedes, Grado, Dias, Turno, Bloque, Areas, 
    Cursos, Profesores, ProfesorCurso, Seccion, PlanEstudio,
    GradoDiaConfig, SeccionTurno, Usuario, Tutoria
)
from datetime import time as pytime

def poblar_bd():
    create_db_and_tables()
    with Session(engine) as s:
        if s.exec(select(Cursos)).first():
            print("La BD ya tiene datos. Borra database.db primero.")
            return

        print("=== Poblando BD v2 (Sábado + Tutorías) ===")

        # --- Admin ---
        s.add(Usuario(email="admin@colegio.com", nombre="Administrador"))

        # --- Colegio ---
        col = Colegio(nombre_colegio="Colegio Central")
        s.add(col); s.commit(); s.refresh(col)

        # --- Sedes ---
        sede_a = Sedes(id_colegio=col.id_colegio, nombre_sede="Sede A")
        sede_b = Sedes(id_colegio=col.id_colegio, nombre_sede="Sede B")
        s.add_all([sede_a, sede_b]); s.commit()
        s.refresh(sede_a); s.refresh(sede_b)

        # --- Días (ahora con Sábado) ---
        dias_nombres = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sábado"]
        dias = []
        for i, nombre in enumerate(dias_nombres):
            d = Dias(nombre_dia=nombre, orden=i+1)
            s.add(d); dias.append(d)
        s.commit()
        for d in dias: s.refresh(d)
        dia_map = {d.nombre_dia: d for d in dias}

        # --- Turnos ---
        t_man = Turno(nombre="Mañana")
        t_tar = Turno(nombre="Tarde")
        s.add_all([t_man, t_tar]); s.commit()
        s.refresh(t_man); s.refresh(t_tar)

        # --- Bloques (6 por turno) ---
        for i in range(1, 7):
            s.add(Bloque(id_turno=t_man.id_turno, numero_bloque=i, hora_inicio=pytime(7+i,0), hora_final=pytime(8+i,0)))
            s.add(Bloque(id_turno=t_tar.id_turno, numero_bloque=i, hora_inicio=pytime(13+i,0), hora_final=pytime(14+i,0)))
        s.commit()

        # --- Áreas (7 categorías, incluyendo Tutoría) ---
        areas_data = [
            ("Matemática", 4), ("Comunicación", 4), ("Ciencia y Tecnología", 4),
            ("Ciencias Sociales", 4), ("Idiomas", 4), ("Educación Física", 4),
            ("Tutoría", 4)
        ]
        areas = {}
        for nombre, max_h in areas_data:
            a = Areas(nombre=nombre, max_horas_dia=max_h)
            s.add(a); s.commit(); s.refresh(a)
            areas[nombre] = a

        # --- Cursos (18, incluyendo Tutoría) ---
        cursos_data = [
            ("Álgebra", "Matemática"), ("Aritmética", "Matemática"),
            ("Geometría", "Matemática"), ("Trigonometría", "Matemática"),
            ("Razonamiento Matemático", "Matemática"),
            ("Literatura", "Comunicación"), ("Razonamiento Verbal", "Comunicación"),
            ("Anatomía", "Ciencia y Tecnología"), ("Biología", "Ciencia y Tecnología"),
            ("Química", "Ciencia y Tecnología"), ("Física Elemental", "Ciencia y Tecnología"),
            ("Historia y Geografía", "Ciencias Sociales"), ("Economía", "Ciencias Sociales"),
            ("Filosofía", "Ciencias Sociales"), ("DPCC", "Ciencias Sociales"),
            ("Inglés", "Idiomas"), ("Educación Física", "Educación Física"),
            ("Tutoría", "Tutoría")
        ]
        cursos = {}
        for nombre, area_nombre in cursos_data:
            c = Cursos(nombre_curso=nombre, id_area=areas[area_nombre].id_area)
            s.add(c); s.commit(); s.refresh(c)
            cursos[nombre] = c

        # --- Grados (5) ---
        grados = {}
        for n in range(1, 6):
            g = Grado(numero=n)
            s.add(g); s.commit(); s.refresh(g)
            grados[n] = g

        # --- Plan de Estudio (Malla Curricular) ---
        # Grados 1-3: misma malla (15 cursos, 30h L-V)
        malla_1_3 = [
            ("Álgebra",3), ("Aritmética",2), ("Geometría",2), ("Trigonometría",1),
            ("Razonamiento Matemático",2), ("Literatura",2), ("Razonamiento Verbal",3),
            ("Biología",2), ("Química",2), ("Física Elemental",2),
            ("Historia y Geografía",2), ("DPCC",2), ("Inglés",2),
            ("Educación Física",2), ("Tutoría",1)
        ]
        for n in [1,2,3]:
            for nombre_c, horas in malla_1_3:
                s.add(PlanEstudio(id_grado=grados[n].id_grado, id_curso=cursos[nombre_c].id_curso, horas_semanales=horas))
        
        # Grado 4: 17 cursos, 33h (L-S)
        malla_4 = [
            ("Álgebra",3), ("Aritmética",2), ("Geometría",2), ("Trigonometría",1),
            ("Razonamiento Matemático",2), ("Literatura",2), ("Razonamiento Verbal",3),
            ("Anatomía",2), ("Biología",2), ("Química",2), ("Física Elemental",2),
            ("Historia y Geografía",2), ("Economía",2), ("DPCC",2),
            ("Tutoría",1), ("Inglés",1), ("Educación Física",1)
        ]
        for nombre_c, horas in malla_4:
            s.add(PlanEstudio(id_grado=grados[4].id_grado, id_curso=cursos[nombre_c].id_curso, horas_semanales=horas))

        # Grado 5: 15 cursos, 33h (L-S)
        malla_5 = [
            ("Álgebra",3), ("Geometría",2), ("Trigonometría",1),
            ("Razonamiento Matemático",3), ("Literatura",2), ("Razonamiento Verbal",3),
            ("Anatomía",2), ("Biología",3), ("Química",3), ("Física Elemental",3),
            ("Historia y Geografía",2), ("Economía",2),
            ("Tutoría",1), ("Filosofía",2), ("Inglés",1)
        ]
        for nombre_c, horas in malla_5:
            s.add(PlanEstudio(id_grado=grados[5].id_grado, id_curso=cursos[nombre_c].id_curso, horas_semanales=horas))
        s.commit()

        # --- GradoDiaConfig ---
        # Grados 1-3: L-V con 6 slots
        for n in [1,2,3]:
            for dia_nombre in ["Lunes","Martes","Miercoles","Jueves","Viernes"]:
                s.add(GradoDiaConfig(id_grado=grados[n].id_grado, id_dia=dia_map[dia_nombre].id_dia, bloques_dia=6))
        # Grados 4-5: L-S con 6 slots
        for n in [4,5]:
            for dia_nombre in ["Lunes","Martes","Miercoles","Jueves","Viernes","Sábado"]:
                s.add(GradoDiaConfig(id_grado=grados[n].id_grado, id_dia=dia_map[dia_nombre].id_dia, bloques_dia=6))
        s.commit()

        # --- Profesores (25) ---
        profes_data = [
            ("Juan Perez", sede_a, ["Aritmética","Geometría","Trigonometría","Razonamiento Matemático"]),
            ("Maria Lopez", sede_a, ["Literatura","Razonamiento Verbal"]),
            ("Carlos Rios", sede_a, ["Anatomía","Biología","Química","Física Elemental"]),
            ("Ana Torres", sede_a, ["Historia y Geografía","Economía"]),
            ("Luis Mendoza", sede_b, ["Filosofía","DPCC"]),
            ("Sofia Vargas", sede_b, ["Inglés"]),
            ("Roberto Chavez", sede_a, ["Educación Física"]),
            ("Carmen Diaz", sede_a, ["Álgebra","Geometría"]),
            ("Jorge Ramirez", sede_a, ["Álgebra","Aritmética"]),
            ("Patricia Flores", sede_a, ["Geometría","Trigonometría"]),
            ("Andres Castillo", sede_a, ["Razonamiento Matemático","Álgebra"]),
            ("Valeria Gutierrez", sede_a, ["Literatura","Razonamiento Verbal"]),
            ("Ricardo Morales", sede_b, ["Literatura","Razonamiento Verbal"]),
            ("Claudia Herrera", sede_b, ["Anatomía","Biología"]),
            ("Miguel Sanchez", sede_b, ["Química","Física Elemental"]),
            ("Daniela Vega", sede_b, ["Anatomía","Química"]),
            ("Fernando Paredes", sede_b, ["Historia y Geografía","Economía"]),
            ("Gabriela Quispe", sede_b, ["Filosofía","DPCC"]),
            ("Eduardo Mamani", sede_b, ["Historia y Geografía","Filosofía"]),
            ("Lucia Condori", sede_b, ["Inglés"]),
            ("Kevin Soto", sede_a, ["Inglés"]),
            ("Diana Pinto", sede_a, ["Educación Física"]),
            ("Hector Medina", sede_b, ["Educación Física"]),
            ("Silvia Ramos", sede_a, ["Razonamiento Verbal"]),
            ("Oscar Huanca", sede_b, ["Razonamiento Matemático","Álgebra"]),
        ]
        profes = {}
        for nombre, sede, _ in profes_data:
            p = Profesores(nombre_profesor=nombre, id_sede=sede.id_sede)
            s.add(p); s.commit(); s.refresh(p)
            profes[nombre] = p

        # --- ProfesorCurso ---
        for nombre, _, cursos_list in profes_data:
            for curso_nombre in cursos_list:
                s.add(ProfesorCurso(id_profesor=profes[nombre].id_profesores, id_curso=cursos[curso_nombre].id_curso))
        s.commit()

        # --- Secciones (14) ---
        secciones_data = [
            # Sede A
            ("1° A", 1, sede_a, t_man), ("1° B", 1, sede_a, t_man),
            ("2° A", 2, sede_a, t_man), ("2° B", 2, sede_a, t_man),
            ("3°",   3, sede_a, t_man),
            ("4°",   4, sede_a, t_tar),
            ("5° A", 5, sede_a, t_tar), ("5° B", 5, sede_a, t_tar),
            # Sede B
            ("1° A", 1, sede_b, t_man), ("1° B", 1, sede_b, t_man),
            ("2°",   2, sede_b, t_man),
            ("3°",   3, sede_b, t_man),
            ("4°",   4, sede_b, t_man),
            ("5°",   5, sede_b, t_man),
        ]
        
        secciones = {}
        for nombre, grado_n, sede, turno in secciones_data:
            sec = Seccion(id_sede=sede.id_sede, id_grado=grados[grado_n].id_grado, nombre=nombre)
            s.add(sec); s.commit(); s.refresh(sec)
            key = f"{sede.nombre_sede}_{nombre}"
            secciones[key] = sec
            
            # SeccionTurno: todos los días que el grado tiene
            if grado_n in [4, 5]:
                dias_sec = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sábado"]
            else:
                dias_sec = ["Lunes","Martes","Miercoles","Jueves","Viernes"]
            
            for dia_nombre in dias_sec:
                s.add(SeccionTurno(id_seccion=sec.id_seccion, id_turno=turno.id_turno, id_dia=dia_map[dia_nombre].id_dia))
            s.commit()

        # --- Tutorías (cada sección tiene un tutor asignado) ---
        tutorias_map = {
            "Sede A_1° A": "Juan Perez", "Sede A_1° B": "Juan Perez",
            "Sede A_2° A": "Maria Lopez", "Sede A_2° B": "Maria Lopez",
            "Sede A_3°": "Carlos Rios", "Sede A_4°": "Carlos Rios",
            "Sede A_5° A": "Ana Torres", "Sede A_5° B": "Ana Torres",
            "Sede B_1° A": "Luis Mendoza", "Sede B_1° B": "Luis Mendoza",
            "Sede B_2°": "Sofia Vargas",
            "Sede B_3°": "Roberto Chavez",
            "Sede B_4°": "Carmen Diaz",
            "Sede B_5°": "Jorge Ramirez",
        }
        for sec_key, prof_nombre in tutorias_map.items():
            sec = secciones[sec_key]
            prof = profes[prof_nombre]
            s.add(Tutoria(id_seccion=sec.id_seccion, id_profesor=prof.id_profesores))
        s.commit()

        print("=== BD v2 Poblada Exitosamente (Sábado + Tutorías) ===")

if __name__ == "__main__":
    poblar_bd()
