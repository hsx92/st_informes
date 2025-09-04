
import pandas as pd
import yaml
import psycopg2
from psycopg2 import pool
import streamlit as st
from jinja2 import Template
from copy import deepcopy
from typing import Dict
import time

# Importar el nuevo sistema de logging
from logging_config import get_logger, log_execution_time, log_database_query, setup_logging

# Inicializar logger para este módulo
logger = get_logger(__name__)

# Si es el módulo principal, configurar logging
if __name__ == "__main__":
    main_logger, audit_logger = setup_logging()


# CONN CLASS con logging mejorado
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
        """Obtiene el pool de conexiones con logging"""
        if cls._pool is None:
            try:
                logger.info(f"Creando pool de conexiones a {cls.__HOST}:{cls.__PORT}/{cls.__DB}")
                
                cls._pool = pool.SimpleConnectionPool(
                    cls.__MIN_CONN,
                    cls.__MAX_CONN,
                    host=cls.__HOST,
                    port=cls.__PORT,
                    user=cls.__USER,
                    password=cls.__PASSWORD,
                    database=cls.__DB
                )
                
                logger.info(f"Pool de conexiones creado exitosamente (min: {cls.__MIN_CONN}, max: {cls.__MAX_CONN})")
                return cls._pool
                
            except psycopg2.Error as e:
                logger.error(f"Error al crear pool de conexiones PostgreSQL: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.critical(f"Error inesperado al crear pool de conexiones: {e}", exc_info=True)
                raise
        else:
            return cls._pool

    @classmethod
    def get_conn(cls):
        """Obtiene una conexión del pool"""
        try:
            conn = cls.get_pool().getconn()
            logger.debug("Conexión obtenida del pool")
            return conn
        except Exception as e:
            logger.error(f"Error al obtener conexión del pool: {e}")
            raise

    @classmethod
    def free_conn(cls, conn):
        """Libera una conexión al pool"""
        try:
            cls.get_pool().putconn(conn)
            logger.debug("Conexión devuelta al pool")
        except Exception as e:
            logger.error(f"Error al liberar conexión: {e}")


class Cursor:
    def __init__(self):
        self._conn = None
        self._cursor = None
        self._query_start = None

    def __enter__(self):
        self._conn = Conexion.get_conn()
        self._conn.autocommit = True
        self._cursor = self._conn.cursor()
        self._query_start = time.time()
        return self._cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        execution_time = time.time() - self._query_start
        
        if exception_value:
            self._conn.rollback()
            
            # Log del error con contexto completo
            logger.error(
                "Error en transacción de BD",
                exc_info=(exception_type, exception_value, exception_traceback),
                extra={
                    'query': getattr(self._cursor, 'query', 'N/A'),
                    'execution_time': execution_time
                }
            )
            
            # Mostrar error al usuario de forma amigable
            if "authentication_status" in st.session_state and st.session_state["authentication_status"]:
                st.error('⚠️ Ha ocurrido un error al procesar los datos. El equipo técnico ha sido notificado.')
            
        else:
            # Log de queries exitosas (si está habilitado)
            query = getattr(self._cursor, "query", None)
            if query:
                if isinstance(query, (bytes, bytearray)):
                    query_text = query.decode()
                else:
                    query_text = str(query)
                    
                # Log solo queries lentas o si está en modo debug
                if execution_time > 1.0 or st.secrets.get("LOG_QUERIES", False):
                    log_database_query(query_text, execution_time=execution_time)
                
                # Detectar queries de solo lectura
                is_read_only = query_text.strip().lower().startswith("select")
                if not self._conn.autocommit and not is_read_only:
                    self._conn.commit()
                    logger.debug(f"Transacción confirmada (tiempo: {execution_time:.3f}s)")
                    
        self._cursor.close()
        Conexion.free_conn(self._conn)


# HELPERS con logging

def _render_str(value: str, params: dict) -> str:
    """Renderiza una cadena con parámetros Jinja2"""
    try:
        return Template(value).render(params)
    except Exception as e:
        logger.warning(f"Error al renderizar template: {e}. Valor original: {value[:100]}...")
        return value


def render_obj(obj, params):
    """Renderiza recursivamente un objeto con parámetros"""
    try:
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
    except Exception as e:
        logger.error(f"Error al renderizar objeto: {e}")
        return obj


@st.cache_data(ttl=600)
@log_execution_time
def _load_informes() -> Dict[str, object]:
    """Carga la configuración de informes desde YAML"""
    try:
        logger.debug("Cargando configuración de informes desde informes.yml")
        with open("informes.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.info("Configuración de informes cargada exitosamente")
        return data
    except FileNotFoundError:
        logger.error("Archivo informes.yml no encontrado")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error al parsear informes.yml: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al cargar informes: {e}")
        raise


def get_informe(nombre_informe: str, params: Dict[str, object]) -> Dict[str, object]:
    """Obtiene y procesa un informe con sus componentes"""
    logger.info(f"Generando informe: {nombre_informe}", extra={'params': params})
    
    try:
        data = _load_informes()
        
        informes = data.get("informe")
        if isinstance(informes, dict):
            informes = [informes]
        
        for informe in informes:
            if informe.get("nombre") == nombre_informe:
                logger.debug(f"Informe {nombre_informe} encontrado, procesando componentes...")
                
                informe_render = render_obj(deepcopy(informe), params)
                resultado = {"nombre": informe_render["nombre"], "componentes": {}}
                
                total_componentes = len(informe_render.get("componentes", {}))
                componentes_procesados = 0
                
                for comp_nombre, comp in informe_render.get("componentes", {}).items():
                    try:
                        logger.debug(f"Procesando componente: {comp_nombre}")
                        
                        params_comp = {k: params[k] for k in comp.get("parametros", []) if k in params}
                        plantilla = comp.pop("plantilla_sql", None)
                        
                        if plantilla:
                            df = ejecutar_consulta_parametrizada(plantilla, params_comp)
                            comp["resultado_sql"] = df
                            logger.debug(f"Componente {comp_nombre}: {len(df)} filas obtenidas")
                        
                        resultado["componentes"][comp_nombre] = comp
                        componentes_procesados += 1
                        
                    except Exception as e:
                        logger.error(f"Error procesando componente {comp_nombre}: {e}")
                        # Continuar con otros componentes
                        comp["error"] = str(e)
                        resultado["componentes"][comp_nombre] = comp
                
                logger.info(
                    f"Informe {nombre_informe} generado: {componentes_procesados}/{total_componentes} componentes procesados"
                )
                return resultado
        
        logger.error(f"Informe '{nombre_informe}' no encontrado en la configuración")
        raise KeyError(f"Informe '{nombre_informe}' no encontrado")
        
    except Exception as e:
        logger.error(f"Error generando informe {nombre_informe}: {e}", exc_info=True)
        raise


# DB COMMS con logging mejorado

@st.cache_data(ttl=600)
@log_execution_time
def get_provincias():
    """
    Obtiene un df de provincias desde la base de datos.

    Returns:
        pd.DataFrame: DataFrame con los nombres de provincia y sus IDs.
    """
    logger.debug("Obteniendo listado de provincias")
    
    with Cursor() as cursor:
        try:
            query = "SELECT provincia_id, provincia, region_iso, region_cofecyt FROM ref_provincia ORDER BY region_iso;"
            cursor.execute(query)
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=["id", "provincia", "nombre_iso", "region"])
            
            logger.info(f"Provincias obtenidas: {len(df)} registros")
            return df
            
        except psycopg2.Error as e:
            logger.error(f"Error de BD al obtener provincias: {e}")
            st.error("Error al obtener las provincias")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])
            
        except Exception as e:
            logger.critical(f"Error inesperado al obtener provincias: {e}", exc_info=True)
            st.error("Error inesperado al cargar los datos")
            return pd.DataFrame(columns=["id", "provincia", "nombre_iso", "region"])


