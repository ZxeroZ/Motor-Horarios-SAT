from ortools.sat.python import cp_model
import collections

def get_configs(H: int) -> list[list[int]]:
    if H == 1:
        return [[1]]
    if H == 2:
        return [[2], [1, 1]]
    if H == 3:
        return [[3], [2, 1]]
    if H == 4:
        return [[4], [2, 2]]
    return [[H]]

def construir_modelo(datos_procesados: dict) -> tuple[cp_model.CpModel, dict]:
    """
    Construye el modelo CP-SAT usando Bloques de Variables contiguas.
    """
    model = cp_model.CpModel()
    
    config = datos_procesados["configuracion"]
    cursos = datos_procesados["cursos"]
    categorias = datos_procesados["categorias"]
    profesores_dict = datos_procesados["profesores"]
    
    profesores_por_curso = datos_procesados["profesores_por_curso"]
    requerimientos_seccion = datos_procesados["requerimientos_seccion"]
    disp_seccion = datos_procesados["disp_seccion"]
    disp_profesor = datos_procesados["disp_profesor"]
    disp_profesor_slots = datos_procesados.get("disp_profesor_slots", {})
    disp_profesor_pref_slots = datos_procesados.get("disp_profesor_pref_slots", {})
    secciones_dict = datos_procesados["secciones"]
    tutorias_dict = datos_procesados.get("tutorias", {})
    bloques_reservados = datos_procesados.get("bloques_reservados", [])
    
    turnos = config["turnos"]

    # Diccionario para almacenar las variables maestras de bloque
    bloques_z = {}
    
    # Lista para almacenar recompensas de la función objetivo
    objetivo_recompensas = []
    
    # Agrupadores
    cobertura_curso = collections.defaultdict(list)          
    unicidad_seccion = collections.defaultdict(list)          
    unicidad_profesor = collections.defaultdict(list)         
    limite_dia_profesor = collections.defaultdict(list)       
    limite_dia_categoria_sec = collections.defaultdict(list)  
    presencia_profesor_sede = collections.defaultdict(list)
    curso_espacio_unico_vars = collections.defaultdict(list)
    presencia_profesor_sede = collections.defaultdict(list)
    
    # Almacenaremos los Z clasificados para las reservas: (s_id, dia, turno, slot) -> [var, var...]
    vars_por_slot = collections.defaultdict(list)

    # 1. GENERACIÓN DEL ESPACIO BOOLEANO POR BLOQUES (Contiguos y Únicos)
    for s_id, reqs in requerimientos_seccion.items():
        s_disp = disp_seccion.get(s_id, set())
        seccion_info = secciones_dict[s_id]
        sede_id = seccion_info.get("sede")
        grado_id = seccion_info.get("grado")
        horario_plantilla = seccion_info.get("horario_plantilla", {})
        dias_seccion = list(horario_plantilla.keys())
        
        for c_id, horas in reqs.items():
            cat_id = cursos[c_id]["categoria_id"]
            H = horas
            
            if c_id == "TUT1" and tutorias_dict:
                tutor_asignado = tutorias_dict.get(s_id)
                posibles_profesores = [tutor_asignado] if tutor_asignado else []
            else:
                posibles_profesores = [
                    p_id for p_id in profesores_por_curso.get(c_id, [])
                    if grado_id in profesores_dict[p_id].get("grados_habilitados", [])
                ]
            
            configs = get_configs(H)
            all_cfg_p_vars = []
            v_dict = {}
            
            for p_id in posibles_profesores:
                for cfg_idx, blocks in enumerate(configs):
                    v = model.NewBoolVar(f"cfg_{s_id}_{c_id}_{p_id}_{cfg_idx}")
                    all_cfg_p_vars.append(v)
                    v_dict[(p_id, cfg_idx)] = v
                    
                    if len(blocks) == 1:
                        objetivo_recompensas.append((v, 100))
                    else:
                        objetivo_recompensas.append((v, 10))
            
            # 1. Cobertura Estricta Relaxed
            # model.AddExactlyOne(all_cfg_p_vars)
            
            cobertura_var = model.NewBoolVar(f"cobertura_{s_id}_{c_id}")
            model.Add(sum(all_cfg_p_vars) == cobertura_var)
            objetivo_recompensas.append((cobertura_var, 10000))
            
            for p_id in posibles_profesores:
                p_disp = disp_profesor.get(p_id, set())
                p_disp_slots = disp_profesor_slots.get(p_id, {})
                
                for cfg_idx, blocks in enumerate(configs):
                    v = v_dict[(p_id, cfg_idx)]
                    z_vars_by_day = collections.defaultdict(list)
                    
                    for sub_idx, sub_H in enumerate(blocks):
                        z_vars_sub = []
                        for dia in dias_seccion:
                            slots_del_dia = horario_plantilla.get(dia, 0)
                            for turno in turnos:
                                if (dia, turno) in s_disp and (dia, turno) in p_disp:
                                    if (dia, turno, sede_id) in p_disp_slots:
                                        slots_del_profe = p_disp_slots[(dia, turno, sede_id)]
                                    elif (dia, turno) in p_disp_slots:
                                        slots_del_profe = p_disp_slots[(dia, turno)]
                                    else:
                                        # Profesor no disponible en esta sede
                                        continue
                                    
                                    p_pref_slots = disp_profesor_pref_slots.get(p_id, {})
                                    if (dia, turno, sede_id) in p_pref_slots:
                                        pref_slots_del_profe = p_pref_slots[(dia, turno, sede_id)]
                                    elif (dia, turno) in p_pref_slots:
                                        pref_slots_del_profe = p_pref_slots[(dia, turno)]
                                    else:
                                        pref_slots_del_profe = set()
                                    
                                    # Iteramos los slots de 'Inicio' en el que el sub-bloque cabe
                                    for start in range(slots_del_dia - sub_H + 1):
                                        # start va de 0 a (slots_del_dia - sub_H)
                                        # Los slots fisicos son 1-indexados (ej. 1, 2, 3...)
                                        slots_requeridos = set(range(start + 1, start + sub_H + 1))
                                        
                                        if not slots_requeridos.issubset(slots_del_profe):
                                            continue  # El profe no está libre en estos bloques exactos

                                        variable_name = f"z_{s_id}_{c_id}_{p_id}_{dia}_{turno}_{start}_H{sub_H}_cfg{cfg_idx}_sub{sub_idx}"
                                        var = model.NewBoolVar(variable_name)
                                        
                                        # Recompensa por preferencia docente (Opción B: intersección por slot)
                                        interseccion_pref = len(slots_requeridos.intersection(pref_slots_del_profe))
                                        if interseccion_pref > 0:
                                            objetivo_recompensas.append((var, interseccion_pref * 500))
                                        
                                        # Registramos la tupla decodificadora para exporter/solver
                                        bloques_z[(s_id, c_id, p_id, dia, turno, start, sub_H, sub_idx)] = var
                                        
                                        z_vars_sub.append(var)
                                        z_vars_by_day[dia].append(var)
                                        
                                        # El bloque ocupa simultáneamente sub_H slots, los sumamos al conflicto
                                        for k in range(sub_H):
                                            slot_ocupado = start + k
                                            unicidad_seccion[(s_id, dia, turno, slot_ocupado)].append(var)
                                            unicidad_profesor[(p_id, dia, turno, slot_ocupado)].append(var)
                                            vars_por_slot[(s_id, dia, turno, slot_ocupado)].append(var)
                                            if sede_id:
                                                presencia_profesor_sede[(p_id, dia, turno, slot_ocupado, sede_id)].append(var)
                                            
                                            # Restricción de espacio único para cursos especiales
                                            if cursos[c_id].get("requiere_espacio_unico", False):
                                                curso_espacio_unico_vars[(c_id, sede_id, dia, turno, slot_ocupado)].append(var)
                                        
                                        # Para los topes diarios, ponderamos por la duración
                                        limite_dia_profesor[(p_id, dia)].append((var, sub_H))
                                        limite_dia_categoria_sec[(s_id, dia, cat_id)].append((var, sub_H))
                        
                        # Cada sub-bloque debe ser asignado exactamente una vez si V es elegido (1)
                        model.Add(sum(z_vars_sub) == v)
                    
                    # 2. Fragmentación Días Diferentes: Si hay múltiples sub-bloques,
                    #    la suma de asignaciones de toda la configuración en UN DIA no puede ser mayor a V
                    if len(blocks) > 1:
                        for dia, vars_dia in z_vars_by_day.items():
                            model.Add(sum(vars_dia) <= v)

    # 2. DECLARACIÓN DE RESTRICCIONES (CONSTRAINTS)
    
    # [B] Conflicto Sección por Slot Puntual
    for vars_list in unicidad_seccion.values():
        model.AddAtMostOne(vars_list)
        
    # [C] Conflicto Profesor por Slot Puntual
    for vars_list in unicidad_profesor.values():
        model.AddAtMostOne(vars_list)
        
    # [D] Límite de carga diaria por Profesor
    # (Comentado temporalmente por petición del usuario para evitar INFEASIBLE experimental)
    # for (p_id, dia), tuplas_var_H in limite_dia_profesor.items():
    #     max_horas = profesores_dict[p_id]["max_horas_dia"]
    #     model.Add(sum(var * h for var, h in tuplas_var_H) <= max_horas)
        
    # [E] Límite de carga diaria por Categoría
    for (s_id, dia, cat_id), tuplas_var_H in limite_dia_categoria_sec.items():
        max_horas_cat = categorias[cat_id]["max_horas_dia"]
        model.Add(sum(var * h for var, h in tuplas_var_H) <= max_horas_cat)
        
    # [F] Tiempo de traslado inter-sedes (Travel Time)
    sedes_disponibles = config.get("sedes", [])
    if len(sedes_disponibles) > 1:
        # Recuperar dias globales y slots maximos para iterar la restriccion holísticamente
        dias_usados = set()
        max_slots_global = 0
        for s in secciones_dict.values():
            plantilla = s.get("horario_plantilla", {})
            dias_usados.update(plantilla.keys())
            for slots in plantilla.values():
                if slots > max_slots_global:
                    max_slots_global = slots

        for p_id in profesores_dict.keys():
            for dia in dias_usados:
                for turno in turnos:
                    for k in range(max_slots_global - 1):
                        for sede1 in sedes_disponibles:
                            for sede2 in sedes_disponibles:
                                if sede1 != sede2:
                                    vars_sede1_k = presencia_profesor_sede.get((p_id, dia, turno, k, sede1), [])
                                    vars_sede2_k_plus_1 = presencia_profesor_sede.get((p_id, dia, turno, k + 1, sede2), [])
                                    
                                    if vars_sede1_k and vars_sede2_k_plus_1:
                                        model.Add(sum(vars_sede1_k) + sum(vars_sede2_k_plus_1) <= 1)
                                        
    # [G] Espacio único para cursos especiales (por sede)
    for vars_list in curso_espacio_unico_vars.values():
        if len(vars_list) > 1:
            model.AddAtMostOne(vars_list)
            
    # [H] Reservas Disyuntivas de Bloques
    for r_idx, r in enumerate(bloques_reservados):
        r_sede = r.get("sede")
        r_dia = r.get("dia")
        r_turno = r.get("turno")
        r_opciones = r.get("opciones_slots", [])
        r_grados = r.get("grados_afectados")
        
        # Identificar secciones afectadas por esta regla
        secciones_afectadas = []
        for s_id, s_info in secciones_dict.items():
            if s_info.get("sede") == r_sede:
                if not r_grados or s_info.get("grado") in r_grados:
                    secciones_afectadas.append(s_id)
        
        if not secciones_afectadas or not r_opciones:
            continue
            
        # Crear variables booleanas de decisión para cada opción de la regla
        y_vars = []
        for opt_idx, opt_slots in enumerate(r_opciones):
            y_var = model.NewBoolVar(f"y_reserva_{r_idx}_opt_{opt_idx}")
            y_vars.append(y_var)
            
            # Recolectar todas las variables Z que intersecan con esta opción
            vars_en_colision = []
            for s_id in secciones_afectadas:
                for slot_fisico in opt_slots:
                    slot_idx = slot_fisico - 1  # vars_por_slot usa 0-indexing internamente
                    vars_en_colision.extend(vars_por_slot.get((s_id, r_dia, r_turno, slot_idx), []))
                    
            # Si se elige esta opción (y_var == 1), ninguna de estas Z puede ser 1
            for z_var in vars_en_colision:
                model.AddImplication(y_var, z_var.Not())
                
        # El solver DEBE elegir exactamente una opción de reserva
        model.AddExactlyOne(y_vars)

    # 3. FUNCIÓN OBJETIVO
    # Maximizar las recompensas: +10000 por cobertura, +100 por no fragmentar, +10 por fragmentar.
    model.Maximize(sum(var * recompensa for var, recompensa in objetivo_recompensas))
        
    return model, bloques_z
