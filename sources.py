import pandas as pd
import yaml
import psycopg2
from psycopg2 import pool
import streamlit as st
from jinja2 import Template
from copy import deepcopy
from typing import Dict
from functools import wraps
import time
from logging_config import get_logger, log_database_operation, log_execution

# Initialize logger for this module
logger = get_logger(__name__)


# Performance monitoring decorator
def monitor_performance(threshold: float = 1.0):
    """Decorator to monitor and log slow operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                if elapsed_time > threshold:
                    logger.warning(
                        f"Slow operation detected: {func.__name__} took {elapsed_time:.2f} seconds"
                    )
                else:
                    logger.debug(f"{func.__name__} completed in {elapsed_time:.2f} seconds")
                
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed_time:.2f} seconds: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


# CONN CLASS with enhanced logging
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
                logger.info(f"Creating database connection pool to {cls.__HOST}:{cls.__PORT}/{cls.__DB}")
                
                cls._pool = pool.SimpleConnectionPool(
                    cls.__MIN_CONN,
                    cls.__MAX_CONN,
                    host=cls.__HOST,
                    port=cls.__PORT,
                    user=cls.__USER,
                    password=cls.__PASSWORD,
                    database=cls.__DB
                )
                
                logger.info(f"Database pool created successfully with {cls.__MIN_CONN}-{cls.__MAX_CONN} connections")
                return cls._pool
                
            except psycopg2.Error as e:
                logger.critical(f"Failed to create database pool: {e}")
                raise
            except Exception as e:
                logger.critical(f"Unexpected error creating database pool: {e}")
                raise
        else:
            return cls._pool

    @classmethod
    def get_conn(cls):
        try:
            conn = cls.get_pool().getconn()
            logger.debug("Database connection acquired from pool")
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    @classmethod
    def free_conn(cls, conn):
        try:
            cls.get_pool().putconn(conn)
            logger.debug("Database connection returned to pool")
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
            raise


class Cursor:
    def __init__(self):
        self._conn = None
        self._cursor = None
        self._start_time = None

    def __enter__(self):
        self._start_time = time.time()
        self._conn = Conexion.get_conn()
        self._conn.autocommit = True
        self._cursor = self._conn.cursor()
        logger.debug("Database cursor created")
        return self._cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        elapsed_time = time.time() - self._start_time
        
        if exception_value:
            self._conn.rollback()
            logger.error(
                f"Database transaction rolled back after {elapsed_time:.2f}s due to error: {exception_value}"
            )
            st.error('Ha ocurrido un error, la transacción ha sido cancelada.')
        else:
            query = getattr(self._cursor, "query", None)
            is_read_only = False
            
            if query:
                if isinstance(query, (bytes, bytearray)):
                    query_text = query.decode()
                else:
                    query_text = str(query)
                    
                is_read_only = query_text.strip().lower().startswith("select")
                # Log for slow queries
                if elapsed_time > 1.0:
                    logger.warning(f"Slow query detected ({elapsed_time:.2f}s): {query_text[:200]}...")

            if not self._conn.autocommit and not is_read_only:
                self._conn.commit()
                logger.debug(f"Database transaction committed after {elapsed_time:.2f}s")
        
        self._cursor.close()
        Conexion.free_conn(self._conn)


# HELPERS with logging

@log_execution()
def _render_str(value: str, params: dict) -> str:
    """Render a string template with parameters."""
    try:
        return Template(value).render(params)
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        return value


@log_execution()
def render_obj(obj, params):
    """Recursively render an object with parameters."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            rendered_key = _render_str(k, params) if isinstance(k, str) else k
            new_dict[rendered_key] = render_obj(v, params)
        return new_dict
    if isinstance(obj, list):
        return [render_obj(i, params) for i in obj]
    if isinstance(obj, str):
        return _render_str(obj, params)
    return obj


