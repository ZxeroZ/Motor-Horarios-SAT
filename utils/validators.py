"""
Validaciones de integridad del JSON de entrada.
 
Cada función valida un aspecto específico y retorna una lista de errores
encontrados. Una lista vacía significa que esa validación pasó correctamente.
 
El flujo recomendado es llamar a `validar_todo` desde el main o desde el
preprocessor antes de construir el modelo.
"""
 
 
def validar_categorias(categorias: list[dict]) -> list[str]:
    errores = []
 
    if len(categorias) == 0:
        errores.append("[categorias] La lista de categorías no puede estar vacía")
        return errores
 
    ids_vistos = set()
    for categoria in categorias:
        cid = categoria.get("id", "")
 
        if not cid:
            errores.append("[categorias] Se encontró una categoría sin campo 'id'")
            continue
 
        if cid in ids_vistos:
            errores.append(f"[categorias] ID duplicado: '{cid}'")
        ids_vistos.add(cid)
 
        if "nombre" not in categoria:
            errores.append(f"[categorias][{cid}] Falta el campo 'nombre'")
 
        if "max_horas_dia" not in categoria:
            errores.append(f"[categorias][{cid}] Falta el campo 'max_horas_dia'")
        else:
            max_horas = categoria["max_horas_dia"]
            if not isinstance(max_horas, int) or max_horas < 1:
                errores.append(
                    f"[categorias][{cid}] 'max_horas_dia' debe ser un entero mayor a 0, "
                    f"se recibió: {max_horas}"
                )
 
    return errores
 
 
def validar_configuracion(configuracion: dict) -> list[str]:
    errores = []
 
    for campo in ["sedes", "turnos"]:
        if campo not in configuracion:
            errores.append(f"[configuracion] Falta el campo obligatorio: '{campo}'")
 
    if "sedes" in configuracion and len(configuracion["sedes"]) == 0:
        errores.append("[configuracion] 'sedes' no puede estar vacío")
 
    if "turnos" in configuracion and len(configuracion["turnos"]) == 0:
        errores.append("[configuracion] 'turnos' no puede estar vacío")
 
    return errores
 
 
def validar_cursos(cursos: list[dict], ids_categorias: set[str]) -> list[str]:
    errores = []
 
    if len(cursos) == 0:
        errores.append("[cursos] La lista de cursos no puede estar vacía")
        return errores
 
    ids_vistos = set()
    for curso in cursos:
        cid = curso.get("id", "")
 
        if not cid:
            errores.append("[cursos] Se encontró un curso sin campo 'id'")
            continue
 
        if cid in ids_vistos:
            errores.append(f"[cursos] ID duplicado: '{cid}'")
        ids_vistos.add(cid)
 
        if "nombre" not in curso:
            errores.append(f"[cursos][{cid}] Falta el campo 'nombre'")
 
        if "categoria_id" not in curso:
            errores.append(f"[cursos][{cid}] Falta el campo 'categoria_id'")
        elif curso["categoria_id"] not in ids_categorias:
            errores.append(
                f"[cursos][{cid}] La categoría '{curso['categoria_id']}' "
                f"no existe en la lista de categorías"
            )

        if "requiere_espacio_unico" in curso:
            if not isinstance(curso["requiere_espacio_unico"], bool):
                errores.append(f"[cursos][{cid}] 'requiere_espacio_unico' debe ser un booleano (true/false)")
 
    return errores


