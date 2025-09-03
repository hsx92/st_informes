import streamlit as st
import streamlit_authenticator as stauth
import yaml
from streamlit_authenticator.utilities import LoginError
from yaml import SafeLoader
from pathlib import Path


def login():
    credentials_path = Path(__file__).parent / ".streamlit" / "credentials.yaml"
    with credentials_path.open("r", encoding="utf-8") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
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
