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
 
 
def validar_cobertura(
    secciones: list[dict],
    profesores: list[dict],
    cursos: list[dict],
    grados: list[dict],
    tutorias: dict,
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
                
            if curso_id == "TUT1":
                if not tutorias.get(sid):
                    errores.append(
                        f"[cobertura][{sid}] El curso de tutoría (TUT1) no tiene un "
                        f"tutor pre-asignado en el segmento 'tutorias'"
                    )
                continue
                
            profesores_aptos = [
                p for p in profesores
                if curso_id in p.get("cursos_habilitados", [])
            ]
            if len(profesores_aptos) == 0:
                errores.append(
                    f"[cobertura][{sid}] El curso '{curso_id}' no tiene ningún "
                    f"profesor habilitado para enseñarlo"
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
 
    errores += validar_profesores(profesores, ids_cursos, dias_validos, turnos_validos)
    errores += validar_secciones(
        secciones, ids_grados, sedes_validas, dias_validos, turnos_validos
    )
    
    ids_secciones = {s["id"] for s in secciones if "id" in s}
    ids_profesores = {p["id"] for p in profesores if "id" in p}
    errores += validar_tutorias(tutorias, ids_secciones, ids_profesores)
    
    errores += validar_cobertura(secciones, profesores, cursos, grados, tutorias)
 
    return errores
 