def validar_grados(grados: list[dict], ids_cursos: set[str]) -> list[str]:
    errores = []
 
    if len(grados) == 0:
        errores.append("[grados] La lista de grados no puede estar vacía")
        return errores
 
    ids_vistos = set()
    for grado in grados:
        gid = grado.get("id", "")
 
        if not gid:
            errores.append("[grados] Se encontró un grado sin campo 'id'")
            continue
 
        if gid in ids_vistos:
            errores.append(f"[grados] ID duplicado: '{gid}'")
        ids_vistos.add(gid)
 
        if "nombre" not in grado:
            errores.append(f"[grados][{gid}] Falta el campo 'nombre'")
            
        if "horario_plantilla" not in grado:
            errores.append(f"[grados][{gid}] Falta el campo 'horario_plantilla'")
        else:
            plantilla = grado["horario_plantilla"]
            if len(plantilla) == 0:
                errores.append(f"[grados][{gid}] 'horario_plantilla' no puede estar vacío")
            for dia, slots in plantilla.items():
                if not isinstance(slots, int) or slots < 1:
                    errores.append(f"[grados][{gid}] los slots para '{dia}' deben ser mayores a 0")
 
        if "cursos_requeridos" not in grado:
            errores.append(f"[grados][{gid}] Falta el campo 'cursos_requeridos'")
        else:
            requeridos = grado["cursos_requeridos"]
            if len(requeridos) == 0:
                errores.append(
                    f"[grados][{gid}] 'cursos_requeridos' no puede estar vacío"
                )
            cursos_vistos = set()
            for req in requeridos:
                if "curso_id" not in req:
                    errores.append(f"[grados][{gid}] Falta 'curso_id' en curso requerido")
                    continue
                curso_id = req["curso_id"]
                if curso_id not in ids_cursos:
                    errores.append(
                        f"[grados][{gid}] El curso '{curso_id}' en "
                        f"'cursos_requeridos' no existe en la lista de cursos"
                    )
                if curso_id in cursos_vistos:
                    errores.append(
                        f"[grados][{gid}] El curso '{curso_id}' está "
                        f"duplicado en 'cursos_requeridos'"
                    )
                cursos_vistos.add(curso_id)
                
                if "horas_semanales" not in req:
                    errores.append(f"[grados][{gid}] Falta 'horas_semanales' para el curso '{curso_id}'")
                else:
                    horas = req["horas_semanales"]
                    if not isinstance(horas, int) or horas < 1:
                        errores.append(
                            f"[grados][{gid}] 'horas_semanales' de '{curso_id}' debe ser un entero mayor a 0, "
                            f"se recibió: {horas}"
                        )
 
    return errores
 
 
