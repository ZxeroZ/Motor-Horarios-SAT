# Backend — API REST para Motor de Horarios CP-SAT

## Descripción General

El backend es una **API REST construida con FastAPI + SQLModel** que actúa como intermediario entre la base de datos SQLite y el motor de optimización CP-SAT (OR-Tools de Google). Su función principal es:

1. **Exponer endpoints CRUD** para todas las entidades académicas (colegios, sedes, grados, cursos, profesores, secciones, etc.)
2. **Traducir los datos de la BD** al formato JSON que el motor CP-SAT necesita para calcular horarios
3. **Persistir el horario generado** en la tabla `horario_final` para consultas posteriores sin necesidad de recalcular

---

## Arquitectura

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   main.py (API)  │────▶│   database.db    │
│   (React)    │◀────│   FastAPI REST    │◀────│   (SQLite)       │
└──────────────┘     └────────┬─────────┘     └──────────────────┘
                              │
                              │ POST /api/generar-horario
                              ▼
                    ┌─────────────────────┐
                    │ engine_connector.py │
                    │   1. Lee la BD       │
                    │   2. Construye JSON  │
                    │   3. Llama al Motor  │
                    │   4. Guarda resultado│
                    └────────┬────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   engine/ (Motor)   │
                    │   CP-SAT OR-Tools   │
                    │   (NO es nuestro)   │
                    └─────────────────────┘
```

---

## Archivos del Backend

### `main.py` — API REST

Contiene **todos los endpoints HTTP** organizados por entidad. Cada tabla de la BD tiene al menos `GET` (listar) y `POST` (crear). Las entidades principales también tienen `PUT` (editar) y `DELETE` (borrar).

**Endpoints especiales:**
- `POST /api/login` — Autenticación por email/password
- `POST /api/generar-horario` — Ejecuta el flujo completo: BD → Validación → Motor → Guardar resultado
- `GET /api/cargar-horario` — Devuelve el último horario guardado sin recalcular

### `engine_connector.py` — El Puente (BD ↔ Motor)

Este es el archivo más crítico. Contiene tres funciones:

#### `build_json_from_db(session)`
Lee **todas las tablas** de SQLite y construye un diccionario Python con el formato exacto que el motor espera:

```json
{
  "configuracion": {"sedes": [...], "turnos": [...]},
  "categorias": [{"id": "CAT_1", "nombre": "Matemática", "max_horas_dia": 4}],
  "cursos": [{"id": "CUR_1", "nombre": "Álgebra", "categoria_id": "CAT_1"}],
  "grados": [{"id": "GRA_1", "cursos_requeridos": [...], "horario_plantilla": {"Lunes": 6, ...}}],
  "profesores": [{"id": "PROF_1", "cursos_habilitados": [...], "disponibilidad": {...}}],
  "secciones": [{"id": "SEC_1", "grado": "GRA_1", "sede": "Sede A", "disponibilidad": {...}}]
}
```

**Mapeos importantes:**
- `Areas` → `categorias` (el motor las llama categorías)
- `GradoDiaConfig` → `horario_plantilla` (cuántos bloques tiene cada día para un grado)
- `SeccionTurno` → `disponibilidad` de secciones (en qué turno estudia cada sección)
- Los IDs se prefijan: `CUR_`, `PROF_`, `SEC_`, `GRA_`, `CAT_`

#### `generar_horario_engine(session)`
Orquesta el flujo completo:
1. Llama a `build_json_from_db()` para extraer datos
2. Pasa el JSON por el validador (`utils/validators.py`)
3. Preprocesa los datos (`engine/preprocessor.py`)
4. Construye el modelo CP-SAT (`engine/model.py`)
5. Resuelve el modelo (`engine/solver.py`)
6. Si el resultado es OPTIMAL, guarda en `horario_final`

#### `_guardar_horario(session, asignaciones)`
Toma las asignaciones del motor y las persiste en la tabla `horario_final`:
- Borra el horario anterior
- Mapea IDs del motor (SEC_1, CUR_1) de vuelta a IDs numéricos de la BD
- Expande bloques contiguos en slots individuales (un bloque de 3 horas = 3 filas)

### `models.py` — Modelos de Datos

Define todas las tablas usando SQLModel (SQLAlchemy + Pydantic). Las tablas están organizadas en niveles de dependencia:

**Nivel 0 (sin dependencias):** Colegio, Turno, Grado, Dias, Areas, Usuario
**Nivel 1 (dependen del nivel 0):** Sedes, Bloque, Cursos, Profesores
**Nivel 2 (dependen del nivel 1):** Seccion, GradoDiaConfig, PlanEstudio, ProfesorCurso
**Nivel 3 (dependen del nivel 2):** SeccionTurno, Restricciones, CargaAcademica, HorarioFinal

### `database.py` — Conexión

Configura SQLite con `database.db` y proporciona la función `get_session()` para inyección de dependencias en FastAPI.

---

## Tablas de la Base de Datos

| Tabla | Propósito |
|-------|-----------|
| `colegio` | Datos del colegio |
| `sedes` | Sedes físicas (Sede A, Sede B) |
| `turno` | Turnos disponibles (Mañana, Tarde) |
| `grado` | Grados (1°, 2°, ..., 5°) |
| `dias` | Días de la semana |
| `areas` | Áreas/Categorías académicas |
| `bloque` | Bloques horarios por turno |
| `cursos` | Cursos/Materias |
| `profesores` | Profesores y su carga máxima diaria |
| `seccion` | Secciones (1° A, 1° B, etc.) |
| `grado_dia_config` | Cuántos bloques tiene cada grado por día |
| `plan_estudio` | Malla curricular: qué cursos y cuántas horas por grado |
| `profesor_curso` | Qué cursos puede dictar cada profesor |
| `seccion_turno` | En qué turno y día está disponible cada sección |
| `restricciones` | Restricciones adicionales del motor |
| `carga_academica` | Carga académica por profesor |
| `horario_final` | Resultado: cada slot asignado del horario generado |
| `usuario` | Usuarios del sistema (login) |

---

## Cómo Ejecutar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Poblar la BD con datos de prueba
python populate_db.py

# 3. Iniciar el servidor
uvicorn backend.main:app --reload
```

