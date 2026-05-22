# Motor de Horarios CP-SAT (Python)

Este proyecto implementa un motor de optimización de horarios escolares utilizando **Google OR-Tools (CP-SAT)**.
Está diseñado bajo una arquitectura modular y desacoplada, lo que permite su funcionamiento tanto de forma autónoma (CLI) como su futura integración como módulo externo o tarea en paralelo (Celery) dentro de un framework web.

---

## 1. Flujo de Ejecución y Rol de Componentes

La arquitectura del motor sigue un pipeline secuencial de procesamiento de datos:

1. **`loader.py` & `validators.py`**: Puerta de entrada del sistema. Ingiere el archivo `datos.json`, valida la integridad referencial (que las sedes existan, que los profesores dicten cursos reales, etc.) y carga la memoria estructural.
2. **`preprocessor.py`**: El traductor algorítmico. Convierte arreglos en diccionarios y Sets matemáticos ($\mathcal{O}(1)$). Aplana la jerarquía curricular para saber exactamente cuántas horas necesita cada sección, y procesa la disponibilidad granular de profesores a nivel de "Slots Físicos" (ej. `{1, 2, 3}`).
3. **`model.py`**: El cerebro matemático. Traduce las entidades a variables booleanas de CP-SAT. Aquí se generan las configuraciones de fragmentación de bloques, se inyectan las restricciones duras (Hard Constraints) y se construye la Función Objetivo para maximizar la calidad del horario.
4. **`solver.py`**: El orquestador de búsqueda. Invoca a los *workers* paralelos de Google OR-Tools para explorar el árbol de decisiones. Extrae la solución factible u óptima y decodifica las variables matemáticas ganadoras de vuelta a diccionarios Python.
5. **`exporter.py`**: Formatea la salida bruta del solver en un archivo `horario_result.json` presentable, ordenado cronológicamente y agrupado por sección y por profesor.
6. **`metrics.py`**: Módulo analítico post-ejecución. Evalúa el resultado final para emitir el `metrics.json`, calculando la carga horaria semanal de cada maestro, ocupación total de la infraestructura y contabilizando los "huecos" o espacios libres restantes por aula.

---

## 2. Restricciones Implementadas (Constraints)

El motor opera bajo un riguroso set de reglas agrupadas en Restricciones Duras (inquebrantables) y Blandas (optimizables mediante recompensas).

### A. Restricciones de Disponibilidad y Ubicuidad
* **Disponibilidad Matricial Multi-Sede:** El motor procesa la disponibilidad del docente a un nivel altamente granular: Día $\rightarrow$ Turno $\rightarrow$ Sede $\rightarrow$ Slots Físicos (ej. `{1, 2, 3}`).
* **Validación Estricta de Slots:** Un curso solo se asigna a un profesor si los *N* slots consecutivos que requiere el bloque son un subconjunto matemático estricto (`issubset`) de su disponibilidad en esa **sede específica**.
* **Exclusividad de Sección:** Una sección no puede recibir dos cursos ni atender a dos profesores en el mismo slot físico.
* **Exclusividad de Profesor:** Un maestro no puede estar en dos aulas al mismo tiempo.
* **Tiempo de Traslado Inter-Sedes (Travel Time):** El motor prohíbe que un profesor sea asignado a dos sedes distintas en slots consecutivos (a excepción del quiebre natural provocado por el recreo).

### C. Restricciones Blandas (Soft Constraints)
* **Disponibilidad Preferente:** Los docentes pueden tener horarios "ideales" (ej. "Prefiero dictar los Lunes a primera hora"). Esta preferencia es una restricción blanda; el motor **premiará** la colocación de la clase en esos bloques específicos sin forzar un error si no es posible. Se garantiza matemáticamente mediante validadores que la zona preferente sea un subconjunto de la zona de disponibilidad estricta.

