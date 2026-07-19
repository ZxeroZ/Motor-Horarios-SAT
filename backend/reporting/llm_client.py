import os
import json
import time
from typing import Dict, Any, Tuple
import logging
from openai import OpenAI
from backend.reporting.config import llm_settings

logger = logging.getLogger(__name__)

# Configuración de proveedores (basado en APIs compatibles con OpenAI)
PROVIDERS = {
    "openrouter": {
        "base_url": llm_settings.MAIN_PROVIDER_BASE_URL,
        "api_key_env": "MAIN_PROVIDER_API_KEY",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/ZxeroZ/Motor-Horarios-SAT",
            "X-OpenRouter-Title": "Motor-Horarios-SAT"
        }
    },
    "groq": {
        "base_url": llm_settings.FALLBACK_PROVIDER_BASE_URL,
        "api_key_env": "FALLBACK_PROVIDER_API_KEY",
        "extra_headers": {}
    }
}

def call_llm_api(provider_name: str, model: str, system_prompt: str, payload: dict, temperature: float, max_tokens: int) -> Tuple[dict, dict]:
    """
    Realiza la llamada a la API usando el SDK de OpenAI.
    Retorna (resultado_json, metricas_uso).
    """
    provider_info = PROVIDERS.get(provider_name)
    if not provider_info:
        raise ValueError(f"Proveedor desconocido: {provider_name}")

    api_key = os.getenv(provider_info["api_key_env"])
    if not api_key:
        raise ValueError(f"Falta API key en variable de entorno: {provider_info['api_key_env']}")

    client = OpenAI(
        base_url=provider_info["base_url"],
        api_key=api_key,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ]

    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            extra_headers=provider_info["extra_headers"]
        )
    except Exception as e:
        raise RuntimeError(f"Error en la API de {provider_name}: {str(e)}")
    
    end_time = time.time()
    
    raw_content = response.choices[0].message.content
    try:
        parsed_json = json.loads(raw_content)
    except json.JSONDecodeError:
        # Fallback de limpieza si el modelo incluyó sintaxis markdown (```json ... ```) a pesar de la restricción
        clean_content = raw_content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        parsed_json = json.loads(clean_content.strip())

    usage = {
        "tokens_usados": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0,
        "tiempo_respuesta_ms": int((end_time - start_time) * 1000)
    }

    return parsed_json, usage


def generar_reporte(system_prompt: str, payload: dict, config: Any) -> Tuple[dict, str, str, dict]:
    """
    Ejecuta el mecanismo de fallback intra e inter proveedor.
    Retorna (reporte_estructurado, provider_exitoso, modelo_exitoso, metricas_uso)
    """
    modelos_primario = config.MODELOS_PRIMARIO
    modelos_fallback = config.MODELOS_FALLBACK

    # 1. Fallback Intra-Proveedor (Primario)
    for modelo in modelos_primario:
        try:
            logger.info(f"Intentando generar reporte con {config.PROVIDER_PRIMARIO} -> {modelo}")
            res, usage = call_llm_api(
                provider_name=config.PROVIDER_PRIMARIO,
                model=modelo,
                system_prompt=system_prompt,
                payload=payload,
                temperature=config.TEMPERATURA,
                max_tokens=config.MAX_TOKENS
            )
            return res, config.PROVIDER_PRIMARIO, modelo, usage
        except Exception as e:
            logger.warning(f"Fallo en {config.PROVIDER_PRIMARIO} con modelo {modelo}: {str(e)}. Reintentando siguiente modelo...")
            time.sleep(1.5)  # Backoff leve
            
    # 2. Fallback Inter-Proveedor (Secundario)
    if not modelos_fallback:
        raise Exception(f"Todos los modelos de {config.PROVIDER_PRIMARIO} fallaron y no hay fallback configurado.")
        
    logger.warning(f"Todos los modelos de {config.PROVIDER_PRIMARIO} fallaron. Pasando al provider fallback: {config.PROVIDER_FALLBACK}")
    
    for modelo in modelos_fallback:
        try:
            logger.info(f"Intentando generar reporte con {config.PROVIDER_FALLBACK} -> {modelo}")
            res, usage = call_llm_api(
                provider_name=config.PROVIDER_FALLBACK,
                model=modelo,
                system_prompt=system_prompt,
                payload=payload,
                temperature=config.TEMPERATURA,
                max_tokens=config.MAX_TOKENS
            )
            return res, config.PROVIDER_FALLBACK, modelo, usage
        except Exception as e:
            logger.warning(f"Fallo en {config.PROVIDER_FALLBACK} con modelo {modelo}: {str(e)}. Reintentando siguiente modelo...")
            time.sleep(1.5)
            
    raise Exception("El mecanismo de fallback se agotó. No se pudo generar el reporte con ningún proveedor ni modelo.")
