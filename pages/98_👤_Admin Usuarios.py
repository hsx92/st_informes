"""Streamlit page for user administration.

This module provides user management functionality including creating,
updating, and deleting users with role-based access control.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
from pathlib import Path
import logging
from functools import wraps
from typing import Optional, Dict, Any
from css_utils import load_css, get_metric_css

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Decorador para logging
def log_action(action_name: str):
    """Decorator to log user actions with context."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = st.session_state.get("username", "unknown")
            logger.info(f"User '{user}' initiated action: {action_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Action '{action_name}' completed successfully by user '{user}'")
                return result
            except Exception as e:
                logger.error(f"Action '{action_name}' failed for user '{user}': {str(e)}")
                raise
        return wrapper
    return decorator


# Configuración de la página
st.set_page_config(
    page_title="Admin Usuarios - SICyT",
    page_icon=st.secrets["LOGO_CORTO"],
    layout="wide"
)
st.logo(image=st.secrets["LOGO_LARGO"], size="large")

# ---- CSS ----
icon_css = load_css("static/iconos/dist/css/icono-arg.css")
metric_css = get_metric_css("dark")  # Usar tema oscuro para mejor contraste

combined_css = f"""
<style>
{icon_css}
{metric_css}
/* Estilos adicionales para formularios */
div.stButton > button {{
    background-color: #54698B;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-weight: 500;
    transition: background-color 0.3s;
}}
div.stButton > button:hover {{
    background-color: #7589A3;
}}
/* Mejor visibilidad para mensajes de éxito/error */
.stSuccess, .stError, .stWarning {{
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
}}
</style>
"""

st.markdown(combined_css, unsafe_allow_html=True)


# ---- FUNCIONES AUXILIARES ----

def load_config() -> Dict[str, Any]:
    """Load authentication configuration from YAML file.
    
    Returns:
        Dictionary containing authentication configuration.
    """
    try:
        credentials_path = Path(__file__).parent.parent / ".streamlit" / "credentials.yaml"
        with credentials_path.open("r", encoding="utf-8") as file:
            config = yaml.load(file, Loader=SafeLoader)
            logger.info("Configuration loaded successfully")
            return config
    except FileNotFoundError:
        logger.error("Credentials file not found")
        st.error("Error: No se encontró el archivo de configuración")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        st.error(f"Error al cargar la configuración: {str(e)}")
        return {}