### B. Restricciones Pedagógicas y Laborales
* **Límite de Sobrecarga por Categoría:** Limita la cantidad de horas que una sección puede recibir de una misma área de conocimiento (ej. "Ciencias") en un solo día para evitar fatiga estudiantil.
* **Repelencia de Días (Fragmentación):** Si un curso de 3 horas se divide en submódulos de 2 y 1 hora, estos fragmentos *jamás* caerán en el mismo día.

---

## 3. Modelo Matemático: Fragmentación y Función Objetivo

A diferencia de modelos básicos de franjas unitarias, este motor resuelve **Bloques Contiguos** dinámicos, lo cual eleva la complejidad matemática pero garantiza horarios humanamente coherentes.

### 3.1. Booleanas de Sub-Bloque ($Z$)
Para cada requerimiento (Sección $s$, Curso $c$, Profesor $p$), el motor evalúa distintas configuraciones de fragmentación ($cfg$). Por ejemplo, 3 horas pueden dictarse juntas `[3]` o dividirse `[2, 1]`.

Por cada sub-módulo (ej. el bloque de 2 horas) que inicia en el slot $i$, se crea una variable booleana $Z$:
$$Z_{s, c, p, d, t, i, H, cfg, sub} \in \{0, 1\}$$
Donde $H$ es la duración del bloque. Si $Z = 1$, significa que el curso arranca en el slot $i$ y ocupará automáticamente los slots $[i, i+1, \dots, i+H-1]$.

### 3.2. Activador de Configuración ($V$)
Para que CP-SAT sepa qué estrategia de fragmentación se está usando, existe una booleana superior $V_{p, cfg}$.
$$ \sum_{cfg} V_{p, cfg} \le 1 $$
*(Un profesor solo puede ejecutar UNA configuración de fragmentación para un curso específico).*

### 3.3. Relación de Dependencia
Si el motor decide activar la configuración `[2, 1]` ($V = 1$), entonces está **obligado** a agendar exactamente un bloque de 2 horas y un bloque de 1 hora en la semana:
$$ \sum (Z_{\text{bloque 1}}) = V \quad \text{y} \quad \sum (Z_{\text{bloque 2}}) = V $$

### 3.4. La Función Objetivo (Objective Function)
Dado que a veces es matemáticamente imposible agendar el 100% de los cursos por topes de disponibilidad, el motor pasó de requerir "Cobertura Estricta" a un modelo de "Maximización por Recompensas".

Se crea una variable de estado $\text{Cobertura}_{s, c} \in \{0, 1\}$ que indica si un curso logró asignarse a una sección.
Adicionalmente, se evalúa si los slots $k$ ocupados por una variable sub-bloque $Z$ intersecan con los slots de la **Disponibilidad Preferente** del docente ($\text{Pref}_{p}$).

$$ \text{Maximize} \left( \sum (\text{Cobertura} \times 10000) + \sum (Z \cap \text{Pref}_{p} \times 500) + \sum (V_{cfg} \times \text{Reward}_{cfg}) \right) $$

**Jerarquía de Comportamiento Emergente (Asignación > Preferencia > Contigüidad):**
1. **Asignación Primordial (+10,000 pts):** El motor prioriza sobre todas las cosas que la clase se dicte. Jamás dejará un curso vacío si existe una permutación matemática que permita encajarlo.
2. **Preferencia Docente (+500 pts por slot):** Si hay múltiples lugares válidos, el motor escoge el que caiga en la "Disponibilidad Preferente" del maestro.
3. **Contigüidad (+100 pts vs +10 pts):** Si el curso no se fragmenta (ej. `[3]`), gana 100 puntos. Si se fragmenta (ej. `[2, 1]`), gana 10 puntos.
4. **El Sacrificio Calculado:** Al ser la Preferencia (+500) matemáticamente mayor que la Contigüidad (+100), si un curso de 3 horas no entra entero en la zona preferida del profesor, el motor **decidirá romper el curso** (sacrificando los 90 pts de diferencia) para poder colocar al menos 1 o 2 horas dentro del horario preferente del docente, maximizando el puntaje global.
