"""
Página principal del sistema de informes con autenticación mejorada.
Utiliza streamlit-authenticator de forma correcta y completa.
"""

import streamlit as st
from auth_manager import get_auth_manager, authenticated_menu, unauthenticated_menu
from css_utils import load_css
from logging_config import get_logger, get_audit_logger, log_execution, log_streamlit_component
# Inicializar loggers
logger = get_logger('inicio')
audit_logger = get_audit_logger()

# Configuración de la página
st.set_page_config(
    page_title="Portal - SICyT",
    page_icon=st.secrets.get("LOGO_CORTO", "🏛️"),
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.logo(image=st.secrets.get('LOGO_LARGO', ''), size="large")

# Cargar CSS
try:
    icon_css = load_css("static/iconos/dist/css/icono-arg.css") if st.secrets.get("USE_ICONS", False) else ""
    logger.debug("CSS de iconos cargado correctamente.")
except Exception as e:
    icon_css = ""
    logger.error(f"Error cargando CSS de iconos: {e}")

# CSS personalizado
custom_css = """
    /* Estilos para el formulario de login */
    div[data-testid="stForm"] {
        max-width: 500px;
        margin: auto;
        padding: 2rem;
        background-color: #232D4F;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Estilos para métricas */
    div[data-testid="stMetricValue"] > div {
        color: #7589A3;
        font-weight: 500;
        font-size: 1.5rem;
    }
    
    /* Estilos para el header */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #354B6E 0%, #7589A3 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    /* Estilos para las tarjetas de bienvenida */
    .welcome-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 1rem;
        color: #232D4F;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
        color: #232D4F;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
"""

combined_css = f"""
<style>
{icon_css}
{custom_css}
</style>
"""

st.markdown(combined_css, unsafe_allow_html=True)

# Inicializar AuthManager
try:
    auth_manager = get_auth_manager()
    logger.debug("AuthManager inicializado correctamente.")
except Exception as e:
    st.error("Error inicializando el sistema de autenticación. Por favor, contacte al administrador.", icon=":material/close:")
    logger.critical(f"Error crítico con autenticación en AuthManager: {e}")
    st.stop()


@log_execution(log_args=False)
def show_login_page():

    """
    Muestra la página de login.
    """
    unauthenticated_menu()
    ip = st.context.ip_address
    if ip:
        logger.info(f"Página principal accedida por IP: {ip}")
    else:
        logger.info("Página principal accedida por IP local.")

    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>Portal de Informes - DNIYES</h1>
        <p>Secretaría de Innovación, Ciencia y Tecnología</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Tabs para diferentes opciones de acceso
        tab1, tab2, tab3 = st.tabs([":material/lock: Iniciar Sesión", ":material/app_registration: Registrarse", ":material/key_vertical: Recuperar Acceso"])

        with tab1:
            st.markdown("### Bienvenido de vuelta")
            st.markdown("Por favor, ingrese sus credenciales para acceder al sistema.")
            
            # Widget de login
            try:
                auth_manager.login(location='main')
            except Exception as e:
                st.error("Error en el login. Contacte al administrador.", icon=":material/close:")
                logger.critical(f"Error crítico en el widget de login: {e}")
                st.stop()
            # Información adicional
            with st.expander("¿Problemas para acceder?", icon=":material/info:"):
                st.markdown("""
                - Verifique que su usuario y contraseña sean correctos
                - Las contraseñas son sensibles a mayúsculas y minúsculas
                - Después de 5 intentos fallidos, su cuenta será bloqueada
                - Contacte al administrador si necesita ayuda: dgicyt@sicyt.gob.ar
                """)
        
        with tab2:
            st.markdown("### Crear Nueva Cuenta")
            st.info("Complete el formulario para solicitar acceso al sistema.", icon=":material/info:")
            
            try:
                # Widget de registro
                email, username, name = auth_manager.register_user(
                    location='main',
                    roles=['viewer']  # Rol por defecto para nuevos usuarios
                )
                
                if email:
                    st.success(
                        f"""
                        Registro exitoso!
                        
                        **Usuario:** {username}
                        **Nombre:** {name}
                        **Email:** {email}
                        
                        Ahora puede iniciar sesión con sus credenciales.
                        """,
                        icon=":material/check_circle:"
                    )
                    st.balloons()
            except Exception as e:
                st.error("Error en el registro. Contacte al administrador.", icon=":material/close:")
                logger.critical(f"Error crítico en el widget de registro: {e}")
                st.stop()

        with tab3:
            st.markdown("### Recuperación de Acceso")
            
            recovery_option = st.radio(
                "¿Qué necesita recuperar?",
                ["Contraseña", "Nombre de Usuario"]
            )
            
            if recovery_option == "Contraseña":
                st.info("Ingrese su nombre de usuario para recibir una nueva contraseña.", icon=":material/info:")
                
                username, email, new_password = auth_manager.forgot_password(location='main', send_email=True)
                
                if username:
                    st.success(
                        f"""
                        Nueva contraseña generada exitosamente para el usuario **{username}**, la misma ha sido enviada a la dirección de email asociada a la cuenta.
                        """,
                        icon=":material/check_circle:"
                    )
                elif username is False:
                    st.error("Usuario inexistente. Verifique e intente nuevamente.", icon=":material/close:")

            else:  # Recuperar nombre de usuario
                st.info("Ingrese su email para recuperar su nombre de usuario.", icon=":material/info:")
                
                username, email = auth_manager.forgot_username(location='main', send_email=True)
                
                if username:
                    st.success(
                        f"""
                        Usuario encontrado! Nombre de usuario enviado a: **{email}**
                        """,
                        icon=":material/check_circle:"
                    )
                elif username is False:
                    st.error("No se encontró ningún usuario con ese email.", icon=":material/close:")


@log_execution(log_args=False)
def show_home_page():
    """Muestra la página principal para usuarios autenticados."""
    authenticated_menu()
    # Obtener información del usuario
    username = st.session_state.get('username')
    name = st.session_state.get('name', username)
    roles = st.session_state.get('roles', [])
    email = st.session_state.get('email', '')
    
    audit_logger.log_data_access(
        user=username,
        resource='home_page',
        action='view'
    )

    # Header de bienvenida
    st.markdown(f"""
    <div class="welcome-card">
        <h1>¡Bienvenido/a, {name}!</h1>
        <p>Has iniciado sesión exitosamente en el Portal de Informes de la SICyT</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")
    # Información del usuario y métricas
    col1, col2, col3, col4, col5 = st.columns([1, 3, .5, 3, 1])

    with col2:
        st.metric("Usuario", username, delta=None, border=True)
        st.metric("Email", email if email else "No especificado", delta=None, border=True)
    
    with col4:
        role_display = ", ".join(roles) if roles else "Sin roles"
        st.metric("Roles", role_display, delta=None, border=True)
        st.metric("Estado", "☑︎ Activo", delta=None, border=True)
    
    st.markdown("---")
    
    # Secciones disponibles basadas en roles
    st.subheader(":material/space_dashboard: Secciones Disponibles")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 Fichas Provinciales</h3>
            <p>Acceda a información detallada y estadísticas de cada provincia.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Ir a Fichas Provinciales", use_container_width=True):
            st.switch_page("pages/1_fichas_provinciales.py")

    with col2:
        if auth_manager.has_role('admin'):
            st.markdown("""
            <div class="feature-card">
                <h3>🪪 Administración de Usuarios</h3>
                <p>Gestione usuarios, roles y permisos del sistema.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Ir a Administración", use_container_width=True):
                st.switch_page("pages/98_admin_usuarios.py")

    # Novedades y actualizaciones
    st.markdown("---")
    st.subheader(":material/newsmode: Novedades y Actualizaciones")
    
    with st.container():
        st.markdown("""
        <div class="welcome-card">
            <h4>Últimas Actualizaciones del Sistema</h4>
            <ul>
                <li>✨ <strong>Nueva interfaz de usuario:</strong> Diseño mejorado y más intuitivo</li>
                <li>🔐 <strong>Sistema de autenticación actualizado:</strong> Mayor seguridad y facilidad de uso</li>
                <li>📊 <strong>Nuevos indicadores provinciales:</strong> Más datos disponibles para análisis</li>
                <li>📱 <strong>Mejoras en responsividad:</strong> Mejor experiencia en dispositivos móviles</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer con información
    st.markdown("---")
    with st.expander("Información del Sistema", icon=":material/info:"):
        st.markdown("""
        ### Portal de Informes - SICyT
        
        - **Versión:** 1.0.0
        - **Última actualización:** Septiembre 2025
        - **Desarrollado por:** Dirección Nacional de Informes y Estudios
        
        ### Soporte Técnico
        
        Para asistencia técnica o consultas sobre el sistema:
        - 📧 Email: dgicyt@sicyt.gob.ar
        
        ### Recursos Útiles
        
        - [Manual de Usuario](/)
        - [Preguntas Frecuentes](/)
        - [Reportar un Problema](/)
        """)

    # Acciones rápidas en el sidebar
    with st.sidebar:
        # Botón de logout
        auth_manager.logout(location='sidebar', key='logout_main')


# MAIN APP LOGIC
@log_streamlit_component('inicio_main')
def main():
    """Función principal de la aplicación."""
    try:
        auth_manager.login(location='unrendered')
        # Verificar estado de autenticación
        if not st.session_state.get('authentication_status'):
            show_login_page()
        else:
            show_home_page()
    except Exception as e:
        st.error("Error inesperado en la aplicación. Por favor, contacte al administrador.", icon=":material/close:")
        logger.critical(f"Error crítico en la función main_page: {e}")
        st.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Error en la aplicación.", icon=":material/close:")
        st.info("Por favor, recargue la página o contacte al administrador si el problema persiste.", icon=":material/info:")
        logger.critical(f"Error crítico en la ejecución principal: {e}")