def validar_profesores(
    profesores: list[dict],
    ids_cursos: set[str],
    dias_validos: list[str],
    turnos_validos: list[str],
    ids_grados: set[str],
) -> list[str]:
    errores = []
 
    if len(profesores) == 0:
        errores.append("[profesores] La lista de profesores no puede estar vacía")
        return errores
 
    ids_vistos = set()
    for profesor in profesores:
        pid = profesor.get("id", "")
 
        if not pid:
            errores.append("[profesores] Se encontró un profesor sin campo 'id'")
            continue
 
        if pid in ids_vistos:
            errores.append(f"[profesores] ID duplicado: '{pid}'")
        ids_vistos.add(pid)
 
        if "nombre" not in profesor:
            errores.append(f"[profesores][{pid}] Falta el campo 'nombre'")
 
        # Validar cursos habilitados
        if "cursos_habilitados" not in profesor:
            errores.append(f"[profesores][{pid}] Falta el campo 'cursos_habilitados'")
        else:
            habilitados = profesor["cursos_habilitados"]
            for curso_id in habilitados:
                if curso_id not in ids_cursos:
                    errores.append(
                        f"[profesores][{pid}] El curso '{curso_id}' en "
                        f"'cursos_habilitados' no existe en la lista de cursos"
                    )
                    
        # Validar grados habilitados
        if "grados_habilitados" not in profesor:
            errores.append(f"[profesores][{pid}] Falta el campo 'grados_habilitados'")
        else:
            grados_hab = profesor["grados_habilitados"]
            if len(grados_hab) == 0:
                errores.append(f"[profesores][{pid}] 'grados_habilitados' no puede estar vacío")
            for grado_id in grados_hab:
                if grado_id not in ids_grados:
                    errores.append(
                        f"[profesores][{pid}] El grado '{grado_id}' en "
                        f"'grados_habilitados' no existe en la lista de grados"
                    )
 
        # Validar disponibilidad
        if "disponibilidad" not in profesor:
            errores.append(f"[profesores][{pid}] Falta el campo 'disponibilidad'")
        else:
            disponibilidad = profesor["disponibilidad"]
            if len(disponibilidad) == 0:
                errores.append(
                    f"[profesores][{pid}] 'disponibilidad' no puede estar vacío"
                )
            for dia, turnos in disponibilidad.items():
                if dia not in dias_validos:
                    errores.append(
                        f"[profesores][{pid}] El día '{dia}' en 'disponibilidad' "
                        f"no está en la configuración"
                    )
                for turno in turnos:
                    if turno not in turnos_validos:
                        errores.append(
                            f"[profesores][{pid}] El turno '{turno}' en el día '{dia}' "
                            f"no está en la configuración"
                        )

        # Validar disponibilidad preferente (opcional, debe ser subconjunto de disponibilidad estricta)
        if "disponibilidad_preferente" in profesor:
            disp_pref = profesor["disponibilidad_preferente"]
            disp_estricta = profesor.get("disponibilidad", {})
            for dia, turnos in disp_pref.items():
                if dia not in dias_validos:
                    errores.append(
                        f"[profesores][{pid}] El día '{dia}' en 'disponibilidad_preferente' "
                        f"no está en la configuración"
                    )
                for turno, sedes in turnos.items():
                    if turno not in turnos_validos:
                        errores.append(
                            f"[profesores][{pid}] El turno '{turno}' en el día '{dia}' "
                            f"de 'disponibilidad_preferente' no está en la configuración"
                        )
                    for sede, slots_pref in sedes.items():
                        # Validar subconjunto
                        try:
                            slots_estrictos = disp_estricta.get(dia, {}).get(turno, {}).get(sede, [])
                            for slot in slots_pref:
                                if slot not in slots_estrictos:
                                    errores.append(
                                        f"[profesores][{pid}] El slot {slot} en {dia}-{turno}-{sede} "
                                        f"de 'disponibilidad_preferente' no existe en la 'disponibilidad' estricta"
                                    )
                        except AttributeError:
                            # En caso de que la estructura estricta esté mal formada, será reportada arriba o fallará
                            pass
 
    return errores
 
 
def validar_secciones(
    secciones: list[dict],
    ids_grados: set[str],
    sedes_validas: list[str],
    dias_validos: list[str],
    turnos_validos: list[str],
) -> list[str]:
    errores = []
 
    if len(secciones) == 0:
        errores.append("[secciones] La lista de secciones no puede estar vacía")
        return errores
 
    ids_vistos = set()
    for seccion in secciones:
        sid = seccion.get("id", "")
 
        if not sid:
            errores.append("[secciones] Se encontró una sección sin campo 'id'")
            continue
 
        if sid in ids_vistos:
            errores.append(f"[secciones] ID duplicado: '{sid}'")
        ids_vistos.add(sid)
 
        if "nombre" not in seccion:
            errores.append(f"[secciones][{sid}] Falta el campo 'nombre'")
 
        # Validar sede
        if "sede" not in seccion:
            errores.append(f"[secciones][{sid}] Falta el campo 'sede'")
        elif seccion["sede"] not in sedes_validas:
            errores.append(
                f"[secciones][{sid}] La sede '{seccion['sede']}' "
                f"no está en la configuración"
            )
 
        # Validar disponibilidad
        if "disponibilidad" not in seccion:
            errores.append(f"[secciones][{sid}] Falta el campo 'disponibilidad'")
        else:
            disponibilidad = seccion["disponibilidad"]
            if len(disponibilidad) == 0:
                errores.append(
                    f"[secciones][{sid}] 'disponibilidad' no puede estar vacío"
                )
            for dia, turnos in disponibilidad.items():
                if dia not in dias_validos:
                    errores.append(
                        f"[secciones][{sid}] El día '{dia}' en 'disponibilidad' "
                        f"no está en la configuración"
                    )
                for turno in turnos:
                    if turno not in turnos_validos:
                        errores.append(
                            f"[secciones][{sid}] El turno '{turno}' en el día '{dia}' "
                            f"no está en la configuración"
                        )
 
        # Validar grado
        if "grado" not in seccion:
            errores.append(f"[secciones][{sid}] Falta el campo 'grado'")
        elif seccion["grado"] not in ids_grados:
            errores.append(
                f"[secciones][{sid}] El grado '{seccion['grado']}' "
                f"no existe en la lista de grados"
            )
 
    return errores
 
 
