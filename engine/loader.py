import json
from pathlib import Path
 
 
def cargar_datos(ruta_json: str) -> dict:
    """
    Lee el archivo JSON de entrada y retorna los datos como diccionario.
    No realiza validaciones de integridad, solo verifica que el archivo
    exista, sea legible y tenga formato JSON válido.
 
    Args:
        ruta_json: Ruta al archivo JSON de entrada.
 
    Returns:
        Diccionario con los datos cargados.
 
    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
        ValueError: Si el archivo no tiene formato JSON válido.
    """
    ruta = Path(ruta_json)
 
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_json}")
 
    if not ruta.is_file():
        raise FileNotFoundError(f"La ruta no corresponde a un archivo: {ruta_json}")
 
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"El archivo no tiene formato JSON válido: {e}")
 
    return datos
 
 
def extraer_configuracion(datos: dict) -> dict:
    return datos.get("configuracion", {})
 
 
def extraer_categorias(datos: dict) -> list[dict]:
    return datos.get("categorias", [])
 
 
def extraer_cursos(datos: dict) -> list[dict]:
    return datos.get("cursos", [])
 
 
def extraer_profesores(datos: dict) -> list[dict]:
    return datos.get("profesores", [])
 
 
def extraer_secciones(datos: dict) -> list[dict]:
    return datos.get("secciones", [])


def extraer_grados(datos: dict) -> list[dict]:
    return datos.get("grados", [])