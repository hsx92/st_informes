import os
import psycopg2
import pandas as pd
import io
from psycopg2 import sql

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_CONFIG = {
    "dbname": "nombre_de_tu_db",
    "user": "tu_usuario",
    "password": "tu_contraseña",
    "host": "localhost",
    "port": "5432"
}

# --- CONFIGURACIÓN DE ARCHIVOS ---
# Ruta al directorio que contiene los archivos CSV
# Asume que la carpeta 'data' está en el mismo nivel que la carpeta del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Mapeo de archivos a tablas
ARCHIVOS_A_CARGAR = {
    'ref_provincia.csv': 'ref_provincia',
    'inversion_id_ract_esid_provincia_region_pais.csv': 'inversion_id_ract_esid_provincia_region_pais',
    'indicadores_contexto_y_sicytar.csv': 'indicadores_contexto_y_sicytar',
    'rrhh_sicytar_agregado_provincia_region_pais.csv': 'rrhh_sicytar_agregado_provincia_region_pais',
    'rrhh_ract_esid.csv': 'rrhh_ract_esid',
    'esid_inversion_sectores_provincia_region_pais.csv': 'esid_inversion_sectores_provincia_region_pais',
    'expo_nivel_tecnologico_provincia_region_pais.csv': 'expo_nivel_tecnologico_provincia_region_pais',
    'expo_por_provincia_top5.csv': 'expo_por_provincia_top5',
    'expo_tecno_destino.csv': 'expo_tecno_destino',
    'percepcion_final.csv': 'percepcion_final',
    'listado_unidades_de_id.csv': 'listado_unidades_de_id',
    'equipos_ssnn_provincia_region_pais.csv': 'equipos_ssnn_provincia_region_pais',
    'inversion_y_articulos_por_investigador_provincia_region_pais.csv': 'inversion_y_articulos_por_investigador_provincia_region_pais',
    'proyectos_pfi.csv': 'proyectos_pfi',
    'productos_provincia_region_pais_renaprod.csv': 'productos_provincia_region_pais_renaprod',
    'patentes_desagregadas_ipc_provincia_region_pais.csv': 'patentes_desagregadas_ipc_provincia_region_pais',
    'proyectos_provincia_region_pais_renaprod.csv': 'proyectos_provincia_region_pais_renaprod',
}

# --- DEFINICIÓN DEL ESQUEMA SQL (DDL) ---

