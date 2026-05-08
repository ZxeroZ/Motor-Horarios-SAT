# Motor de Horarios CP-SAT (Python)

Este proyecto implementa un motor de optimización de horarios escolares utilizando **Google OR-Tools (CP-SAT)**.
Está diseñado bajo una arquitectura modular y desacoplada, lo que permite su funcionamiento tanto de forma autónoma (CLI) como su futura integración como módulo externo o tarea en paralelo (Celery) dentro de un framework web como **Django**.

---

## 1. Estructura del JSON de Entrada (`datos.json`)

El motor ingiere un archivo JSON maestro que aglutina todas las entidades y las reglas del dominio de programación de horarios. Sus campos y entidades principales son:

### `configuracion`
Define los parámetros globales y la matriz temporal de la institución.
- `sedes`: Lista de sedes válidas.
- `dias`: Lista de días a programar (ej. "Lunes", "Martes").
- `turnos`: Identificador de turnos dictados (ej. "Mañana", "Tarde").
- `slots_por_turno`: Clases/horas académicas disponibles por cada turno.

### `categorias`
Agrupa los cursos en áreas de conocimiento para establecer restricciones blandas o pedagógicas.
- `id`, `nombre`: Identificadores básicos.
- `max_horas_dia`: Limita cuántos bloques de esta área puede recibir una sección en un mismo día (ej. Máximo 2 bloques de "Matemática" al día por sección).

### `cursos`
Define las materias individuales dictadas.
- `id`, `nombre`: Identificadores básicos.
- `categoria_id`: Referencia a su categoría raíz (FK).

### `grados`
Define el nivel académico y actúa como plantilla de la malla curricular.
- `id`, `nombre`: Identificadores del grado (ej. 1°, 2°).
- `cursos_requeridos`: Un arreglo de objetos que mapea obligatoriedades para este grado.
  - `curso_id`: Curso a dictar.
  - `horas_semanales`: Cuántos bloques/horas en total requiere el grado a la semana por este curso.

### `secciones`
Representa al grupo de alumnos que recibirán clases. Hereda la malla curricular de su grado correspondiente.
- `id`, `nombre`: Identificadores del aula (ej. 1° "A").
- `grado`: ID del grado al que pertenece, define qué cursos recibe.
- `sede`: Define el local de clases para la sección.
- `disponibilidad`: Matriz estructurada como un diccionario `{"Dia": ["Turno"]}` que marca en qué turnos estudia esta sección. 

### `profesores`
La fuerza laboral de la institución académica. 
- `id`, `nombre`: Identificadores.
- `cursos_habilitados`: Arreglo de IDs de cursos que el profesor domina y puede dictar.
- `max_horas_dia`: Limita el número total de clases que se le puede programar al profesor en un único día para evitar sobrecarga.
- `disponibilidad`: Matriz análoga a la de secciones, limitando los días y turnos de trabajo.

---

## 2. Flujo del Preprocesador (`preprocessor.py`)

El preprocesador actúa como el puente entre la validación de los datos abstractos abstractos (`loader` & `validators`) y el modelo matemático estricto. 
Su rol principal es **acotar drásticamente el espacio de búsqueda** del solver para asegurar un rendimiento del orden de milisegundos a pocos segundos.

### Flujo de Acciones:
1. **Traducciones a HashMaps O(1)**: Convierte las listas puras de JSON en diccionarios para agilizar búsquedas.
2. **Jerarquía Curricular (`requerimientos_seccion`)**: Iterando las secciones y leyendo la FK de `grado`, aplana los requerimientos, sabiendo por adelantado exactamente cuántos bloques en total necesita cada curso y cada sección específica.
3. **Mapeo Inverso de Dominios (`profesores_por_curso`)**: En lugar de consultar iterativamente qué curso puede dictar un profesor, invierte el mapeo generando listas de profesores viables `[P_ids]` para cada `curso_id`.
4. **Matriz Condensada de Disponibilidad (`disp_seccion`, `disp_profesor`)**: Remueve las listas anidadas de strings para reemplazarlas por un simple `Set` de tuplas en Python `(dia, turno)`. Esto permite usar operadores nativos de intersección como la cláusula `in`, bajando el costo computacional a $\mathcal{O}(1)$.

---

## 3. Flujo del Modelo CP-SAT (`model.py`)

Se encarga de recibir los datos transformados por el preprocesador, mapear el problema al universo matemático de booleanos e instanciar las reglas de negocio estrictas.

### Generación del Espacio Booleano
En lugar de crear un universo combinatorio ciego para variables (que generaría $\approx$ 378,000 variables y estrangularía a CP-SAT), utiliza los Sets de disponibilidad generados en el `preprocessor.py`.
Declara variables booleanas (`1` o `0`) utilizando una nomenclatura descriptiva:  
`x_{seccion}_{curso}_{profesor}_{dia}_{turno}_{slot}`

Sólo genera e indexa aquellas variables donde **la intersección de la disponibilidad del profesor y la disponibilidad de la sección coinciden en tiempo y materia**. Esto desciende el espacio computacional activo a un promedio de $\approx$ 15,000 variables.

Durante la generación de estas variables, el programa las inyecta en listas agrupadoras dinámicas `collections.defaultdict(list)`, categorizando inmediatamente a quién le pertenece esa booleana (al slot del estudiante, al slot del profesor, al conteo del día del profesor, etc.).

### Declaración de Restricciones (Constraints)
Gracias a los agrupadores dinámicos descritos, OR-Tools aplica sus reglas utilizando sumatorias simples:

1. **[A] Cobertura Exacta**: Garantiza que se programe el número total de horas semanales para cada dupla `(curso, seccion)`.  
   `sum(variables) == horas_requeridas`
2. **[B] Exclusividad / Conflicto Sección**: Garantiza que una sección no tenga 2 profesores o 2 cursos al mismo tiempo (mismo slot).  
   `sum(variables_mismo_slot_seccion) <= 1`
3. **[C] Exclusividad / Conflicto Profesor**: Evita que un maestro dicte a 2 secciones a la misma vez corporizando el concepto de ubicuidad.  
   `sum(variables_mismo_slot_profesor) <= 1`
4. **[D] Descanso / Carga Laboral del Profesor**: Cuida que la acumulación de Booleanas activas de un profesor en un solo día, independientemente del turno o curso, no supere la variable `max_horas_dia` asignada para este.  
   `sum(variables_dia_profesor) <= max_por_dia`
5. **[E] Restricciones Pedagógicas por Categoría**: Rescata el límite superior impuesto en `categorias`. Se asegura que el número de clases de un área del conocimiento impartida a una sección en un solo día, no sobresature a los estudiantes.  
   `sum(variables_dia_seccion_categoria) <= max_horas_cat`
