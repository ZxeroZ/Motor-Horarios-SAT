import json
from typing import Dict, Any

def construir_payload(snapshot, config) -> Dict[str, Any]:
    """
    Construye el payload JSON filtrado para enviar al LLM.
    :param snapshot: Instancia del modelo HorarioSnapshot
    :param config: Instancia del modelo ConfiguracionIA
    :return: Dict con el payload
    """
    try:
        campos_habilitados = json.loads(config.campos_habilitados)
    except Exception:
        campos_habilitados = {}
        
    payload = {}
    
    # Extraer de json_data y json_metricas
    try:
        json_data = json.loads(snapshot.json_data) if snapshot.json_data else {}
    except Exception:
        json_data = {}
        
    try:
        json_metricas = json.loads(snapshot.json_metricas) if snapshot.json_metricas else {}
    except Exception:
        json_metricas = {}

    kpis = json_metricas.get("kpis", {})

    # 1. Contexto del escenario
    if campos_habilitados.get("contexto_escenario", True):
        estadisticas = json_data.get("estadisticas", {})
        payload["contexto_escenario"] = {
            "estado_solver": json_data.get("estado", snapshot.estado),
            "tiempo_solver_segundos": estadisticas.get("tiempo_segundos", snapshot.tiempo_segundos),
            "ramas_exploradas": estadisticas.get("ramas_exploradas", 0),
            "total_profesores": len(json_metricas.get("profesores", {})),
            "total_clases": json_metricas.get("resumen_slots", {}).get("total_ocupados", 0)
        }

    # 2. KPIs
    payload["kpis"] = {}
    
    if campos_habilitados.get("kpis.cobertura", True) and "cobertura" in kpis:
        payload["kpis"]["cobertura"] = kpis["cobertura"]
        
    if campos_habilitados.get("kpis.balance_docente", True) and "balance_docente" in kpis:
        payload["kpis"]["balance_docente"] = kpis["balance_docente"]
        
    if campos_habilitados.get("kpis.fragmentacion", True) and "fragmentacion" in kpis.get("balance_docente", {}):
        payload["kpis"]["fragmentacion"] = kpis["balance_docente"]["fragmentacion"]
        
    if campos_habilitados.get("kpis.utilizacion", True) and "utilizacion" in kpis:
        payload["kpis"]["utilizacion_sedes"] = kpis["utilizacion"].get("ocupacion_por_sede", {})
        payload["kpis"]["densidad_diaria"] = {
            dia: data.get("densidad", 0)
            for dia, data in kpis["utilizacion"].get("densidad_diaria", {}).items()
        }
        
    if campos_habilitados.get("kpis.saturacion_cursos", False) and "saturacion_cursos" in kpis:
        payload["kpis"]["saturacion_cursos"] = kpis["saturacion_cursos"]

    if not payload["kpis"]:
        del payload["kpis"]

    # 3. Anomalías (construidas en base a umbrales empíricos)
    if campos_habilitados.get("anomalias", True):
        anomalias = []
        
        # Desbalance
        if "balance_docente" in kpis and "balance_carga" in kpis["balance_docente"]:
            bc = kpis["balance_docente"]["balance_carga"]
            if bc.get("coeficiente_variacion", 0) > 0.4:
                anomalias.append({
                    "tipo": "desbalance_alto",
                    "descripcion": f"Coeficiente de variación alto ({bc['coeficiente_variacion']}). Hay mala distribución de horas."
                })
            pmax = bc.get("profesor_mas_cargado", {})
            prom = bc.get("promedio_horas", 0)
            if pmax and prom > 0 and pmax.get("horas", 0) > prom * 1.5:
                anomalias.append({
                    "tipo": "sobrecarga_docente",
                    "descripcion": f"{pmax.get('id')} tiene {pmax.get('horas')}h frente al promedio de {prom}h."
                })
                
        # Cobertura baja
        if "cobertura" in kpis:
            cob = kpis["cobertura"]
            if cob.get("tasa_global", 1) < 1.0:
                anomalias.append({
                    "tipo": "cobertura_incompleta",
                    "descripcion": f"Faltan asignar clases. Tasa global: {cob.get('tasa_global')}."
                })
                
        # Utilizacion
        if "utilizacion" in kpis:
            sedes = kpis["utilizacion"].get("ocupacion_por_sede", {})
            for sede, ut in sedes.items():
                if ut > 0.95:
                    anomalias.append({
                        "tipo": "sede_saturada",
                        "descripcion": f"Sede {sede} está al {ut*100}% de su capacidad."
                    })
                elif ut < 0.5:
                    anomalias.append({
                        "tipo": "sede_subutilizada",
                        "descripcion": f"Sede {sede} está solo al {ut*100}% de su capacidad."
                    })
                    
        if anomalias:
            payload["anomalias"] = anomalias

    return payload