@st.cache_data(ttl=600)
@log_execution()
def _load_informes() -> Dict[str, object]:
    """Load report configurations from YAML file."""
    try:
        with open("informes.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.info("Report configurations loaded successfully")
            return data
    except FileNotFoundError:
        logger.error("informes.yml file not found")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse informes.yml: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading informes.yml: {e}")
        raise


@log_execution()
def get_informe(nombre_informe: str, params: Dict[str, object]) -> Dict[str, object]:
    """Get and process a report with the given parameters."""
    logger.info(f"Generating report: {nombre_informe} with params: {params}")
    
    try:
        data = _load_informes()

        informes = data.get("informe")
        if isinstance(informes, dict):
            informes = [informes]

        for informe in informes:
            if informe.get("nombre") == nombre_informe:
                logger.debug(f"Report template '{nombre_informe}' found")
                
                informe_render = render_obj(deepcopy(informe), params)
                resultado = {"nombre": informe_render["nombre"], "componentes": {}}

                component_count = len(informe_render.get("componentes", {}))
                logger.debug(f"Processing {component_count} components for report '{nombre_informe}'")

                for comp_nombre, comp in informe_render.get("componentes", {}).items():
                    try:
                        params_comp = {k: params[k] for k in comp.get("parametros", []) if k in params}
                        plantilla = comp.pop("plantilla_sql", None)
                        
                        if plantilla:
                            logger.debug(f"Executing SQL for component: {comp_nombre}")
                            df = ejecutar_consulta_parametrizada(plantilla, params_comp)
                            comp["resultado_sql"] = df
                            
                        resultado["componentes"][comp_nombre] = comp
                        
                    except Exception as e:
                        logger.error(f"Failed to process component '{comp_nombre}': {e}")
                        # Continue processing other components
                        comp["resultado_sql"] = pd.DataFrame()
                        comp["error"] = str(e)
                        resultado["componentes"][comp_nombre] = comp
                
                logger.info(f"Report '{nombre_informe}' generated successfully")
                return resultado

        logger.error(f"Report '{nombre_informe}' not found in configuration")
        raise KeyError(f"Informe '{nombre_informe}' no encontrado")
        
    except KeyError:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report '{nombre_informe}': {e}")
        raise


# DB COMMS with enhanced logging

@st.cache_data(ttl=600)
@log_database_operation("SELECT")
def get_provincias() -> pd.DataFrame:
    """
    Obtiene un df de provincias desde la base de datos.

    Returns:
        pd.DataFrame: DataFrame con los nombres de provincia y sus IDs.
    """
    with Cursor() as cursor:
        try:
            query = "SELECT provincia_id, provincia, region_iso, region_cofecyt FROM ref_provincia ORDER BY region_iso;"
            cursor.execute(query)
            rows = cursor.fetchall()
            
            df = pd.DataFrame(rows, columns=["id", "provincia", "nombre_iso", "region"])
            logger.info(f"Retrieved {len(df)} provinces from database")
            return df
            
        except psycopg2.Error as e:
            logger.error(f"Database error retrieving provinces: {e}")
            st.error(f"Error al obtener las provincias: {e}")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving provinces: {e}")
            st.error(f"Error inesperado: {e}")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])


@log_database_operation("SELECT")
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
    logger.debug(f"Executing parameterized query with params: {params}")

    # 1. Renderizado de la plantilla SQL con Jinja2
    try:
        template = Template(plantilla_sql)
        sql_renderizado = template.render(params)
        
        # Log query for debugging (truncated for security)
        query_preview = sql_renderizado[:200] + "..." if len(sql_renderizado) > 200 else sql_renderizado
        logger.debug(f"Rendered SQL query: {query_preview}")
        
    except Exception as e:
        logger.error(f"Failed to render SQL template: {e}")
        return pd.DataFrame()

    # 2. Ejecución de la consulta
    try:
        with Cursor() as cursor:
            cursor.execute(sql_renderizado)
            rows = cursor.fetchall()
            
            if rows:
                column_names = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)
                logger.info(f"Query successful: {len(df)} rows × {len(df.columns)} columns returned")
            else:
                logger.warning("Query returned no results")
                df = pd.DataFrame()
                
        return df
        
    except psycopg2.Error as e:
        logger.error(f"Database error executing query: {e}")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        return pd.DataFrame()


# Health check function
def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        with Cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("Database connection check successful")
                return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
    
    return False


# Export functions
__all__ = [
    'Conexion',
    'Cursor',
    'get_provincias',
    'get_informe',
    'ejecutar_consulta_parametrizada',
    'render_obj',
    'check_database_connection'
]