SQL_SCHEMA = """
DROP TABLE IF EXISTS ref_provincia, inversion_id_ract_esid_provincia_region_pais, indicadores_contexto_y_sicytar,
rrhh_sicytar_agregado_provincia_region_pais, rrhh_ract_esid, esid_inversion_sectores_provincia_region_pais,
patentes_desagregadas_ipc_provincia_region_pais, proyectos_provincia_region_pais_renaprod,
productos_provincia_region_pais_renaprod, expo_nivel_tecnologico_provincia_region_pais, expo_por_provincia_top5,
expo_tecno_destino, percepcion_final, listado_unidades_de_id, equipos_ssnn_provincia_region_pais,
inversion_y_articulos_por_investigador_provincia_region_pais, proyectos_pfi CASCADE;

CREATE TABLE ref_provincia (
    provincia_id INTEGER PRIMARY KEY,
    provincia VARCHAR(100) NOT NULL,
    codigo_indec VARCHAR(20),
    region_mincyt VARCHAR(100),
    region_iso VARCHAR(20),
    region_cofecyt VARCHAR(100)
);

CREATE TABLE inversion_id_ract_esid_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    tipo_institucion_ract VARCHAR(100),
    monto_inversion NUMERIC(20, 2),
    monto_inversion_constante_2004 NUMERIC(20, 2)
);

CREATE TABLE indicadores_contexto_y_sicytar (
    id INTEGER PRIMARY KEY,
    provincia VARCHAR(100),
    region_cofecyt VARCHAR(100),
    poblacion_censo_2022 INTEGER,
    superficie REAL,
    vab_cepal_2022 BIGINT,
    tasas_actividad_eph_3trim_2024 REAL,
    tasa_empleo_3trim_2024 REAL,
    tasa_desocupacion_eph_3trim_2024 REAL,
    cant_empresas_sipa_2022 INTEGER,
    trabajo_registrado_sipa_2024 INTEGER,
    exportaciones_millones_uss_opex_2023 NUMERIC(15, 2),
    pea_miles_eph_3trim_2024 REAL,
    pea_miles_censo_2022 REAL,
    becario_id INTEGER,
    docente INTEGER,
    investigador INTEGER,
    otro_personal INTEGER,
    tasa_inv_millon_hab REAL,
    tasa_inv_1000_pea REAL
);

CREATE TABLE rrhh_sicytar_agregado_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    tipo_personal_sicytar VARCHAR(100),
    es_conicet VARCHAR(10),
    sexo_descripcion VARCHAR(50),
    gran_area_experticia VARCHAR(100),
    cant_personas INTEGER
);

CREATE TABLE rrhh_ract_esid (
    id SERIAL PRIMARY KEY,
    provincia_id INTEGER,
    anio INTEGER,
    tipo_institucion_ract VARCHAR(100),
    tipo_personal VARCHAR(100),
    tipo_jornada VARCHAR(50),
    valor REAL
);

CREATE TABLE esid_inversion_sectores_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    sector_clae VARCHAR(255),
    monto_inversion NUMERIC(20, 2),
    monto_inversion_constante_2004 NUMERIC(20, 2)
);

CREATE TABLE patentes_desagregadas_ipc_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    lens_id VARCHAR(255),
    application_number VARCHAR(255),
    anio INTEGER,
    provincia VARCHAR(100),
    region_cofecyt VARCHAR(100),
    renaorg_id VARCHAR(50),
    institucion VARCHAR(255),
    es_institucion_nacional BOOLEAN,
    letra_ipc_descripcion VARCHAR(255)
);

CREATE TABLE proyectos_provincia_region_pais_renaprod (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    anio_inicio INTEGER,
    institucion_financiadora VARCHAR(255),
    tmp_fondo_anpcyt VARCHAR(100),
    tipo_proyecto_cyt VARCHAR(100),
    gran_area VARCHAR(100),
    tipo_organizacion_ejecutora VARCHAR(100),
    monto_financiado_adjudicado_prorrateado NUMERIC(20, 2),
    monto_total_adjudicado_prorrateado NUMERIC(20, 2),
    monto_financiado_adjudicado_constante_2004_prorrateado NUMERIC(20, 2),
    monto_total_adjudicado_constante_2004_prorrateado NUMERIC(20, 2)
);

CREATE TABLE productos_provincia_region_pais_renaprod (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER,
    anio_publica INTEGER,
    unidad_territorial VARCHAR(100),
    tipo_producto_cientifico VARCHAR(255),
    revista_sjr VARCHAR(255),
    gran_area VARCHAR(100),
    nivel_agregacion VARCHAR(50)
);

CREATE TABLE expo_nivel_tecnologico_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    "ITEnfoqueindustria" VARCHAR(100),
    fob_millones_uss NUMERIC(20, 2)
);

CREATE TABLE expo_por_provincia_top5 (
    id SERIAL PRIMARY KEY,
    region_cofecyt VARCHAR(100),
    provincia VARCHAR(100),
    gran_rubro VARCHAR(255),
    "2021" NUMERIC(20, 2),
    "2022" NUMERIC(20, 2),
    "2023" NUMERIC(20, 2),
    "2024" NUMERIC(20, 2)
);

CREATE TABLE expo_tecno_destino (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    cod_prov VARCHAR(100),
    intensidad_tecnologica BOOLEAN,
    pais_destino VARCHAR(100),
    fob_millones_sum NUMERIC(20, 2)
);

CREATE TABLE percepcion_final (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    indicador VARCHAR(255),
    variable VARCHAR(255),
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    valor REAL
);

CREATE TABLE listado_unidades_de_id (
    organizacion_id INTEGER PRIMARY KEY,
    organizacion VARCHAR(255),
    nivel_1 VARCHAR(255),
    provincia VARCHAR(100)
);

CREATE TABLE equipos_ssnn_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    unidad_territorial VARCHAR(100),
    sistema_nacional VARCHAR(255),
    cant_equipos INTEGER,
    nivel_agregacion VARCHAR(50)
);

CREATE TABLE inversion_y_articulos_por_investigador_provincia_region_pais (
    id SERIAL PRIMARY KEY,
    anio INTEGER,
    nivel_agregacion VARCHAR(50),
    unidad_territorial VARCHAR(100),
    monto_inversion NUMERIC(20, 2),
    cant_investigadores INTEGER,
    cant_articulos INTEGER,
    inversion_investigador NUMERIC(20, 2),
    articulos_investigador REAL
);

CREATE TABLE proyectos_pfi (
    id_pfi VARCHAR(100) PRIMARY KEY,
    anio INTEGER,
    cupo VARCHAR(50),
    region_cofecyt VARCHAR(100),
    provincia VARCHAR(100),
    tema VARCHAR(255),
    sector VARCHAR(255),
    vertical VARCHAR(255),
    tecnologias TEXT,
    vertical_tecnologia TEXT
);
"""


