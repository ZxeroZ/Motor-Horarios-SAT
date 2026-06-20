from typing import List, Optional

class AppError(Exception):
    """Base para errores controlados de la aplicación."""

    def __init__(self, message: str, status_code: int = 500, errors: Optional[List[str]] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or [message]
        super().__init__(self.message)

class ValidationError(AppError):
    """Errores de validación de datos antes de procesar."""

    def __init__(self, errors: List[str]):
        super().__init__(
            message="Error de validación",
            status_code=422,
            errors=errors
        )

class DatabaseError(AppError):
    """Errores de acceso o consulta a la base de datos."""

    def __init__(self, message: str = "Error al acceder a la base de datos"):
        super().__init__(message=message, status_code=500)

class EngineError(AppError):
    """Errores del motor de optimización CP-SAT."""

    def __init__(self, message: str = "Error en el motor de optimización"):
        super().__init__(message=message, status_code=400)

class NotFoundError(AppError):
    """Recurso no encontrado."""

    def __init__(self, resource: str = "Recurso", id_value: int = None):
        msg = f"{resource} no encontrado"
        if id_value is not None:
            msg = f"{resource} con id {id_value} no encontrado"
        super().__init__(message=msg, status_code=404)

class ConflictError(AppError):
    """Conflicto de duplicados o restricción única."""

    def __init__(self, message: str = "Conflicto: el registro ya existe"):
        super().__init__(message=message, status_code=409)
