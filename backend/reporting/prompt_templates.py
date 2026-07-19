import json

SYSTEM_PROMPT = """{prompt_base}

Se te proporcionará un payload JSON estructurado con métricas de rendimiento y anomalías detectadas en un horario escolar generado de forma algorítmica (con un solver CP-SAT).

Tu objetivo es analizar estos datos y retornar un reporte en formato JSON estricto que cumpla con el siguiente esquema. No agregues markdown (como ```json) ni texto fuera del objeto JSON.

Esquema JSON requerido:
{{
  "resumen_ejecutivo": "Un párrafo breve y profesional (max 3 oraciones) resumiendo la calidad general del horario.",
  "decisiones_clave": [
    {{
      "area": "Nombre del área (ej. Distribución docente, Utilización de sedes, etc.)",
      "explicacion": "Análisis de qué hizo el algoritmo y por qué basado en las métricas.",
      "impacto": "alto | medio | bajo"
    }}
  ],
  "alertas": [
    {{
      "severidad": "alta | media | baja",
      "area": "Área afectada (ej. Cobertura curricular)",
      "mensaje": "Descripción de la alerta o cuello de botella.",
      "sugerencia": "Recomendación accionable para el administrador."
    }}
  ],
  "sugerencias_optimizacion": [
    {{
      "prioridad": 1,
      "accion": "Sugerencia específica para modificar los datos de entrada o restricciones.",
      "impacto_esperado": "Qué mejoraría si se aplica esta sugerencia."
    }}
  ],
  "metricas_interpretadas": {{
    "salud_general": "excelente | buena | regular | pobre",
    "puntuacion": 85,
    "areas_fuertes": ["lista", "de", "áreas"],
    "areas_mejora": ["lista", "de", "áreas"]
  }}
}}

Asegúrate de basar todo tu análisis puramente en los datos del payload proporcionado.
"""

def get_system_prompt(prompt_base: str) -> str:
    return SYSTEM_PROMPT.format(prompt_base=prompt_base)