def create_schema(conn):
    """Crea el esquema de la base de datos ejecutando el DDL."""
    try:
        with conn.cursor() as cur:
            print("Creando el esquema de la base de datos...")
            cur.execute(SQL_SCHEMA)
            conn.commit()
            print("Esquema creado exitosamente.")
    except Exception as e:
        print(f"Error al crear el esquema: {e}")
        conn.rollback()
        raise


def bulk_load_data(cur, table_name, df):
    """Carga datos en una tabla usando el método de alto rendimiento COPY."""
    # Limpia la tabla antes de la carga
    cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE;").format(sql.Identifier(table_name)))

    # Prepara los datos en un buffer en memoria
    buffer = io.StringIO()
    # Asegura que las columnas del DF coincidan con la tabla y maneja nulos
    df.columns = [f'"{col}"' if col.isdigit() or col == 'ITEnfoqueindustria' else col for col in df.columns]
    df.to_csv(buffer, index=False, header=False, sep=';', na_rep='\\N')
    buffer.seek(0)

    # Ejecuta el comando COPY
    copy_sql = sql.SQL("COPY {} FROM STDIN WITH (FORMAT CSV, DELIMITER ';', NULL '\\N')").format(sql.Identifier(table_name))
    cur.copy_expert(sql=copy_sql, file=buffer)


def upsert_from_df(cur, df, table_name, conflict_column, update_columns):
    """
    Realiza un 'upsert' (INSERT ON CONFLICT UPDATE) desde un DataFrame de pandas.
    """
    cols = df.columns.tolist()

    # Construcción de la sentencia SQL de forma segura
    insert_stmt = sql.SQL("INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT ({conflict}) DO UPDATE SET {updates}").format(
        table=sql.Identifier(table_name),
        cols=sql.SQL(', ').join(map(sql.Identifier, cols)),
        conflict=sql.Identifier(conflict_column),
        updates=sql.SQL(', ').join([
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col)) for col in update_columns
        ])
    )

    # Prepara los datos para la ejecución en bloque
    from psycopg2.extras import execute_values
    # Reemplaza NaN de pandas por None, que psycopg2 traduce a NULL
    data_tuples = [tuple(row) for row in df.replace({pd.NA: None, float('nan'): None}).itertuples(index=False)]
    execute_values(cur, insert_stmt, data_tuples)


