import streamlit as st
from data_handler import login


st.set_page_config(page_title="Informes - SICyT", page_icon='📊', layout="wide", initial_sidebar_state="collapsed")
logo = r'https://www.argentina.gob.ar/profiles/argentinagobar/themes/argentinagobar/argentinagobar_theme/logo_argentina-blanco.svg'
st.logo(image=logo, size="large")

with open("static/iconos/dist/css/icono-arg.css", "r") as css_file:
    css = css_file.read()

# Inyectar el CSS en la aplicación
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        login()
    except KeyError:
        st.session_state['authentication_status'] = False