def validar_tutorias(tutorias: dict, ids_secciones: set[str], ids_profesores: set[str]) -> list[str]:
    errores = []
    
    conteo_tutor = {}
    for sid, pid in tutorias.items():
        if sid not in ids_secciones:
            errores.append(f"[tutorias] La sección '{sid}' no existe en la lista de secciones")
        if pid not in ids_profesores:
            errores.append(f"[tutorias] El profesor '{pid}' asignado a la sección '{sid}' no existe")
            continue
            
        conteo_tutor[pid] = conteo_tutor.get(pid, 0) + 1
        if conteo_tutor[pid] > 2:
            errores.append(f"[tutorias] El profesor '{pid}' excede el límite de 2 tutorías asignadas")
            
    return errores
 
 
def validar_bloques_reservados(reservas: list[dict], sedes_validas: list[str], dias_validos: list[str], turnos_validos: list[str], ids_grados: set[str]) -> list[str]:
    errores = []
    
    for idx, r in enumerate(reservas):
        sede = r.get("sede")
        dia = r.get("dia")
        turno = r.get("turno")
        opciones_slots = r.get("opciones_slots")
        grados = r.get("grados_afectados")
        
        if not sede or not dia or not turno or not opciones_slots:
            errores.append(f"[bloques_reservados][indice {idx}] Faltan campos obligatorios (sede, dia, turno, opciones_slots)")
            continue
            
        if sede not in sedes_validas:
            errores.append(f"[bloques_reservados][indice {idx}] Sede '{sede}' inválida")
        if dia not in dias_validos:
            errores.append(f"[bloques_reservados][indice {idx}] Día '{dia}' inválido")
        if turno not in turnos_validos:
            errores.append(f"[bloques_reservados][indice {idx}] Turno '{turno}' inválido")
            
        if not isinstance(opciones_slots, list) or len(opciones_slots) == 0:
            errores.append(f"[bloques_reservados][indice {idx}] 'opciones_slots' debe ser un arreglo de opciones")
        else:
            for o_idx, opt in enumerate(opciones_slots):
                if not isinstance(opt, list) or not all(isinstance(x, int) for x in opt):
                    errores.append(f"[bloques_reservados][indice {idx}][opcion {o_idx}] debe ser un arreglo de enteros")
            
        if grados is not None:
            if not isinstance(grados, list):
                errores.append(f"[bloques_reservados][indice {idx}] 'grados_afectados' debe ser un arreglo")
            else:
                for g in grados:
                    if g not in ids_grados:
                        errores.append(f"[bloques_reservados][indice {idx}] Grado afectado '{g}' no existe")

    return errores