# --- LÓGICAS DE CARGA ESPECIALES ---
def cargar_provincias(cur):
    filename = 'ref_provincia.csv'
    print(f"--- Procesando: {filename} (Carga Especial con Upsert) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, filename), sep=';')
        # Las columnas a actualizar si hay conflicto en 'provincia_id'
        update_cols = ['provincia', 'codigo_indec', 'region_mincyt', 'region_iso', 'region_cofecyt']
        upsert_from_df(cur, df, 'ref_provincia', 'provincia_id', update_cols)
        print(f" Se procesaron {len(df)} registros para ref_provincia.")
    except Exception as e:
        print(f"ERROR cargando Provincias: {e}")
        raise


def cargar_indicadores_contexto(cur):
    filename = 'indicadores_contexto_y_sicytar.csv'
    print(f"--- Procesando: {filename} (Carga Especial con Upsert) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, filename), sep=';')
        update_cols = [col for col in df.columns if col != 'id']
        upsert_from_df(cur, df, 'indicadores_contexto_y_sicytar', 'id', update_cols)
        print(f" Se procesaron {len(df)} registros para indicadores_contexto_y_sicytar.")
    except Exception as e:
        print(f"ERROR cargando IndicadoresContexto: {e}")
        raise


def cargar_unidadesID(cur):
    filename = 'listado_unidades_de_id.csv'
    print(f"--- Procesando: {filename} (Carga Especial con Upsert) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, filename), sep=';')
        update_cols = ['organizacion', 'nivel_1', 'provincia']
        upsert_from_df(cur, df, 'listado_unidades_de_id', 'organizacion_id', update_cols)
        print(f" Se procesaron {len(df)} registros para listado_unidades_de_id.")
    except Exception as e:
        print(f"ERROR cargando UnidadesID: {e}")
        raise


def cargar_proyectosPFI(cur):
    filename = 'proyectos_pfi.csv'
    print(f"--- Procesando: {filename} (Carga Especial con Upsert) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, filename), sep=';')
        update_cols = [col for col in df.columns if col != 'id_pfi']
        upsert_from_df(cur, df, 'proyectos_pfi', 'id_pfi', update_cols)
        print(f" Se procesaron {len(df)} registros para proyectos_pfi.")
    except Exception as e:
        print(f"ERROR cargando ProyectosPFI: {e}")
        raise


# --- FUNCIÓN PRINCIPAL ---

def main():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("🚀 Conexión a la base de datos PostgreSQL exitosa.")

        # 1. Crear el esquema
        create_schema(conn)

        with conn.cursor() as cur:
            # 2. Cargas especiales con lógica de "upsert"
            cargar_provincias(cur)
            cargar_indicadores_contexto(cur)
            cargar_unidadesID(cur)
            cargar_proyectosPFI(cur)

            # 3. Carga masiva para el resto de los modelos
            print("\n--- Iniciando Carga Masiva (Truncate + Copy) ---")
            special_files = [
                'ref_provincia.csv',
                'indicadores_contexto_y_sicytar.csv',
                'listado_unidades_de_id.csv',
                'proyectos_pfi.csv'
            ]

            for filename, table_name in ARCHIVOS_A_CARGAR.items():
                if filename in special_files:
                    continue  # Ya se cargaron

                filepath = os.path.join(DATA_DIR, filename)
                try:
                    print(f"Cargando datos para la tabla {table_name} desde {filename}...")
                    df = pd.read_csv(filepath, sep=';')
                    bulk_load_data(cur, table_name, df)
                    print(f" Se cargaron {len(df)} registros para {table_name}.")

                except FileNotFoundError:
                    print(f" ADVERTENCIA: No se encontró el archivo {filename}")
                except Exception as e:
                    print(f"Ocurrió un error al cargar {table_name}: {e}")
                    raise  # Detenemos la ejecución si una carga masiva falla

            conn.commit()
            print("\n Proceso de construcción y carga de datos finalizado exitosamente.")

    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Un error inesperado ocurrió: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn is not None:
            conn.close()
            print("🔌 Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    main()
