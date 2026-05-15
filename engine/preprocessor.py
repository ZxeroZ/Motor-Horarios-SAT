def preprocesar(datos: dict) -> dict:
    """
    Transforma los datos validados en estructuras de búsqueda O(1) 
    y precalcula combinaciones viables para inicializar variables
    en CP-SAT con el menor costo posible.
    """
    grados = {g["id"]: g for g in datos.get("grados", [])}
    cursos = {c["id"]: c for c in datos.get("cursos", [])}
    categorias = {c["id"]: c for c in datos.get("categorias", [])}
    profesores_lista = datos.get("profesores", [])
    secciones_lista = datos.get("secciones", [])
    configuracion = datos.get("configuracion", {})
    tutorias = datos.get("tutorias", {})

    # Lookup maps para resolver IDs a nombres (nuevo formato de disponibilidad)
    dia_id_to_nombre = configuracion.get("dia_id_to_nombre", {})
    turno_id_to_nombre = configuracion.get("turno_id_to_nombre", {})

    # Mapeos básicos para acceso O(1)
    profesores_dict = {p["id"]: p for p in profesores_lista}
    
    secciones_dict = {}
    for s in secciones_lista:
        s_copia = dict(s)
        grado_id = s_copia.get("grado")
        s_copia["horario_plantilla"] = grados.get(grado_id, {}).get("horario_plantilla", {})
        secciones_dict[s_copia["id"]] = s_copia

    # 1. Profesores requeridos/habilitados por curso
    profesores_por_curso = {c_id: [] for c_id in cursos.keys()}
    for p in profesores_lista:
        p_id = p["id"]
        for c_id in p.get("cursos_habilitados", []):
            if c_id in profesores_por_curso:
                profesores_por_curso[c_id].append(p_id)

    # 2. Requerimientos de clases por sección
    requerimientos_seccion = {}
    for sec in secciones_lista:
        s_id = sec["id"]
        grado = grados.get(sec["grado"], {})
        reqs = {}
        for req in grado.get("cursos_requeridos", []):
            reqs[req["curso_id"]] = req["horas_semanales"]
        requerimientos_seccion[s_id] = reqs

    # 3. Transformar disponibilidades a formato de acceso rápido: set de tuplas (dia, turno)
    disp_seccion = {}
    for sec in secciones_lista:
        s_disp = set()
        for dia, turnos in sec.get("disponibilidad", {}).items():
            for t in turnos:
                s_disp.add((dia, t))
        disp_seccion[sec["id"]] = s_disp

    disp_profesor = {}
    disp_profesor_slots = {}
    for p in profesores_lista:
        p_disp = set()
        p_disp_slots = {}
        disponibilidad = p.get("disponibilidad", {})
        
        if isinstance(disponibilidad, list):
            # Nuevo formato: lista de {id_dia, id_turno, nro_bloque}
            for slot in disponibilidad:
                dia_nombre = dia_id_to_nombre.get(slot["id_dia"], str(slot["id_dia"]))
                turno_nombre = turno_id_to_nombre.get(slot["id_turno"], str(slot["id_turno"]))
                nro = slot["nro_bloque"]
                p_disp.add((dia_nombre, turno_nombre))
                if (dia_nombre, turno_nombre) not in p_disp_slots:
                    p_disp_slots[(dia_nombre, turno_nombre)] = set()
                p_disp_slots[(dia_nombre, turno_nombre)].add(nro)
        elif isinstance(disponibilidad, dict):
            # Formato legacy dict
            for dia, turnos in disponibilidad.items():
                if isinstance(turnos, list):
                    for t in turnos:
                        p_disp.add((dia, t))
                        p_disp_slots[(dia, t)] = set([1, 2, 3, 4, 5, 6])
                elif isinstance(turnos, dict):
                    for t, slots in turnos.items():
                        p_disp.add((dia, t))
                        p_disp_slots[(dia, t)] = set(slots)

        disp_profesor[p["id"]] = p_disp
        disp_profesor_slots[p["id"]] = p_disp_slots

    return {
        "configuracion": configuracion,
        "cursos": cursos,
        "categorias": categorias,
        "profesores": profesores_dict,
        "secciones": secciones_dict,
        "profesores_por_curso": profesores_por_curso,
        "requerimientos_seccion": requerimientos_seccion,
        "disp_seccion": disp_seccion,
        "disp_profesor": disp_profesor,
        "disp_profesor_slots": disp_profesor_slots,
        "tutorias": tutorias,
    }
