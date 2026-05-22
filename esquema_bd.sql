-- Esquema de la Base de Datos (Estructura Vacía)

CREATE TABLE colegio (
	id_colegio INTEGER NOT NULL, 
	nombre_colegio VARCHAR NOT NULL, 
	PRIMARY KEY (id_colegio)
);

CREATE TABLE turno (
	id_turno INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	PRIMARY KEY (id_turno)
);

CREATE TABLE grado (
	id_grado INTEGER NOT NULL, 
	numero INTEGER NOT NULL, 
	PRIMARY KEY (id_grado)
);

CREATE TABLE dias (
	id_dia INTEGER NOT NULL, 
	nombre_dia VARCHAR NOT NULL, 
	orden INTEGER NOT NULL, 
	PRIMARY KEY (id_dia)
);

CREATE TABLE areas (
	id_area INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	max_horas_dia INTEGER, 
	PRIMARY KEY (id_area)
);

CREATE TABLE profesores (
	id_profesor INTEGER NOT NULL, 
	nombre_profesor VARCHAR NOT NULL, 
	PRIMARY KEY (id_profesor)
);

CREATE TABLE usuario (
	id_usuario INTEGER NOT NULL, 
	email VARCHAR NOT NULL, 
	nombre VARCHAR NOT NULL, 
	id_colegio INTEGER, 
	PRIMARY KEY (id_usuario), 
	UNIQUE (email), 
	FOREIGN KEY(id_colegio) REFERENCES colegio (id_colegio)
);

CREATE TABLE sedes (
	id_sede INTEGER NOT NULL, 
	id_colegio INTEGER, 
	nombre_sede VARCHAR NOT NULL, 
	PRIMARY KEY (id_sede), 
	FOREIGN KEY(id_colegio) REFERENCES colegio (id_colegio)
);

CREATE TABLE bloque (
	id_bloque INTEGER NOT NULL, 
	id_turno INTEGER, 
	numero_bloque INTEGER, 
	hora_inicio TIME, 
	hora_final TIME, 
	PRIMARY KEY (id_bloque), 
	FOREIGN KEY(id_turno) REFERENCES turno (id_turno)
);

CREATE TABLE cursos (
	id_curso INTEGER NOT NULL, 
	id_area INTEGER, 
	nombre_curso VARCHAR NOT NULL, 
	PRIMARY KEY (id_curso), 
	FOREIGN KEY(id_area) REFERENCES areas (id_area)
);

CREATE TABLE grado_dia_config (
	id_config INTEGER NOT NULL, 
	id_grado INTEGER, 
	id_dia INTEGER, 
	bloques_dia INTEGER, 
	PRIMARY KEY (id_config), 
	FOREIGN KEY(id_grado) REFERENCES grado (id_grado), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia)
);

CREATE TABLE seccion (
	id_seccion INTEGER NOT NULL, 
	id_sede INTEGER, 
	id_grado INTEGER, 
	nombre VARCHAR, 
	PRIMARY KEY (id_seccion), 
	FOREIGN KEY(id_sede) REFERENCES sedes (id_sede), 
	FOREIGN KEY(id_grado) REFERENCES grado (id_grado)
);

CREATE TABLE plan_estudio (
	id_plan INTEGER NOT NULL, 
	id_grado INTEGER, 
	id_curso INTEGER, 
	horas_semanales INTEGER, 
	PRIMARY KEY (id_plan), 
	FOREIGN KEY(id_grado) REFERENCES grado (id_grado), 
	FOREIGN KEY(id_curso) REFERENCES cursos (id_curso)
);

CREATE TABLE profesor_sedes (
	id_profe_sedes INTEGER NOT NULL, 
	id_profesor INTEGER, 
	id_sede INTEGER, 
	PRIMARY KEY (id_profe_sedes), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_sede) REFERENCES sedes (id_sede)
);

CREATE TABLE profesor_disponibilidad (
	id_disponibilidad INTEGER NOT NULL, 
	id_profesor INTEGER, 
	id_dia INTEGER, 
	id_turno INTEGER, 
	id_sede INTEGER, 
	nro_bloque INTEGER, 
	PRIMARY KEY (id_disponibilidad), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia), 
	FOREIGN KEY(id_turno) REFERENCES turno (id_turno), 
	FOREIGN KEY(id_sede) REFERENCES sedes (id_sede)
);

CREATE TABLE profesor_preferencia (
	id_preferencia INTEGER NOT NULL, 
	id_profesor INTEGER, 
	id_dia INTEGER, 
	id_turno INTEGER, 
	id_sede INTEGER, 
	nro_bloque INTEGER, 
	PRIMARY KEY (id_preferencia), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia), 
	FOREIGN KEY(id_turno) REFERENCES turno (id_turno), 
	FOREIGN KEY(id_sede) REFERENCES sedes (id_sede)
);

CREATE TABLE profesor_curso (
	id_profesor_curso INTEGER NOT NULL, 
	id_profesor INTEGER, 
	id_curso INTEGER, 
	PRIMARY KEY (id_profesor_curso), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_curso) REFERENCES cursos (id_curso)
);

CREATE TABLE restricciones (
	id_restricciones INTEGER NOT NULL, 
	id_profesor INTEGER, 
	id_dia INTEGER, 
	id_bloque INTEGER, 
	PRIMARY KEY (id_restricciones), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia), 
	FOREIGN KEY(id_bloque) REFERENCES bloque (id_bloque)
);

CREATE TABLE seccion_turno (
	id_seccion_turno INTEGER NOT NULL, 
	id_seccion INTEGER, 
	id_turno INTEGER, 
	id_dia INTEGER, 
	PRIMARY KEY (id_seccion_turno), 
	FOREIGN KEY(id_seccion) REFERENCES seccion (id_seccion), 
	FOREIGN KEY(id_turno) REFERENCES turno (id_turno), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia)
);

CREATE TABLE tutoria (
	id_tutotia INTEGER NOT NULL, 
	id_seccion INTEGER, 
	id_profesor INTEGER, 
	PRIMARY KEY (id_tutotia), 
	FOREIGN KEY(id_seccion) REFERENCES seccion (id_seccion), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor)
);

CREATE TABLE carga_academica (
	id_carga INTEGER NOT NULL, 
	id_seccion INTEGER, 
	id_profesor INTEGER, 
	id_plan INTEGER, 
	PRIMARY KEY (id_carga), 
	FOREIGN KEY(id_seccion) REFERENCES seccion (id_seccion), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor), 
	FOREIGN KEY(id_plan) REFERENCES plan_estudio (id_plan)
);

CREATE TABLE horario_final (
	id_horario_final INTEGER NOT NULL, 
	id_seccion INTEGER, 
	id_dia INTEGER, 
	id_bloque INTEGER, 
	id_curso INTEGER, 
	id_profesor INTEGER, 
	PRIMARY KEY (id_horario_final), 
	FOREIGN KEY(id_seccion) REFERENCES seccion (id_seccion), 
	FOREIGN KEY(id_dia) REFERENCES dias (id_dia), 
	FOREIGN KEY(id_bloque) REFERENCES bloque (id_bloque), 
	FOREIGN KEY(id_curso) REFERENCES cursos (id_curso), 
	FOREIGN KEY(id_profesor) REFERENCES profesores (id_profesor)
);

