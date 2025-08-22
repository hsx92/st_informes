# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 22:11:18 2023

@author: facun
"""
import pandas as pd
from typing import Union
from jinja2 import Template
import psycopg2
from psycopg2 import pool
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
import yaml
from yaml import SafeLoader
from copy import deepcopy
from typing import Dict
from great_tables import GT, style, loc
import logging

logging.basicConfig(filename='InformesApp-dh.log', level=logging.INFO)
logger = logging.getLogger(__name__)


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


# This class provides a context manager for database operations
class Cursor:
    def __init__(self):
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = Conexion.get_conn()
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            self._conn.rollback()
            st.error('Ha ocurrido un error, la transacción ha sido cancelada.')
            logger.info(f'Detalles: {exception_type} /// {exception_value} /// {exception_traceback}')
        else:
            self._conn.commit()
        self._cursor.close()
        Conexion.free_conn(self._conn)


def _render_str(value: str, params: dict) -> str:
    try:
        return Template(value).render(params)
    except Exception:
        return value


def render_obj(obj, params):
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


def insertar_saltos(cadena):
    if not isinstance(cadena, str):
        return cadena

    cadena_restante = cadena
    partes = []
    corte_despues_de = 35

    while len(cadena_restante) > corte_despues_de:
        try:
            # Busca el primer espacio a partir del caracter n°35
            indice_espacio = cadena_restante.index(' ', corte_despues_de)
            # Guarda la parte hasta el espacio
            partes.append(cadena_restante[:indice_espacio])
            # La cadena restante es lo que viene después del espacio
            cadena_restante = cadena_restante[indice_espacio + 1:]
        except ValueError:
            # Si no hay más espacios después de 35 caracteres, sal del bucle
            break

    # Agrega la última parte que queda de la cadena
    partes.append(cadena_restante)

    # Une todas las partes con el tag <br>
    return '<br>'.join(partes)


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


def get_informe(nombre_informe: str, params: Dict[str, object]) -> Dict[str, object]:
    with open("informes.yml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

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


def procesar_kpi(df: pd.DataFrame, config: dict) -> str:
    if df.empty or pd.isna(df.iloc[0, 0]):
        return "N/A"
    valor = df.iloc[0, 0]
    formato = config.get('format', 'raw')
    sufijo = config.get('suffix', '')
    if formato == 'int':
        return f"{int(float(valor)):,}{sufijo}".replace(",", ".")
    if formato == 'float':
        return f"{float(valor):,.2f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{valor}{sufijo}"


def tabla_pivot(componente: dict, render_gt: bool = False) -> Union[pd.DataFrame, GT, None]:
    """
    Crea una tabla dinámica (pivot table) y la formatea con great_tables.

    Args:
        componente (dict): Un diccionario con los datos y la configuración.
                          Debe contener 'resultado_sql' (DataFrame) y 'config'.

    Returns:
        GT: Un objeto de great_tables listo para ser visualizado.
    """
    # 1. Extraer el DataFrame de los datos
    df = componente['resultado_sql']

    # 2. Crear la tabla dinámica usando la configuración del componente
    pivot_config = componente['config']['pivot']
    if 'index' in pivot_config:
        tabla = (
            df
            .pivot_table(
                index=pivot_config['index'],
                columns=pivot_config['columns'],
                values=pivot_config['values'],
                aggfunc=pivot_config['aggfunc']
            )
            .reset_index()
        )
        # Borrar el contenido del column_header de la columna índice
        tabla.columns = tabla.columns.where(tabla.columns != pivot_config['index'], '')
        col_str = tabla.columns.tolist()
        col_str = col_str[1:] if col_str else []
    else:
        tabla = df.pivot_table(
            columns=pivot_config['columns'],
            values=pivot_config['values'],
            aggfunc=pivot_config['aggfunc']
        )
        col_str = tabla.columns.tolist()

    # 3. Construcción del objeto GT con el formato deseado
    if render_gt:
        try:
            gt = (
                GT(tabla)
                .tab_header(title=componente['nombre'])
                .tab_stubhead(label='')
                .opt_table_font(
                    stack="geometric-humanist"
                )
                # 1. Formato para el cuerpo de la primera columna (el índice)
                .tab_style(
                    style.css("padding-top: 25px; padding-bottom: 25px;"),  # El primer valor es el padding vertical (top/bottom)
                    locations=loc.body()
                )
                .tab_style(
                    style.css("padding-top: 15px; padding-bottom: 15px;"),  # El primer valor es el padding vertical (top/bottom)
                    locations=loc.column_header()
                )
                .tab_style(
                    style.css("padding-top: 15px; padding-bottom: 15px;"),  # El primer valor es el padding vertical (top/bottom)
                    locations=loc.header()
                )
                .tab_style(
                    style.fill(color="#4D7AAE"),
                    locations=loc.body(columns='')
                )
                # 2. Formato para el encabezado de la primera columna
                .tab_style(
                    style.text(weight="bold", color="white", align="center"),
                    locations=loc.body(columns='')
                )
                # 3. Formato para el encabezado de las otras columnas
                .tab_style(
                    style.text(weight="bold", color="white", align="center"),
                    locations=loc.column_labels()
                )
                .tab_style(
                    style=style.text(align="center", color="gray", weight="lighter"),
                    locations=loc.body(columns=col_str)
                )
                .data_color(
                    na_color="white",
                    palette=[
                        "#FDF8E7", "#FBF5E0", "#F9F2DA", "#F7EFD4", "#F5EDCE", "#F3EAC8",
                        "#F1E7C2", "#EFE4BC", "#EFE1B6", "#ECE4B1", "#EAE2AC", "#E8DFAB",
                        "#E6DC9F", "#E4D999", "#E2D693", "#E0D38D", "#DED087", "#DCCDA1"
                    ],
                    domain=[df[pivot_config['values']].min(), df[pivot_config['values']].max()],
                )
                .fmt_integer(
                    columns=col_str,
                    use_seps=True,
                    sep_mark="."
                )
                .tab_options(
                    heading_background_color="#54698B",
                    column_labels_background_color="#54698B",  # Nuevo: Color de fondo para encabezados
                    table_border_top_color="#54698B",
                    table_border_bottom_color="#54698B",
                    row_striping_include_stub=True,
                    table_font_names="Poppins"
                )
            )
            return gt
        except Exception as e:
            st.error(f"Error al crear la tabla: {e}")
            return None
    else:
        return tabla


def login():
    with open('/home/hsx2/dev/proyectos/st_informes/portalInformes/.streamlit/credentials.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        credentials='/home/hsx2/dev/proyectos/st_informes/portalInformes/.streamlit/credentials.yaml',
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=config['cookie']['expiry_days']
    )

    try:
        authenticator.login(fields={'Form name': 'Login', 'Username': 'Usuario', 'Password': 'Contraseña'}, location='main')
    except LoginError as e:
        st.error(e)

    if st.session_state["authentication_status"]:
        st.session_state["authenticator"] = authenticator
        st.title(f"Bienvenido/a {st.session_state['name']}!")
        st.subheader("◀️   Seleccione una opción del menú")
        st.markdown('''---''')
        st.title('📰 Novedades:')

        authenticator.logout('Cerrar sesión', 'main')

    elif "authentication_status" not in st.session_state:
        st.warning('Por favor ingrese usuario y contraseña')

    elif st.session_state["authentication_status"] is False:
        st.error('Usuario/contraseña incorrectos')
