from ortools.sat.python import cp_model
import collections

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
    
    dias = config["dias"]
    turnos = config["turnos"]
    slots_por_turno = config["slots_por_turno"]

    # Diccionario para almacenar las variables maestras de bloque
    bloques_z = {}
    
    # Agrupadores
    cobertura_curso = collections.defaultdict(list)          
    unicidad_seccion = collections.defaultdict(list)          
    unicidad_profesor = collections.defaultdict(list)         
    limite_dia_profesor = collections.defaultdict(list)       
    limite_dia_categoria_sec = collections.defaultdict(list)  

    # 1. GENERACIÓN DEL ESPACIO BOOLEANO POR BLOQUES (Contiguos y Únicos)
    for s_id, reqs in requerimientos_seccion.items():
        s_disp = disp_seccion.get(s_id, set())
        for c_id, horas in reqs.items():
            cat_id = cursos[c_id]["categoria_id"]
            H = horas
            
            for p_id in profesores_por_curso.get(c_id, []):
                p_disp = disp_profesor.get(p_id, set())
                
                for dia in dias:
                    for turno in turnos:
                        if (dia, turno) in s_disp and (dia, turno) in p_disp:
                            # Iteramos los slots de 'Inicio' en el que el bloque de tamaño H cabe
                            for start in range(slots_por_turno - H + 1):
                                variable_name = f"z_{s_id}_{c_id}_{p_id}_{dia}_{turno}_{start}_H{H}"
                                var = model.NewBoolVar(variable_name)
                                
                                # Registramos la tupla decodificadora
                                bloques_z[(s_id, c_id, p_id, dia, turno, start, H)] = var
                                
                                cobertura_curso[(s_id, c_id)].append(var)
                                
                                # El bloque ocupa simultáneamente H slots, los sumamos al conflicto
                                for k in range(H):
                                    slot_ocupado = start + k
                                    unicidad_seccion[(s_id, dia, turno, slot_ocupado)].append(var)
                                    unicidad_profesor[(p_id, dia, turno, slot_ocupado)].append(var)
                                
                                # Para los topes diarios, ponderamos por la duración del bloque en horas
                                limite_dia_profesor[(p_id, dia)].append((var, H))
                                limite_dia_categoria_sec[(s_id, dia, cat_id)].append((var, H))

    # 2. DECLARACIÓN DE RESTRICCIONES (CONSTRAINTS)
    
    # [A] Cobertura estricta: Elegir exactamente un bloque-maestro
    # Esto asignará el curso completo, de la duración esperada, con UN PROFESOR en UN DIA CONSECUTIVAMENTE.
    for (s_id, c_id), vars_list in cobertura_curso.items():
        # model.AddExactlyOne exige que matemáticamente una de estas variables sea 1, el resto 0.
        model.AddExactlyOne(vars_list)
        
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
        
    return model, bloques_z