def validar_cobertura(
    secciones: list[dict],
    profesores: list[dict],
    cursos: list[dict],
    grados: list[dict],
    tutorias: dict,
    bloques_reservados: list[dict],
) -> list[str]:
    """
    Verifica que cada curso requerido por cada sección tenga al menos
    un profesor habilitado para enseñarlo. No garantiza que los horarios
    coincidan, pero detecta casos obviamente irresolubles antes de llamar
    al solver.
    """
    errores = []
 
    mapa_cursos = {c["id"]: c for c in cursos}
    mapa_grados = {g["id"]: g for g in grados}
 
    for seccion in secciones:
        sid = seccion.get("id", "")
        grado_id = seccion.get("grado", "")
        grado = mapa_grados.get(grado_id, {})
        
        for req in grado.get("cursos_requeridos", []):
            curso_id = req.get("curso_id")
            if curso_id not in mapa_cursos:
                continue  # Ya reportado en validar_grados
                
            if curso_id == "TUT1" and tutorias:
                if not tutorias.get(sid):
                    errores.append(
                        f"[cobertura][{sid}] El curso de tutoría (TUT1) no tiene un "
                        f"tutor pre-asignado en el segmento 'tutorias'"
                    )
                continue
                
            profesores_aptos = [
                p for p in profesores
                if curso_id in p.get("cursos_habilitados", []) and grado_id in p.get("grados_habilitados", [])
            ]
            if len(profesores_aptos) == 0:
                errores.append(
                    f"[cobertura][{sid}] El curso '{curso_id}' no tiene ningún "
                    f"profesor habilitado para enseñarlo en el grado '{grado_id}'"
                )

        # Análisis Preventivo de Capacidad
        horas_requeridas = sum(req.get("horas_semanales", 0) for req in grado.get("cursos_requeridos", []))
        
        # Calcular slots disponibles originalmente
        plantilla = grado.get("horario_plantilla", {})
        # Solo sumamos los dias que tiene la seccion en su disponibilidad por si acaso,
        # o asumimos que la plantilla es el máximo. Las secciones también tienen disponibilidad,
        # pero asumiremos la plantilla global del grado.
        slots_totales = sum(plantilla.values())
        
        # Restar los slots reservados que le aplican a esta sección
        slots_reservados_seccion = 0
        for r in bloques_reservados:
            if r.get("sede") == seccion.get("sede"):
                grados_afectados = r.get("grados_afectados")
                # Aplica si el arreglo de grados está vacío/ausente, o si el grado de la sección está explícitamente en el arreglo
                if not grados_afectados or grado_id in grados_afectados:
                    # Buscamos la opción que reserve la MAYOR cantidad de slots dentro del horario habilitado (el peor escenario de capacidad)
                    dia_reserva = r.get("dia")
                    opciones_slots = r.get("opciones_slots", [])
                    
                    if dia_reserva in plantilla:
                        max_slots_dia = plantilla[dia_reserva]
                        peor_escenario = 0
                        for opt in opciones_slots:
                            slots_validos_opt = sum(1 for s in opt if 1 <= s <= max_slots_dia)
                            if slots_validos_opt > peor_escenario:
                                peor_escenario = slots_validos_opt
                        slots_reservados_seccion += peor_escenario
                                
        capacidad_real = slots_totales - slots_reservados_seccion
        if capacidad_real < horas_requeridas:
            errores.append(
                f"[cobertura][{sid}] La sección requiere {horas_requeridas} horas, pero tras aplicar "
                f"las reservas de bloques, su capacidad real es de solo {capacidad_real} slots físicos. "
                f"(Slots base: {slots_totales}, Reservas que le afectan: {slots_reservados_seccion}). "
                f"Esto garantiza que el escenario sea irresoluble."
            )

    return errores
 
 
