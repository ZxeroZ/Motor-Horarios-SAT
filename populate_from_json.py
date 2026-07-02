import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import (
    Colegio, Sedes, Grado, Dias, Turno, Bloque, Areas, 
    Cursos, Profesores, ProfesorCurso, Seccion, PlanEstudio,
    GradoDiaConfig, SeccionTurno, Usuario, Tutoria, 
    SedeProfesor, ProfesorDisponibilidad, ProfesorPreferencia,
    GradoProfesor, BloqueReservado, BloqueGrado, BloqueOpcion, BloqueOpcionSlot
)
from datetime import time as pytime

def poblar_desde_json():
    create_db_and_tables()
    with open("data/input/datos.json", encoding="utf-8") as f:
        datos = json.load(f)

    with Session(engine) as s:
        if s.exec(select(Cursos)).first():
            print("La BD ya tiene datos. Borra database.db primero.")
            return

        print("=== Poblando BD desde datos.json ===")

        # --- Admin ---
        s.add(Usuario(email="admin@colegio.com", nombre="Administrador"))

        # --- Colegio ---
        col = Colegio(nombre_colegio="Colegio Central")
        s.add(col)
        s.commit()
        s.refresh(col)

        # --- Sedes ---
        sedes_nombres = datos.get("configuracion", {}).get("sedes", [])
        sedes_map = {}
        for nombre in sedes_nombres:
            sede = Sedes(id_colegio=col.id_colegio, nombre_sede=nombre)
            s.add(sede)
            s.commit()
            s.refresh(sede)
            sedes_map[nombre] = sede

        # --- Turnos y Bloques ---
        turnos_nombres = datos.get("configuracion", {}).get("turnos", [])
        turnos_map = {}
        for nombre in turnos_nombres:
            t = Turno(nombre=nombre)
            s.add(t)
            s.commit()
            s.refresh(t)
            turnos_map[nombre] = t
            
            # Generar bloques visuales genéricos
            for i in range(1, 13):
                b = Bloque(id_turno=t.id_turno, numero_bloque=i, hora_inicio=pytime(8, 0), hora_fin=pytime(8, 45))
                s.add(b)
            s.commit()

        # --- Días ---
        dias_nombres = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dias_map = {}
        for i, nombre in enumerate(dias_nombres):
            d = Dias(nombre_dia=nombre, orden=i+1)
            s.add(d)
            s.commit()
            s.refresh(d)
            dias_map[nombre] = d

        # --- Categorias (Areas) ---
        areas_map = {}
        for cat in datos.get("categorias", []):
            a = Areas(nombre=cat["nombre"], max_horas_dia=cat.get("max_horas_dia", 4))
            s.add(a)
            s.commit()
            s.refresh(a)
            areas_map[cat["id"]] = a

        # --- Cursos ---
        cursos_map = {}
        for cur in datos.get("cursos", []):
            area = areas_map.get(cur["categoria_id"])
            if area:
                # Hack for Tutoría to avoid encoding mismatches
                nombre_cur = "Tutoría" if "tutor" in cur["nombre"].lower() else cur["nombre"]
                requiere_espacio = cur.get("requiere_espacio_unico", False)
                curso = Cursos(nombre_curso=nombre_cur, id_area=area.id_area, requiere_espacio_unico=requiere_espacio)
                s.add(curso)
                s.commit()
                s.refresh(curso)
                cursos_map[cur["id"]] = curso

        # --- Grados & PlanEstudio & GradoDiaConfig ---
        grados_map = {}
        for g in datos.get("grados", []):
            numero_grado = int(g["nombre"].replace("°", "").strip()) if "°" in g["nombre"] else 0
            grado = Grado(numero=numero_grado)
            s.add(grado)
            s.commit()
            s.refresh(grado)
            grados_map[g["id"]] = grado

            for req in g.get("cursos_requeridos", []):
                curso = cursos_map.get(req["curso_id"])
                if curso:
                    s.add(PlanEstudio(id_grado=grado.id_grado, id_curso=curso.id_curso, horas_semanales=req["horas_semanales"]))
            
            for dia_nombre, bloques in g.get("horario_plantilla", {}).items():
                dia = dias_map.get(dia_nombre)
                if dia:
                    s.add(GradoDiaConfig(id_grado=grado.id_grado, id_dia=dia.id_dia, bloques_dia=bloques))
        s.commit()

        # --- Secciones & SeccionTurno ---
        secciones_map = {}
        for sec in datos.get("secciones", []):
            grado = grados_map.get(sec["grado"])
            sede = sedes_map.get(sec["sede"])
            if grado and sede:
                seccion = Seccion(id_sede=sede.id_sede, id_grado=grado.id_grado, nombre=sec["nombre"])
                s.add(seccion)
                s.commit()
                s.refresh(seccion)
                secciones_map[sec["id"]] = seccion

                for dia_nombre, turnos in sec.get("disponibilidad", {}).items():
                    dia = dias_map.get(dia_nombre)
                    if dia:
                        for turno_nombre in turnos:
                            turno = turnos_map.get(turno_nombre)
                            if turno:
                                s.add(SeccionTurno(id_seccion=seccion.id_seccion, id_turno=turno.id_turno, id_dia=dia.id_dia))
        s.commit()

        # --- Profesores, ProfesorCurso, SedeProfesor, ProfesorDisponibilidad ---
        profes_map = {}
        for p in datos.get("profesores", []):
            prof = Profesores(nombre_profesor=p["nombre"], horas_minimas=p.get("horas_minimas", 6))
            s.add(prof)
            s.commit()
            s.refresh(prof)
            profes_map[p["id"]] = prof
            
            for c_id in p.get("cursos_habilitados", []):
                curso = cursos_map.get(c_id)
                if curso:
                    s.add(ProfesorCurso(id_profesor=prof.id_profesor, id_curso=curso.id_curso))
            
            sedes_agregadas = set()
            disp = p.get("disponibilidad", {})
            for dia_nombre, turnos_dict in disp.items():
                dia = dias_map.get(dia_nombre)
                if not dia: continue
                if isinstance(turnos_dict, list):
                    continue
                for turno_nombre, sedes_dict in turnos_dict.items():
                    turno = turnos_map.get(turno_nombre)
                    if not turno: continue
                    if isinstance(sedes_dict, list):
                        continue
                    for sede_nombre, bloques in sedes_dict.items():
                        sede = sedes_map.get(sede_nombre)
                        if sede:
                            sedes_agregadas.add(sede.id_sede)
                            for b in bloques:
                                s.add(ProfesorDisponibilidad(
                                    id_profesor=prof.id_profesor,
                                    id_dia=dia.id_dia,
                                    id_turno=turno.id_turno,
                                    id_sede=sede.id_sede,
                                    nro_bloque=b
                                ))

            for s_id in sedes_agregadas:
                s.add(SedeProfesor(id_profesor=prof.id_profesor, id_sede=s_id))

            # GradoProfesor: vincular profesor con todos los grados disponibles
            grados_hab = p.get("grados_habilitados", [])
            if grados_hab:
                for g_id in grados_hab:
                    grado_obj = grados_map.get(g_id)
                    if grado_obj:
                        s.add(GradoProfesor(id_profesor=prof.id_profesor, id_grado=grado_obj.id_grado))
            else:
                # Fallback: habilitar para todos los grados
                for g_obj in grados_map.values():
                    s.add(GradoProfesor(id_profesor=prof.id_profesor, id_grado=g_obj.id_grado))

        s.commit()

        # --- Tutorias ---
        tutorias = datos.get("tutorias", {})
        for sec_id, prof_id in tutorias.items():
            seccion = secciones_map.get(sec_id)
            prof = profes_map.get(prof_id)
            if seccion and prof:
                s.add(Tutoria(id_seccion=seccion.id_seccion, id_profesor=prof.id_profesor))
        s.commit()

        # --- Bloques Reservados ---
        reservas = datos.get("bloques_reservados", [])
        for r in reservas:
            sede = sedes_map.get(r.get("sede"))
            dia = dias_map.get(r.get("dia"))
            turno = turnos_map.get(r.get("turno"))
            
            if not (sede and dia and turno): continue
            
            reserva_obj = BloqueReservado(id_sede=sede.id_sede, id_dia=dia.id_dia, id_turno=turno.id_turno)
            s.add(reserva_obj)
            s.commit()
            s.refresh(reserva_obj)
            
            for g_id in r.get("grados_afectados", []):
                grado = grados_map.get(g_id)
                if grado:
                    s.add(BloqueGrado(id_bloque_reservado=reserva_obj.id_bloque_reservado, id_grado=grado.id_grado))
            
            for idx, options in enumerate(r.get("opciones_slots", [])):
                opcion_obj = BloqueOpcion(id_bloque_reservado=reserva_obj.id_bloque_reservado, nro_opcion=idx + 1)
                s.add(opcion_obj)
                s.commit()
                s.refresh(opcion_obj)
                
                for slot_nro in options:
                    s.add(BloqueOpcionSlot(id_bloque_opcion=opcion_obj.id_bloque_opcion, nro_bloque=slot_nro))
            s.commit()

        print("=== BD Poblada desde JSON Exitosamente ===")

if __name__ == "__main__":
    poblar_desde_json()
