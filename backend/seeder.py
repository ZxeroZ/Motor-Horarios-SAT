"""
Seeder legacy — DEPRECADO. Usar populate_db.py en su lugar.
Este archivo se mantiene por referencia pero usa el esquema actual de modelos.
"""
import json
import os
from datetime import time
from sqlmodel import Session
from backend.database import create_db_and_tables, engine
from backend.models import (
    Colegio, Sedes, Usuario, Areas, Cursos, Grado, Seccion, 
    PlanEstudio, Dias, Turno, Bloque, GradoDiaConfig,
    Profesores, ProfesorCurso, ProfesorSedes
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
        print("1. Creando Colegio y Sedes...")
        colegio = Colegio(nombre_colegio="Colegio San Ignacio (Demo)")
        session.add(colegio)
        session.commit()
        session.refresh(colegio)

        sedes_db = {}
        for nombre_sede in datos["configuracion"]["sedes"]:
            s = Sedes(nombre_sede=nombre_sede, id_colegio=colegio.id_colegio)
            session.add(s)
            session.commit()
            session.refresh(s)
            sedes_db[nombre_sede] = s

        print("2. Creando Turnos...")
        turnos_db = {}
        for nombre_turno in datos["configuracion"]["turnos"]:
            t = Turno(nombre=nombre_turno)
            session.add(t)
            session.commit()
            session.refresh(t)
            turnos_db[nombre_turno] = t

        print("3. Creando Días...")
        dias_db = {}
        dias_nombres = set()
        for g in datos.get("grados", []):
            dias_nombres.update(g.get("horario_plantilla", {}).keys())
        for idx, nombre_dia in enumerate(sorted(dias_nombres)):
            d = Dias(nombre_dia=nombre_dia, orden=idx+1)
            session.add(d)
            session.commit()
            session.refresh(d)
            dias_db[nombre_dia] = d

        print("4. Creando Bloques (visual)...")
        max_slots = max(
            slots for g in datos.get("grados", []) 
            for slots in g.get("horario_plantilla", {}).values()
        )
        for t_nombre, t_obj in turnos_db.items():
            for i in range(1, max_slots + 1):
                b = Bloque(
                    id_turno=t_obj.id_turno,
                    numero_bloque=i,
                    hora_inicio=time(7 + i, 0),
                    hora_final=time(8 + i, 0)
                )
                session.add(b)
        session.commit()

        print("5. Creando Áreas y Cursos...")
        areas_db = {}
        for cat in datos["categorias"]:
            a = Areas(nombre=cat["nombre"], max_horas_dia=cat["max_horas_dia"])
            session.add(a)
            session.commit()
            session.refresh(a)
            areas_db[cat["id"]] = a

        cursos_db = {}
        for c in datos["cursos"]:
            area_obj = areas_db.get(c["categoria_id"])
            if area_obj:
                curso_obj = Cursos(nombre_curso=c["nombre"], id_area=area_obj.id_area)
                session.add(curso_obj)
                session.commit()
                session.refresh(curso_obj)
                cursos_db[c["id"]] = curso_obj

        print("6. Creando Grados y Plan de Estudio...")
        grados_db = {}
        for g in datos["grados"]:
            grado_obj = Grado(numero=int(g["nombre"].replace("°", "")))
            session.add(grado_obj)
            session.commit()
            session.refresh(grado_obj)
            grados_db[g["id"]] = grado_obj
            
            # GradoDiaConfig
            for dia_nombre, bloques in g.get("horario_plantilla", {}).items():
                if dia_nombre in dias_db:
                    session.add(GradoDiaConfig(
                        id_grado=grado_obj.id_grado,
                        id_dia=dias_db[dia_nombre].id_dia,
                        bloques_dia=bloques
                    ))
            
            # Plan de Estudio
            for req in g.get("cursos_requeridos", []):
                c_obj = cursos_db.get(req["curso_id"])
                if c_obj:
                    session.add(PlanEstudio(
                        id_grado=grado_obj.id_grado,
                        id_curso=c_obj.id_curso,
                        horas_semanales=req["horas_semanales"]
                    ))
            session.commit()

        print("7. Creando Profesores...")
        for p in datos["profesores"]:
            prof_obj = Profesores(nombre_profesor=p["nombre"])
            session.add(prof_obj)
            session.commit()
            session.refresh(prof_obj)
            
            # ProfesorSedes (inferir sede de disponibilidad)
            sedes_asignadas = set()
            for dia_data in p.get("disponibilidad", {}).values():
                for turno_data in dia_data.values():
                    if isinstance(turno_data, dict):
                        sedes_asignadas.update(turno_data.keys())
            for sede_nombre in sedes_asignadas:
                if sede_nombre in sedes_db:
                    session.add(ProfesorSedes(
                        id_profesor=prof_obj.id_profesor,
                        id_sede=sedes_db[sede_nombre].id_sede
                    ))
            
            # ProfesorCurso
            for c_id in p.get("cursos_habilitados", []):
                c_obj = cursos_db.get(c_id)
                if c_obj:
                    session.add(ProfesorCurso(
                        id_profesor=prof_obj.id_profesor, 
                        id_curso=c_obj.id_curso
                    ))
            
        session.commit()
        print("¡Base de datos poblada exitosamente desde datos.json!")

if __name__ == "__main__":
    run_seeder()
