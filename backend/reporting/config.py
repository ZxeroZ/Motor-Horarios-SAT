import os
import json
from dotenv import load_dotenv

load_dotenv()

class LLMSettings:
    PROVIDER_PRIMARIO = os.getenv("LLM_PROVIDER_PRIMARIO", "openrouter")
    PROVIDER_FALLBACK = os.getenv("LLM_PROVIDER_FALLBACK", "groq")
    
    MAIN_PROVIDER_BASE_URL = os.getenv("MAIN_PROVIDER_BASE_URL", "https://openrouter.ai/api/v1")
    FALLBACK_PROVIDER_BASE_URL = os.getenv("FALLBACK_PROVIDER_BASE_URL", "https://api.groq.com/openai/v1")
    
    _modelos_primario_env = os.getenv("LLM_MODELOS_PRIMARIO", '["nvidia/nemotron-3-ultra:free", "google/gemma-2-27b-it:free", "openrouter/free"]')
    try:
        MODELOS_PRIMARIO = json.loads(_modelos_primario_env)
    except Exception:
        MODELOS_PRIMARIO = ["openrouter/free"]
        
    _modelos_fallback_env = os.getenv("LLM_MODELOS_FALLBACK", '["llama-3.3-70b-versatile", "gemma2-9b-it"]')
    try:
        MODELOS_FALLBACK = json.loads(_modelos_fallback_env)
    except Exception:
        MODELOS_FALLBACK = ["llama-3.3-70b-versatile"]

    PROMPT_BASE = os.getenv("LLM_PROMPT_BASE", "Eres un analista experto en planificación académica. Genera un reporte JSON estructurado analizando las métricas y anomalías del horario.")
    
    TEMPERATURA = float(os.getenv("LLM_TEMPERATURA", "0.3"))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

llm_settings = LLMSettings()