El servidor corre en `http://localhost:8000`. La documentación automática de la API está en `http://localhost:8000/docs`.

---

## Flujo de Generación de Horario

```
Usuario hace clic en "Generar Horario"
         │
         ▼
POST /api/generar-horario
         │
         ▼
engine_connector.build_json_from_db()
  → Lee: Sedes, Turnos, Días, Áreas, Cursos, Grados,
         PlanEstudio, GradoDiaConfig, Profesores,
         ProfesorCurso, Secciones, SeccionTurno
  → Construye JSON con formato del motor
         │
         ▼
validators.validar_todo(datos)
  → Verifica que profesores tengan cursos habilitados
  → Verifica que grados tengan cursos requeridos
  → Si falla → retorna errores al frontend
         │
         ▼
preprocessor.preprocesar(datos)
  → Crea estructuras O(1) para el solver
         │
         ▼
model.construir_modelo(datos_procesados)
  → Crea variables booleanas CP-SAT
  → Aplica restricciones (AddExactlyOne, conflictos, etc.)
         │
         ▼
solver.resolver_modelo(modelo, variables)
  → OR-Tools resuelve (~6 segundos)
  → Retorna: OPTIMAL, INFEASIBLE, o UNKNOWN
         │
         ▼
Si OPTIMAL → _guardar_horario()
  → Borra horario anterior de la BD
  → Inserta cada slot en horario_final
         │
         ▼
Retorna JSON al frontend con las asignaciones
```

---

## Notas Técnicas

- **El motor NO es parte del backend.** Los archivos en `engine/` son del compañero de algoritmos. El backend solo los invoca.
- **`horario_plantilla`** es crítico: define cuántos slots tiene cada día para cada grado. Sin esto el motor no puede calcular.
- **`SeccionTurno`** define la disponibilidad real de cada sección. Si una sección solo tiene turno Mañana, el motor no le asignará clases en la Tarde.
- **INFEASIBLE** significa que los datos son matemáticamente imposibles de resolver (demasiadas horas para los slots disponibles). Esto es responsabilidad del motor/datos, no del backend.
