import os
import pandas as pd
import yaml
import psycopg2
from psycopg2 import pool
import logging
from logging.handlers import RotatingFileHandler
import streamlit as st
from jinja2 import Template
from copy import deepcopy
from typing import Dict
from utils import render_obj


log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)

handler = RotatingFileHandler(
    "InformesApp-dh.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(handler)
logger = logging.getLogger(__name__)


# CONN CLASS
# Configuración de la conexión a la base de datos
class Conexion:
    __HOST = st.secrets["DB_HOST"]
    __PORT = st.secrets["DB_PORT"]
    __USER = st.secrets["DB_USER"]
    __PASSWORD = st.secrets["DB_PASSWORD"]
    __DB = st.secrets["DB_NAME"]
    __MIN_CONN = 1
    __MAX_CONN = 500
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                cls._pool = pool.SimpleConnectionPool(
                    cls.__MIN_CONN,
                    cls.__MAX_CONN,
                    host=cls.__HOST,
                    port=cls.__PORT,
                    user=cls.__USER,
                    password=cls.__PASSWORD,
                    database=cls.__DB
                )

                return cls._pool
            except psycopg2.Error as e:
                raise e
            except Exception as e:
                raise e
        else:
            return cls._pool

    @classmethod
    def get_conn(cls):
        return cls.get_pool().getconn()

    @classmethod
    def free_conn(cls, conn):
        cls.get_pool().putconn(conn)


class Cursor:
    def __init__(self):
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = Conexion.get_conn()
        self._conn.autocommit = True
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            self._conn.rollback()
            st.error('Ha ocurrido un error, la transacción ha sido cancelada.')
            logger.info(f'Detalles: {exception_type} /// {exception_value} /// {exception_traceback}')
        else:
            query = getattr(self._cursor, "query", None)
            is_read_only = False
            if query:
                if isinstance(query, (bytes, bytearray)):
                    query_text = query.decode()
                else:
                    query_text = str(query)
                is_read_only = query_text.strip().lower().startswith("select")
            if not self._conn.autocommit and not is_read_only:
                self._conn.commit()
        self._cursor.close()
        Conexion.free_conn(self._conn)


# FUNCIONES

@st.cache_data
def get_provincias():
    """
    Obtiene un df de provincias desde la base de datos.

    Returns:
        pd.DataFrame: DataFrame con los nombres de provincia y sus IDs.
    """
    with Cursor() as cursor:
        try:
            cursor.execute("SELECT provincia_id, provincia, region_iso, region_cofecyt FROM ref_provincia ORDER BY region_iso;")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=["id", "provincia", "nombre_iso", "region"])
            return df
        except psycopg2.Error as e:
            st.error(f"Error al obtener las provincias: {e}")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])
        except Exception as e:
            st.error(f"Error inesperado: {e}")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])


def ejecutar_consulta_parametrizada(plantilla_sql: str, params: dict) -> pd.DataFrame:
    """
    Toma una plantilla SQL y un diccionario de parámetros, la renderiza
    y ejecuta la consulta contra la base de datos, devolviendo un DataFrame de Pandas.

    Args:
        plantilla_sql: Un string con la consulta SQL que contiene placeholders de Jinja2.
        params: Un diccionario con los valores para reemplazar los placeholders.

    Returns:
        Un DataFrame de Pandas con el resultado de la consulta.
        Retorna un DataFrame vacío si ocurre un error.
    """
    logger.info("Iniciando ejecución de consulta parametrizada...")

    # 1. Renderizado de la plantilla SQL con Jinja2 para inyectar los parámetros de forma segura
    try:
        template = Template(plantilla_sql)
        sql_renderizado = template.render(params)
        logger.info(f"SQL Renderizado: \n{sql_renderizado}")
    except Exception as e:
        logger.error(f"Error al renderizar la plantilla SQL con Jinja2: {e}")
        return pd.DataFrame()

    # 3. Ejecución de la consulta usando Pandas y el motor de SQLAlchemy
    try:
        with Cursor() as cursor:
            cursor.execute(sql_renderizado)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
        logger.info(f"Consulta exitosa. Se obtuvieron {len(df)} filas y {len(df.columns)} columnas.")
        return df
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta SQL con Pandas: {e}")
        return pd.DataFrame()


# @st.cache_data
def _load_informes() -> Dict[str, object]:
    with open("informes.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_informe(nombre_informe: str, params: Dict[str, object]) -> Dict[str, object]:
    data = _load_informes()

    informes = data.get("informe")
    if isinstance(informes, dict):
        informes = [informes]

    for informe in informes:
        if informe.get("nombre") == nombre_informe:
            informe_render = render_obj(deepcopy(informe), params)
            resultado = {"nombre": informe_render["nombre"], "componentes": {}}

            for comp_nombre, comp in informe_render.get("componentes", {}).items():
                params_comp = {k: params[k] for k in comp.get("parametros", []) if k in params}
                plantilla = comp.pop("plantilla_sql", None)
                if plantilla:
                    df = ejecutar_consulta_parametrizada(plantilla, params_comp)
                    comp["resultado_sql"] = df
                resultado["componentes"][comp_nombre] = comp
            return resultado

    raise KeyError(f"Informe '{nombre_informe}' no encontrado")
