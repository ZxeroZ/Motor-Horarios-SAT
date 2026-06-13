def preprocesar(datos: dict) -> dict:
    grados = {g["id"]: g for g in datos.get("grados", [])}
    cursos = {c["id"]: c for c in datos.get("cursos", [])}
    categorias = {c["id"]: c for c in datos.get("categorias", [])}
    profesores_lista = datos.get("profesores", [])
    secciones_lista = datos.get("secciones", [])
    configuracion = datos.get("configuracion", {})
    tutorias = datos.get("tutorias", {})

    # Mapeos básicos para acceso O(1)
    profesores_dict = {p["id"]: p for p in profesores_lista}
    
    secciones_dict = {}
    for s in secciones_lista:
        s_copia = dict(s)
        grado_id = s_copia.get("grado")
        # Inyectar horario_plantilla directo en la sección desde su grado
        s_copia["horario_plantilla"] = grados.get(grado_id, {}).get("horario_plantilla", {})
        secciones_dict[s_copia["id"]] = s_copia

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
    disp_profesor_slots = {}
    disp_profesor_pref_slots = {}
    for p in profesores_lista:
        p_disp = set()
        p_disp_slots = {}
        for dia, turnos in p.get("disponibilidad", {}).items():
            if isinstance(turnos, list):
                # Formato antiguo: "Mañana", "Tarde"
                for t in turnos:
                    p_disp.add((dia, t))
                    p_disp_slots[(dia, t)] = set([1, 2, 3, 4, 5, 6])
            elif isinstance(turnos, dict):
                for t, content in turnos.items():
                    p_disp.add((dia, t))
                    if isinstance(content, list):
                        # Formato antiguo matricial sin sede: {"Mañana": [1, 2, 3]}
                        p_disp_slots[(dia, t)] = set(content)
                    elif isinstance(content, dict):
                        # Formato nuevo matricial con sede: {"Mañana": {"Sede A": [1, 2], "Sede B": [3, 4]}}
                        for sede, slots in content.items():
                            p_disp_slots[(dia, t, sede)] = set(slots)
        disp_profesor[p["id"]] = p_disp
        disp_profesor_slots[p["id"]] = p_disp_slots

        # Procesar disponibilidad preferente
        p_disp_pref_slots = {}
        if "disponibilidad_preferente" in p:
            for dia, turnos in p["disponibilidad_preferente"].items():
                if isinstance(turnos, dict):
                    for t, content in turnos.items():
                        if isinstance(content, dict):
                            for sede, slots in content.items():
                                p_disp_pref_slots[(dia, t, sede)] = set(slots)
        disp_profesor_pref_slots[p["id"]] = p_disp_pref_slots

    # 4. Construcción de Reglas de Bloques Reservados
    bloques_reservados = datos.get("bloques_reservados", [])

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
        "disp_profesor_slots": disp_profesor_slots,
        "disp_profesor_pref_slots": disp_profesor_pref_slots,
        "tutorias": tutorias,
        "bloques_reservados": bloques_reservados,
    }
