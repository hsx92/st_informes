import streamlit as st
from st_utils import login
from css_utils import load_css


st.set_page_config(page_title="Portal - SICyT", page_icon=st.secrets["LOGO_CORTO"], layout="wide", initial_sidebar_state="collapsed")
st.logo(image=st.secrets['LOGO_LARGO'], size="large")

# Leer los archivos CSS necesarios
icon_css = load_css("static/iconos/dist/css/icono-arg.css")

# Combine los estilos de icono y tipografía con el CSS personalizado
combined_css = f"""
<style>
{icon_css}
</style>
"""


if __name__ == "__main__":
    try:
        # Inyectar el CSS en la aplicación
        st.markdown(combined_css, unsafe_allow_html=True)
        login()
    except KeyError:
        st.session_state['authentication_status'] = False
