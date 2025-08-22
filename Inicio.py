import streamlit as st
from data_handler import login
from css_utils import load_css


st.set_page_config(page_title="Portal - SICyT", page_icon=st.secrets["LOGO_CORTO"], layout="wide", initial_sidebar_state="collapsed")
# logo = 'https://www.argentina.gob.ar/profiles/argentinagobar/themes/argentinagobar/argentinagobar_theme/logo_argentina-blanco.svg'
st.logo(image=st.secrets['LOGO_LARGO'], size="large")

custom_streamlit_css = ""

css = load_css("static/iconos/dist/css/icono-arg.css")

# Inyectar el CSS en la aplicación
st.markdown(f"<style>{css}{custom_streamlit_css}</style>", unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        login()
    except KeyError:
        st.session_state['authentication_status'] = False