def validar_horas_minimas(
    profesores: list[dict],
    secciones: list[dict],
    grados: list[dict]
) -> list[str]:
    errores = []
    
    mapa_grados = {g["id"]: g for g in grados}
    
    # 1. Total de demanda global
    demanda_total = 0
    for seccion in secciones:
        grado = mapa_grados.get(seccion.get("grado", ""), {})
        for req in grado.get("cursos_requeridos", []):
            demanda_total += req.get("horas_semanales", 0)
            
    # 2. Total de minimos exigidos
    minimos_totales = sum(p.get("horas_minimas", 6) for p in profesores)
    
    if minimos_totales > demanda_total:
        errores.append(
            f"[horas_minimas] La sumatoria global de horas mínimas exigidas por todos "
            f"los docentes ({minimos_totales}) supera la demanda total de horas de "
            f"todas las secciones ({demanda_total}). El escenario es matemáticamente imposible."
        )
        
    for idx, p in enumerate(profesores):
        p_id = p.get("id", f"INDEX_{idx}")
        horas_min = p.get("horas_minimas", 6)
        
        # Validación fisica
        slots_fisicos = 0
        disponibilidad = p.get("disponibilidad", {})
        if isinstance(disponibilidad, dict):
            for dia, turnos_dict in disponibilidad.items():
                for turno, sedes_dict in turnos_dict.items():
                    for sede, slots in sedes_dict.items():
                        if isinstance(slots, list):
                            slots_fisicos += len(slots)
                
        if horas_min > slots_fisicos:
            errores.append(
                f"[horas_minimas][{p_id}] Exige {horas_min} horas mínimas pero su "
                f"disponibilidad física solo suma {slots_fisicos} slots."
            )
            
        # Validación curricular (horas máximas que podría dictar)
        horas_curriculares_potenciales = 0
        cursos_hab = set(p.get("cursos_habilitados", []))
        grados_hab = set(p.get("grados_habilitados", []))
        
        for seccion in secciones:
            grado_id = seccion.get("grado", "")
            if grado_id in grados_hab:
                grado = mapa_grados.get(grado_id, {})
                for req in grado.get("cursos_requeridos", []):
                    if req.get("curso_id") in cursos_hab:
                        horas_curriculares_potenciales += req.get("horas_semanales", 0)
                        
        if horas_min > horas_curriculares_potenciales:
            errores.append(
                f"[horas_minimas][{p_id}] Exige {horas_min} horas mínimas pero por su "
                f"habilitación curricular (cursos y grados permitidos) solo podría "
                f"enseñar un máximo de {horas_curriculares_potenciales} horas teóricas."
            )
            
    return errores

def validar_todo(datos: dict) -> list[str]:
    """
    Ejecuta todas las validaciones en orden y retorna la lista completa
    de errores encontrados. Si la lista está vacía, los datos son válidos
    para pasar al preprocessor.
    """
    configuracion = datos.get("configuracion", {})
    categorias    = datos.get("categorias", [])
    cursos        = datos.get("cursos", [])
    profesores    = datos.get("profesores", [])
    secciones     = datos.get("secciones", [])
    grados        = datos.get("grados", [])
    tutorias      = datos.get("tutorias", {})
    bloques_reservados = datos.get("bloques_reservados", [])
 
    errores = []
    errores += validar_configuracion(configuracion)
 
    # Si la configuración tiene errores estructurales no tiene sentido
    # seguir validando porque los valores de referencia no son confiables
    if errores:
        return errores
 
    turnos_validos = configuracion.get("turnos", [])
    sedes_validas  = configuracion.get("sedes", [])
 
    errores += validar_categorias(categorias)
    ids_categorias = {c["id"] for c in categorias if "id" in c}
 
    errores += validar_cursos(cursos, ids_categorias)
    ids_cursos = {c["id"] for c in cursos if "id" in c}
    
    errores += validar_grados(grados, ids_cursos)
    ids_grados = {g["id"] for g in grados if "id" in g}
    
    dias_validos_set = set()
    for g in grados:
        if "horario_plantilla" in g:
            dias_validos_set.update(g["horario_plantilla"].keys())
    dias_validos = list(dias_validos_set)
 
    errores += validar_profesores(profesores, ids_cursos, dias_validos, turnos_validos, ids_grados)
    errores += validar_secciones(
        secciones, ids_grados, sedes_validas, dias_validos, turnos_validos
    )
    
    ids_secciones = {s["id"] for s in secciones if "id" in s}
    ids_profesores = {p["id"] for p in profesores if "id" in p}
    errores += validar_tutorias(tutorias, ids_secciones, ids_profesores)
    
    errores += validar_horas_minimas(profesores, secciones, grados)
    
    errores += validar_bloques_reservados(bloques_reservados, sedes_validas, dias_validos, turnos_validos, ids_grados)
    
    errores += validar_cobertura(secciones, profesores, cursos, grados, tutorias, bloques_reservados)
 
    return errores
 