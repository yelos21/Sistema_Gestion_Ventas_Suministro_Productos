-- 4.1 Creación y gestión de bases de datos (consola, psql)

CREATE DATABASE practica_proyecto;
CREATE DATABASE practica_ejemplo1;
CREATE DATABASE practica_ejemplo2;
CREATE DATABASE practica_ejemplo3;

\l practica_*

-- Gestión: renombrar y eliminar 
CREATE DATABASE practica_temporal;
ALTER DATABASE practica_temporal RENAME TO practica_temporal2;
DROP DATABASE practica_temporal2;

\l practica_*
