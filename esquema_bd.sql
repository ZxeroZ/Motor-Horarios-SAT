-- 1. Tablas independientes o base
CREATE TABLE Colegio (
    id_colegio INT AUTO_INCREMENT PRIMARY KEY,
    nombre_colegio VARCHAR(255) NOT NULL
);

CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE Dias (
    id_dia INT AUTO_INCREMENT PRIMARY KEY,
    nombre_dia VARCHAR(50) NOT NULL,
    orden INT
);

CREATE TABLE Grado (
    id_grado INT AUTO_INCREMENT PRIMARY KEY,
    numero INT NOT NULL
);

CREATE TABLE areas (
    id_area INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    max_horas_dia INT
);

CREATE TABLE profesores (
    id_profesor INT AUTO_INCREMENT PRIMARY KEY,
    nombre_profesor VARCHAR(255) NOT NULL
);

-- 2. Tablas con dependencias de nivel 1
CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    id_colegio INT,
    FOREIGN KEY (id_colegio) REFERENCES Colegio(id_colegio)
);

CREATE TABLE Sedes (
    id_sede INT AUTO_INCREMENT PRIMARY KEY,
    id_colegio INT,
    nombre_sede VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_colegio) REFERENCES Colegio(id_colegio)
);

CREATE TABLE Bloque (
    id_bloque INT AUTO_INCREMENT PRIMARY KEY,
    id_turno INT,
    numero_bloque INT,
    hora_inicio TIME,
    hora_final TIME,
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE grado_dia_config (
    id_config INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT,
    id_dia INT,
    bloques_dia INT,
    FOREIGN KEY (id_grado) REFERENCES Grado(id_grado),
    FOREIGN KEY (id_dia) REFERENCES Dias(id_dia)
);

CREATE TABLE cursos (
    id_curso INT AUTO_INCREMENT PRIMARY KEY,
    id_area INT,
    nombre_curso VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_area) REFERENCES areas(id_area)
);

-- 3. Tablas con dependencias de nivel 2
CREATE TABLE seccion (
    id_seccion INT AUTO_INCREMENT PRIMARY KEY,
    id_sede INT,
    id_grado INT,
    nombre VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_sede) REFERENCES Sedes(id_sede),
    FOREIGN KEY (id_grado) REFERENCES Grado(id_grado)
);

CREATE TABLE profesor_curso (
    id_profesor_curso INT AUTO_INCREMENT PRIMARY KEY,
    id_profesor INT,
    id_curso INT,
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
);

CREATE TABLE sedes_profesor (
    id_sede_profesor INT AUTO_INCREMENT PRIMARY KEY,
    id_profesor INT,
    id_sede INT,
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    FOREIGN KEY (id_sede) REFERENCES Sedes(id_sede)
);

-- 4. Tablas con dependencias de nivel 3 (relacionales y cruces complejos)
CREATE TABLE seccion_turno (
    id_seccion_turno INT AUTO_INCREMENT PRIMARY KEY,
    id_seccion INT,
    id_turno INT,
    id_dia INT,
    FOREIGN KEY (id_seccion) REFERENCES seccion(id_seccion),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    FOREIGN KEY (id_dia) REFERENCES Dias(id_dia)
);

CREATE TABLE plan_estudio (
    id_plan INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT,
    id_curso INT,
    horas_semanales INT,
    FOREIGN KEY (id_grado) REFERENCES Grado(id_grado),
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
);

CREATE TABLE Tutoria (
    id_tutoria INT AUTO_INCREMENT PRIMARY KEY,
    id_seccion INT,
    id_profesor INT,
    FOREIGN KEY (id_seccion) REFERENCES seccion(id_seccion),
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor)
);

CREATE TABLE profesor_disponibilidad (
    id_disponibilidad INT AUTO_INCREMENT PRIMARY KEY,
    id_profesor INT,
    id_dia INT,
    id_turno INT,
    id_sede INT,
    nro_bloque INT,
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    FOREIGN KEY (id_dia) REFERENCES Dias(id_dia),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    FOREIGN KEY (id_sede) REFERENCES Sedes(id_sede)
);

CREATE TABLE profesor_preferencia (
    id_preferencia INT AUTO_INCREMENT PRIMARY KEY,
    id_profesor INT,
    id_dia INT,
    id_turno INT,
    id_sede INT,
    nro_bloque INT,
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    FOREIGN KEY (id_dia) REFERENCES Dias(id_dia),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    FOREIGN KEY (id_sede) REFERENCES Sedes(id_sede)
);

CREATE TABLE horario_final (
    id_horario_final INT AUTO_INCREMENT PRIMARY KEY,
    id_seccion INT,
    id_dia INT,
    num_bloque INT,
    id_curso INT,
    id_profesor INT,
    id_turno INT,
    FOREIGN KEY (id_seccion) REFERENCES seccion(id_seccion),
    FOREIGN KEY (id_dia) REFERENCES Dias(id_dia),
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
    FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);
