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

    # Mapeos básicos para acceso O(1)
    profesores_dict = {p["id"]: p for p in profesores_lista}
    secciones_dict = {s["id"]: s for s in secciones_lista}

    # 1. Profesores requeridos/habilitados por curso
    # curso_id -> lista de profesor_id
    profesores_por_curso = {c_id: [] for c_id in cursos.keys()}
    for p in profesores_lista:
        p_id = p["id"]
        for c_id in p.get("cursos_habilitados", []):
            if c_id in profesores_por_curso:
                profesores_por_curso[c_id].append(p_id)

    # 2. Requerimientos de clases por sección
    # seccion_id -> {curso_id: horas_semanales}
    requerimientos_seccion = {}
    for sec in secciones_lista:
        s_id = sec["id"]
        grado = grados.get(sec["grado"], {})
        reqs = {}
        for req in grado.get("cursos_requeridos", []):
            reqs[req["curso_id"]] = req["horas_semanales"]
        requerimientos_seccion[s_id] = reqs

    # 3. Transformar disponibilidades a un formato de acceso rápido: set de tuplas (dia, turno)
    # disp_seccion[seccion_id] = {(dia1, turno1), (dia1, turno2), ...}
    disp_seccion = {}
    for sec in secciones_lista:
        s_disp = set()
        for dia, turnos in sec.get("disponibilidad", {}).items():
            for t in turnos:
                s_disp.add((dia, t))
        disp_seccion[sec["id"]] = s_disp

    disp_profesor = {}
    for p in profesores_lista:
        p_disp = set()
        for dia, turnos in p.get("disponibilidad", {}).items():
            for t in turnos:
                p_disp.add((dia, t))
        disp_profesor[p["id"]] = p_disp

    # Estructura final consolidada lista para instanciar variables en CP-SAT
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
    }
