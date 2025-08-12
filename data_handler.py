# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 22:11:18 2023

@author: facun
"""
import pandas as pd
from jinja2 import Template
import psycopg2
from psycopg2 import pool
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
import yaml
from yaml import SafeLoader
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
            st.write(f'Detalles: {exception_type} /// {exception_value} /// {exception_traceback}')
        else:
            self._conn.commit()
        self._cursor.close()
        Conexion.free_conn(self._conn)


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


"""
def get_credentials(fulldata: bool):
    if not fulldata:
        usuario = st.session_state['username', '']
        where = f"WHERE username = '{usuario}'"
    else:
        where = ''

    with Cursor() as cursor:
        try:
            cursor.execute(f"SELECT name, username, pass, role, createdby, email FROM public.auth {where}")
            users = cursor.fetchall()
            if not users:
                print("No se encontraron usuarios en la base de datos")
                return {"usernames": {}}

            credentials = {"usernames": {}}

            # Add usernames and hashed passwords to the credentials dictionary
            for name, username, password, role, parent, email in users:
                # hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                user_dict = {"name": name, "password": password, "role": role, "parent": parent, "email": email}
                credentials["usernames"].update({username: user_dict})
                print(f"Usuario: {username}, Contraseña: {password[:10]}..., Nombre: {name}, Rol: {role}, Parent: {parent}, Email: {email}")

            print("Diccionario de credenciales:", credentials)
            return credentials
        except psycopg2.Error as e:
            st.exception(e)
            st.stop()
        except Exception as e:
            st.exception(e)
            st.stop()


def validate_password(password):
    # Regular expression to validate the password format
    pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?/&-.])[A-Za-z\d@$!%*#?/&-.]{8,}$"

    # Validate if the password matches the format
    if re.match(pattern, password):
        return True
    else:
        return False


def create_user(userdict):
    password = userdict['pass']
    hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    with Cursor() as cursor:
        try:
            query = '''
            INSERT INTO public.auth (username, name, pass, role, createdby, email)
            VALUES (%s, %s, %s, %s, %s, %s)
            '''
            values = (
                userdict['username'],
                userdict['name'],
                hashed_pwd,
                userdict['role'],
                userdict['createdby'],
                userdict['email']
            )
            cursor.execute(query, values)
            return True
        except psycopg2.Error:
            return False
        except Exception as e:
            st.exception(e)
            st.stop()


def delete_user(userdict):
    with Cursor() as cursor:
        try:
            if st.session_state['role'] == 'admin':
                query = f'''
                    DELETE FROM public.auth
                    WHERE username = '{userdict['username']}';
                '''
                cursor.execute(query)
            else:
                query = f'''
                    DELETE FROM public.auth
                    WHERE username = '{userdict['username']}' AND createdby = '{userdict['user']}';
                '''
                cursor.execute(query)
            deleted_rows = cursor.rowcount
            return deleted_rows > 0
        except psycopg2.Error as e:
            st.exception(e)
            st.stop()
        except Exception as e:
            st.exception(e)
            st.stop()


def upgrade_user_director(userdict):
    with Cursor() as cursor:
        try:
            query = f'''
                UPDATE public.auth
                SET role = 'director'
                WHERE username = '{userdict['username']}' AND createdby = '{userdict['user']}';
            '''
            cursor.execute(query)
            deleted_rows = cursor.rowcount
            return deleted_rows > 0
        except psycopg2.Error as e:
            st.exception(e)
            st.stop()
        except Exception as e:
            st.exception(e)
            st.stop()


def change_password(old_pass: str, new_pass: str):
    credential = get_credentials(fulldata=False)
    username = list(credential['usernames'].keys())[0]
    old_pass_hash = credential['usernames'][username]['password']

    if bcrypt.checkpw(old_pass.encode(), old_pass_hash.encode()):
        new_hashed_pwd = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
        with Cursor() as cursor:
            try:
                query = '''
                UPDATE public.auth
                SET pass = %s
                WHERE username = %s
                    AND name = %s
                    AND role = %s
                    AND createdby = %s
                '''
                values = (
                    new_hashed_pwd,
                    username,
                    credential['usernames'][username]['name'],
                    credential['usernames'][username]['role'],
                    credential['usernames'][username]['parent']
                )
                cursor.execute(query, values)
                return True
            except psycopg2.Error:
                return False
            except Exception as e:
                st.exception(e)
                st.stop()
    else:
        return False


def show_users(username):
    with Cursor() as cursor:
        where = ''
        if st.session_state['role'] != 'admin':
            where = f"WHERE createdby = '{username}'"
        try:
            query = f'''
            SELECT name AS Nombre, username AS Usuario, role AS Rol
            FROM public.auth
            {where};
            '''
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
            df = df.dropna(axis=1, how='all')
            return df
        except psycopg2.Error as e:
            st.exception(e)
            st.stop()
        except Exception as e:
            st.exception(e)
            st.stop()
"""
