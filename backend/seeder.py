import json
import os
from datetime import time
from sqlmodel import Session
from backend.database import create_db_and_tables, engine
from backend.models import (
    Colegio, Sede, Usuario, Area, Curso, Grado, Seccion, 
    PlanEstudio, Configuracion, Dia, DiaGrado, Bloque, 
    Profesor, ProfesorCurso
)

def run_seeder():
    # Crear tablas si no existen
    create_db_and_tables()

    # Cargar archivo JSON
    json_path = os.path.join("data", "input", "datos.json")
    if not os.path.exists(json_path):
        print(f"Error: No se encontró el archivo {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        datos = json.load(f)

    with Session(engine) as session:
        # Purgue de prueba (opcional, aquí asumimos BD limpia)

        print("1. Creando Colegio y Sedes...")
        colegio = Colegio(nombre="Colegio San Ignacio (Demo)")
        session.add(colegio)
        session.commit()
        session.refresh(colegio)

        sedes_db = {}
        for nombre_sede in datos["configuracion"]["sedes"]:
            s = Sede(nombre_sede=nombre_sede, id_colegio=colegio.id_colegio)
            session.add(s)
            session.commit()
            session.refresh(s)
            sedes_db[nombre_sede] = s

        print("2. Creando Configuración Global...")
        conf = Configuracion(
            nombre_turno="Jornada Completa",
            hora_inicio=time(8, 0),
            hora_final=time(14, 0),
            duracion_bloque=45 
        )
        session.add(conf)
        session.commit()

        print("3. Creando Días y Bloques (Slots)...")
        # Días
        dias_db = {}
        for idx, nombre_dia in enumerate(datos["configuracion"]["dias"]):
            d = Dia(nombre_dia=nombre_dia, orden=idx+1)
            session.add(d)
            session.commit()
            session.refresh(d)
            dias_db[nombre_dia] = d

        # Bloques basados en turnos y slots_por_turno
        slots = datos["configuracion"]["slots_por_turno"]
        for turno in datos["configuracion"]["turnos"]:
            for i in range(slots):
                # Pseudo-horas
                b = Bloque(
                    id_turno=conf.id_configuracion,
                    nombre_bloque=f"{turno} - Slot {i+1}",
                    hora_inicio=time(8 + i, 0),
                    hora_final=time(8 + i, 45)
                )
                session.add(b)
        session.commit()

        print("4. Creando Áreas y Cursos...")
        areas_db = {}
        for cat in datos["categorias"]:
            # El id en el json es string, en la BD es autoincrement pero mapeamos el nombre
            a = Area(nombre_area=cat["nombre"], max_horas_dia=cat["max_horas_dia"])
            session.add(a)
            session.commit()
            session.refresh(a)
            areas_db[cat["id"]] = a

        cursos_db = {}
        for c in datos["cursos"]:
            area_obj = areas_db.get(c["categoria_id"])
            if area_obj:
                curso_obj = Curso(nombre_curso=c["nombre"], id_area=area_obj.id_area)
                session.add(curso_obj)
                session.commit()
                session.refresh(curso_obj)
                cursos_db[c["id"]] = curso_obj

        print("5. Creando Grados, Secciones y Plan de Estudio...")
        for g in datos["grados"]:
            grado_obj = Grado(numero=int(g["nombre"].replace("°", "")), nombre_grado=g["nombre"])
            session.add(grado_obj)
            session.commit()
            session.refresh(grado_obj)
            
            # Crear algunas secciones dummy para este grado en la Sede A por defecto
            for letra in ["A", "B"]:
                sec = Seccion(letra=letra, id_grado=grado_obj.id_grado, id_sede=sedes_db["Sede A"].id_sede)
                session.add(sec)
            
            # Plan de Estudio
            for req in g.get("cursos_requeridos", []):
                c_obj = cursos_db.get(req["curso_id"])
                if c_obj:
                    plan = PlanEstudio(
                        id_grado=grado_obj.id_grado,
                        id_curso=c_obj.id_curso,
                        horas_semanales=req["horas_semanales"]
                    )
                    session.add(plan)
            session.commit()

        print("6. Creando Profesores...")
        for p in datos["profesores"]:
            prof_obj = Profesor(
                nombre_profesor=p["nombre"], 
                max_horas_dia=p.get("max_horas_dia", 6),
                id_sede=sedes_db["Sede A"].id_sede # Default
            )
            session.add(prof_obj)
            session.commit()
            session.refresh(prof_obj)
            
            # Profesor - Curso
            for c_id in p.get("cursos_habilitados", []):
                c_obj = cursos_db.get(c_id)
                if c_obj:
                    pc = ProfesorCurso(id_profesor=prof_obj.id_profesor, id_curso=c_obj.id_curso)
                    session.add(pc)
            
            # Mapear 'disponibilidad' a 'Restricciones' es opcional en el seeder básico,
            # pero ya guardamos los cursos que habilitan al engine.
            
        session.commit()
        print("¡Base de datos migrada exitosamente desde datos.json!")

if __name__ == "__main__":
    run_seeder()
