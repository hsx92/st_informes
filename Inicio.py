import streamlit as st
from st_utils import login
from css_utils import load_css
from logging_config import setup_logging


# Configurar logging al inicio de la aplicación
logger, audit_logger = setup_logging("SICyT_Portal")

st.set_page_config(
    page_title="Portal - SICyT",
    page_icon=st.secrets["LOGO_CORTO"],
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.logo(image=st.secrets['LOGO_LARGO'], size="large")

# Inicializar estado de sesión para logs
if 'show_logs_ui' not in st.session_state:
    st.session_state.show_logs_ui = st.secrets.get("SHOW_LOGS_UI", False)

# Leer los archivos CSS necesarios
try:
    icon_css = load_css("static/iconos/dist/css/icono-arg.css")
    logger.debug("Archivos CSS cargados correctamente")
except Exception as e:
    logger.error(f"Error al cargar archivos CSS: {e}")
    icon_css = ""

# Combine los estilos de icono y tipografía con el CSS personalizado
combined_css = f"""
<style>
{icon_css}
</style>
"""


if __name__ == "__main__":
    try:
        # Log de inicio de sesión
        logger.info("Iniciando aplicación Portal SICyT")
        
        # Inyectar el CSS en la aplicación
        st.markdown(combined_css, unsafe_allow_html=True)
        
        # Intentar login
        login_result = login()
        
        # Log de resultado de autenticación
        if st.session_state.get('authentication_status'):
            username = st.session_state.get('username', 'unknown')
            audit_logger.log_login(username, success=True)
            logger.info(f"Usuario {username} autenticado exitosamente")
        elif st.session_state.get('authentication_status') is False:
            # Login fallido
            audit_logger.log_login(
                st.session_state.get('username_input', 'unknown'),
                success=False
            )
            
    except KeyError as e:
        logger.error(f"Error de configuración en autenticación: {e}")
        st.session_state['authentication_status'] = False
        st.error("Error de configuración. Por favor contacte al administrador.")
        
    except Exception as e:
        logger.critical(f"Error crítico al iniciar la aplicación: {e}", exc_info=True)
        st.error("Error al iniciar la aplicación. Por favor recargue la página.")
