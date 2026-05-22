<div align="center">
  <h1>🏫 Motor de Horarios CP-SAT</h1>
  <p><em>Un motor de optimización matemática para la generación de horarios escolares.</em></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/OR_Tools-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google OR-Tools"/>
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React"/>
    <img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  </p>
</div>

---

## 📑 Tabla de Contenidos

1. [Acerca del Proyecto](#-acerca-del-proyecto)
2. [Arquitectura y Componentes](#-arquitectura-y-componentes)
3. [Restricciones (Constraints)](#️-restricciones-del-motor)
4. [Modelo Matemático](#-modelo-matemático)
5. [Instalación y Configuración](#-instalación-y-configuración)

---

## 💡 Acerca del Proyecto

Este proyecto implementa un motor de optimización de horarios escolares utilizando **Google OR-Tools (Constraint Programming - SAT)**. Está diseñado bajo una arquitectura modular y desacoplada, lo que permite su funcionamiento tanto de forma autónoma como su integración dentro de un framework web moderno y responsivo.

---

## 🏗 Arquitectura y Componentes

Este sistema está dividido en dos grandes pilares tecnológicos: el **Backend API** (Gestión de datos y reglas de negocio) y el **Motor Matemático** (Resolución NP-Hard).

### 🖥️ 1. Pilar Backend y API (Gestión de Datos)
Toda la capa de servicios, persistencia y orquestación está construida en **FastAPI** y **SQLModel (SQLite)**. Esta capa es fundamental, ya que el motor matemático no puede consumir datos crudos.

| Componente | Descripción |
|---|---|
| 🗄️ **`models.py`** | Diseño de la Base de Datos Relacional. Implementa más de 15 tablas normalizadas para manejar Sedes, Cursos, Disponibilidad Hiper-Granular y Restricciones. |
| 🛡️ **`main.py` (API)** | Expone endpoints RESTful robustos para realizar CRUD sobre las entidades académicas y actúa como pasarela segura para desencadenar el motor. |
| 🔌 **`engine_connector.py`** | **El puente vital.** Se encarga de leer la base de datos relacional, aplanar las estructuras complejas y traducir los registros SQL a los diccionarios matriciales que el motor necesita. |
| 💾 **Persistencia** | Se encarga de destruir horarios obsoletos y persistir eficientemente el resultado matemático (`HorarioFinal`) mapeándolo a los bloques visuales. |

### 🧠 2. Pilar Motor Matemático (OR-Tools)
Pipeline secuencial de procesamiento y búsqueda:

| Módulo | Descripción |
|---|---|
| 🔌 **`loader.py` & `validators.py`** | Ingiere los datos, valida la integridad referencial y carga la memoria estructural. |
| ⚙️ **`preprocessor.py`** | Traductor algorítmico. Convierte datos jerárquicos a diccionarios y conjuntos matemáticos ($O(1)$). |
| 🧠 **`model.py`** | El cerebro matemático. Genera configuraciones, inyecta restricciones y construye la Función Objetivo. |
| 🚀 **`solver.py`** | Invoca a los *workers* de OR-Tools para explorar el árbol de decisiones y decodificar la solución. |
| 📤 **`exporter.py`** | Formatea la salida bruta del solver en un formato presentable y ordenado. |
| 📊 **`metrics.py`** | Módulo analítico post-ejecución. Evalúa la calidad, calculando métricas de infraestructura y horas. |

---

## ⚖️ Restricciones del Motor

El motor opera bajo un riguroso set de reglas matemáticas para asegurar horarios humanos y factibles:

### 🔴 Restricciones Duras (Hard Constraints)
- **Disponibilidad Matricial:** Control hiper-granular a nivel de (Día $\rightarrow$ Turno $\rightarrow$ Sede $\rightarrow$ Bloques).
- **Validación Estricta:** Un profesor solo se asigna si los bloques requeridos son un subconjunto estricto de su disponibilidad en la sede adecuada.
- **Exclusividad Absoluta:** Un profesor/sección no puede estar en dos clases simultáneamente.
- **Tiempo de Traslado (Travel Time):** Prohíbe que un profesor dicte en sedes distintas en bloques consecutivos sin espacio natural de traslado.
- **Límite de Sobrecarga:** Limita las horas que una sección recibe de una misma "Área de Conocimiento" en un mismo día.
- **Repelencia de Días:** Si un curso de 3h se divide en `[2h, 1h]`, estos fragmentos jamás caerán el mismo día.

### 🟢 Restricciones Blandas (Soft Constraints)
- **Disponibilidad Preferente:** Zonas horarias "ideales" para el docente. El motor premia la asignación en estas franjas sin obligarlas estrictamente.

---

## 📐 Modelo Matemático

A diferencia de modelos básicos de franjas unitarias, este motor resuelve **Bloques Contiguos** dinámicos.

### Función Objetivo por Recompensas
El motor maximiza el siguiente puntaje global en su árbol de búsqueda:

1. **🏆 Asignación Primordial (+10,000 pts):** Prioridad absoluta para que no queden cursos sin dictarse.
2. **⭐ Preferencia Docente (+500 pts / bloque):** Premia ubicar la clase en el horario ideal del maestro.
3. **🧱 Contigüidad (+100 pts vs +10 pts):** Cursos impartidos sin fragmentarse ganan mayor puntaje.

> **💡 El Sacrificio Calculado:** Dado que *Preferencia > Contigüidad*, el motor sacrificará tener bloques juntos (los romperá) si eso permite colocar las horas dentro del horario preferente del docente.


---

## 🚀 Instalación y Configuración

> **Nota para Colaboradores:** La base de datos real y los scripts de poblamiento automatizado **no** se incluyen en el repositorio por políticas de privacidad de la data. 

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/ZxeroZ/Motor-Horarios-SAT.git
   cd Motor-Horarios-SAT
   ```

2. **Crear y activar el entorno virtual**
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicializar la Base de Datos**
   El repositorio no incluye datos reales. Para generar el esquema de SQLite en blanco, ejecuta:
   ```bash
   sqlite3 database.db < esquema_bd.sql
   ```
   *(Deberás insertar tus datos de prueba usando el panel de Administración en el Frontend).*

5. **Levantar el Backend (API)**
   ```bash
   uvicorn backend.main:app --reload
   ```

6. **Levantar el Frontend (React)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---
<div align="center">
  <i>Construido con lógica, matemáticas y mucha paciencia ☕</i><br>
  <!-- Backend by AG_zero -->
</div>