@log_execution_time
def ejecutar_consulta_parametrizada(plantilla_sql: str, params: dict, retry_count: int = 3, timeout: int = 30) -> pd.DataFrame:
    """
    Ejecuta consulta SQL con reintentos, timeout y logging completo.
    
    Args:
        plantilla_sql: Un string con la consulta SQL que contiene placeholders de Jinja2.
        params: Un diccionario con los valores para reemplazar los placeholders.
        retry_count: Número de reintentos en caso de error
        timeout: Timeout en segundos
        
    Returns:
        Un DataFrame de Pandas con el resultado de la consulta.
        Retorna un DataFrame vacío si ocurre un error.
    """
    logger.info("Ejecutando consulta parametrizada", extra={'params': params})
    
    for attempt in range(retry_count):
        try:
            # 1. Renderizar plantilla
            template = Template(plantilla_sql)
            sql_renderizado = template.render(params)
            
            # Log de la query renderizada (solo en debug)
            if st.secrets.get("DEBUG_MODE", False):
                logger.debug(f"SQL renderizado: {sql_renderizado[:500]}...")
            
            # 2. Ejecutar con timeout
            start_time = time.time()
            
            with Cursor() as cursor:
                # Configurar timeout
                cursor.execute(f"SET statement_timeout = {timeout * 1000};")
                
                # Ejecutar query principal
                cursor.execute(sql_renderizado)
                
                # Validar resultados
                if cursor.rowcount == 0:
                    logger.warning(
                        "Consulta sin resultados",
                        extra={'query_preview': plantilla_sql[:100], 'params': params}
                    )
                    return pd.DataFrame()
                
                # Obtener resultados
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)
                
                execution_time = time.time() - start_time
                
                # Log de éxito
                logger.info(
                    f"Consulta exitosa: {len(df)} filas x {len(df.columns)} columnas en {execution_time:.2f}s",
                    extra={
                        'rows': len(df),
                        'columns': len(df.columns),
                        'execution_time': execution_time,
                        'params': params
                    }
                )
                
                return df
                
        except psycopg2.OperationalError as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt  # Backoff exponencial
                logger.warning(
                    f"Error de conexión (intento {attempt + 1}/{retry_count}), reintentando en {wait_time}s: {e}"
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"Error de conexión después de {retry_count} intentos",
                    exc_info=True,
                    extra={'query_preview': plantilla_sql[:200], 'params': params}
                )
                return pd.DataFrame()
                
        except psycopg2.extensions.QueryCanceledError:
            logger.error(
                f"Query cancelada por timeout ({timeout}s)",
                extra={'query_preview': plantilla_sql[:200], 'params': params}
            )
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(
                f"Error ejecutando consulta: {e}",
                exc_info=True,
                extra={'query_preview': plantilla_sql[:200], 'params': params}
            )
            return pd.DataFrame()
    
    return pd.DataFrame()