@log_action("save_configuration")
def save_config(config: Dict[str, Any]) -> bool:
    """Save authentication configuration to YAML file.
    
    Args:
        config: Dictionary containing authentication configuration.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        credentials_path = Path(__file__).parent.parent / ".streamlit" / "credentials.yaml"
        with credentials_path.open("w", encoding="utf-8") as file:
            yaml.dump(config, file, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        st.error(f"Error al guardar la configuración: {str(e)}")
        return False


def get_authenticator(config: Dict[str, Any]) -> Optional[stauth.Authenticate]:
    """Create and return an authenticator instance.
    
    Args:
        config: Authentication configuration dictionary.
        
    Returns:
        Authenticator instance or None if creation fails.
    """
    try:
        return stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )
    except Exception as e:
        logger.error(f"Error creating authenticator: {str(e)}")
        st.error(f"Error al crear el autenticador: {str(e)}")
        return None


@log_action("create_user")
def create_user(config: Dict[str, Any], authenticator: stauth.Authenticate) -> None:
    """Create a new user in the system."""
    st.subheader("➕ Crear nuevo usuario")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Nombre de usuario *")
            new_email = st.text_input("Email *")
            new_first_name = st.text_input("Nombre *")
            new_last_name = st.text_input("Apellido *")
        
        with col2:
            new_password = st.text_input("Contraseña *", type="password")
            new_password_confirm = st.text_input("Confirmar contraseña *", type="password")
            available_roles = ["admin", "director", "viewer"]
            new_roles = st.multiselect("Roles", available_roles, default=["viewer"])
        
        submit = st.form_submit_button("Crear usuario", use_container_width=True)
        
        if submit:
            # Validaciones
            if not all([new_username, new_email, new_first_name, new_last_name, new_password]):
                st.error("Por favor complete todos los campos obligatorios")
                logger.warning("User creation failed: missing required fields")
                return
            
            if new_password != new_password_confirm:
                st.error("Las contraseñas no coinciden")
                logger.warning(f"User creation failed: password mismatch for user {new_username}")
                return
            
            if new_username in config["credentials"]["usernames"]:
                st.error("El nombre de usuario ya existe")
                logger.warning(f"User creation failed: username {new_username} already exists")
                return
            
            try:
                # Hash the password
                hashed_password = stauth.Hasher([new_password]).generate()[0]
                
                # Add new user to config
                config["credentials"]["usernames"][new_username] = {
                    "email": new_email,
                    "first_name": new_first_name,
                    "last_name": new_last_name,
                    "password": hashed_password,
                    "roles": new_roles,
                    "failed_login_attempts": 0,
                    "logged_in": False
                }
                
                # Add to pre-authorized if admin
                if "admin" in new_roles and new_username not in config.get("pre-authorized", []):
                    if "pre-authorized" not in config:
                        config["pre-authorized"] = []
                    config["pre-authorized"].append(new_username)
                
                if save_config(config):
                    st.success(f"Usuario '{new_username}' creado exitosamente")
                    logger.info(f"User '{new_username}' created successfully with roles: {new_roles}")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error al crear el usuario: {str(e)}")
                logger.error(f"Error creating user {new_username}: {str(e)}")


@log_action("update_user")
def update_user(config: Dict[str, Any]) -> None:
    """Update existing user information."""
    st.subheader("✏️ Actualizar usuario")
    
    users = list(config["credentials"]["usernames"].keys())
    selected_user = st.selectbox("Seleccionar usuario", users)
    
    if selected_user:
        user_data = config["credentials"]["usernames"][selected_user]
        
        with st.form("update_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_email = st.text_input("Email", value=user_data.get("email", ""))
                new_first_name = st.text_input("Nombre", value=user_data.get("first_name", ""))
                new_last_name = st.text_input("Apellido", value=user_data.get("last_name", ""))
            
            with col2:
                new_password = st.text_input("Nueva contraseña (dejar vacío para no cambiar)", type="password")
                available_roles = ["admin", "director", "viewer"]
                current_roles = user_data.get("roles", [])
                new_roles = st.multiselect("Roles", available_roles, default=current_roles)
                reset_attempts = st.checkbox("Resetear intentos de login fallidos")
            
            submit = st.form_submit_button("Actualizar usuario", use_container_width=True)
            
            if submit:
                try:
                    # Update user data
                    config["credentials"]["usernames"][selected_user]["email"] = new_email
                    config["credentials"]["usernames"][selected_user]["first_name"] = new_first_name
                    config["credentials"]["usernames"][selected_user]["last_name"] = new_last_name
                    config["credentials"]["usernames"][selected_user]["roles"] = new_roles
                    
                    # Update password if provided
                    if new_password:
                        hashed_password = stauth.Hasher([new_password]).generate()[0]
                        config["credentials"]["usernames"][selected_user]["password"] = hashed_password
                    
                    # Reset login attempts if requested
                    if reset_attempts:
                        config["credentials"]["usernames"][selected_user]["failed_login_attempts"] = 0
                    
                    # Update pre-authorized list
                    if "admin" in new_roles and selected_user not in config.get("pre-authorized", []):
                        if "pre-authorized" not in config:
                            config["pre-authorized"] = []
                        config["pre-authorized"].append(selected_user)
                    elif "admin" not in new_roles and selected_user in config.get("pre-authorized", []):
                        config["pre-authorized"].remove(selected_user)
                    
                    if save_config(config):
                        st.success(f"Usuario '{selected_user}' actualizado exitosamente")
                        logger.info(f"User '{selected_user}' updated successfully")
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al actualizar el usuario: {str(e)}")
                    logger.error(f"Error updating user {selected_user}: {str(e)}")


@log_action("delete_user")
def delete_user(config: Dict[str, Any]) -> None:
    """Delete a user from the system."""
    st.subheader("🗑️ Eliminar usuario")
    
    users = list(config["credentials"]["usernames"].keys())
    current_user = st.session_state.get("username")
    
    # Filter out current user to prevent self-deletion
    deletable_users = [u for u in users if u != current_user]
    
    if not deletable_users:
        st.warning("No hay usuarios disponibles para eliminar")
        return
    
    selected_user = st.selectbox("Seleccionar usuario para eliminar", deletable_users)
    
    if selected_user:
        user_data = config["credentials"]["usernames"][selected_user]
        
        # Show user information
        st.info(f"""
        **Usuario:** {selected_user}
        **Nombre:** {user_data.get('first_name', '')} {user_data.get('last_name', '')}
        **Email:** {user_data.get('email', '')}
        **Roles:** {', '.join(user_data.get('roles', []))}
        """)
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🗑️ Eliminar", type="secondary", use_container_width=True):
                st.session_state.confirm_delete = selected_user
        
        if st.session_state.get("confirm_delete") == selected_user:
            st.warning("⚠️ Esta acción no se puede deshacer. ¿Está seguro?")
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("✅ Confirmar", type="primary", use_container_width=True):
                    try:
                        # Remove user from credentials
                        del config["credentials"]["usernames"][selected_user]
                        
                        # Remove from pre-authorized if present
                        if selected_user in config.get("pre-authorized", []):
                            config["pre-authorized"].remove(selected_user)
                        
                        if save_config(config):
                            st.success(f"Usuario '{selected_user}' eliminado exitosamente")
                            logger.info(f"User '{selected_user}' deleted successfully")
                            del st.session_state.confirm_delete
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar el usuario: {str(e)}")
                        logger.error(f"Error deleting user {selected_user}: {str(e)}")
            
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    del st.session_state.confirm_delete
                    st.rerun()


def show_user_list(config: Dict[str, Any]) -> None:
    """Display a list of all users in the system."""
    st.subheader("👥 Lista de usuarios")
    
    users_data = []
    for username, data in config["credentials"]["usernames"].items():
        users_data.append({
            "Usuario": username,
            "Nombre": f"{data.get('first_name', '')} {data.get('last_name', '')}",
            "Email": data.get("email", ""),
            "Roles": ", ".join(data.get("roles", [])),
            "Intentos fallidos": data.get("failed_login_attempts", 0),
            "Conectado": "✅" if data.get("logged_in", False) else "❌"
        })
    
    if users_data:
        st.dataframe(users_data, use_container_width=True, hide_index=True)
        
        # Mostrar estadísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de usuarios", len(users_data))
        
        with col2:
            admin_count = sum(1 for u in users_data if "admin" in u["Roles"])
            st.metric("Administradores", admin_count)
        
        with col3:
            director_count = sum(1 for u in users_data if "director" in u["Roles"])
            st.metric("Directores", director_count)
        
        with col4:
            connected_count = sum(1 for u in users_data if u["Conectado"] == "✅")
            st.metric("Usuarios conectados", connected_count)
    else:
        st.info("No hay usuarios registrados en el sistema")


# ---- PÁGINA PRINCIPAL ----

def main():
    """Main function for the user administration page."""
    
    # Verificar autenticación
    if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
        st.warning("⚠️ Debe estar logueado para acceder a esta información.")
        logger.warning("Unauthenticated access attempt to admin page")
        st.stop()
    
    # Verificar permisos de admin
    user_roles = st.session_state.get("roles", [])
    if "admin" not in user_roles:
        st.error("🚫 Acceso no autorizado. Se requieren permisos de administrador.")
        logger.warning(f"Unauthorized access attempt by user: {st.session_state.get('username', 'unknown')}")
        st.stop()
    
    # Header
    col1, col2 = st.columns([1, 9], vertical_alignment='center')
    with col1:
        st.markdown("""
            <div class="icon-container">
                <i class="icono-arg-usuarios" style="font-size: 60px; color: #E3E7ED;"></i>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        st.header("Administración de Usuarios")
        st.write("Gestión de usuarios del sistema")
    
    st.markdown("---")
    
    # Log successful access
    logger.info(f"Admin page accessed by user: {st.session_state.get('username', 'unknown')}")
    
    # Cargar configuración
    config = load_config()
    
    if not config:
        st.error("No se pudo cargar la configuración del sistema")
        return
    
    authenticator = get_authenticator(config)
    
    if not authenticator:
        st.error("No se pudo inicializar el sistema de autenticación")
        return
    
    # Tabs para las diferentes funciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Lista de usuarios",
        "➕ Crear usuario",
        "✏️ Actualizar usuario",
        "🗑️ Eliminar usuario"
    ])
    
    with tab1:
        show_user_list(config)
    
    with tab2:
        create_user(config, authenticator)
    
    with tab3:
        update_user(config)
    
    with tab4:
        delete_user(config)
    
    # Footer con información del usuario actual
    st.markdown("---")
    current_user = st.session_state.get("username", "unknown")
    st.caption(f"🔒 Sesión activa: {current_user} | Rol: {', '.join(user_roles)}")
    
    # Botón de logout
    if st.button("🚪 Cerrar sesión", type="secondary"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()
