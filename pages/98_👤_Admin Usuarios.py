"""
Página administrativa para gestión de usuarios del sistema.
Solo accesible para usuarios con rol 'admin'.
"""

import streamlit as st
from usuarios import backup_restore_users
from css_utils import load_css

# Configuración de página
st.set_page_config(
    page_title="Gestión de Usuarios - Portal SICyT",
    page_icon=st.secrets.get("LOGO_CORTO", "👥"),
    layout="wide"
)
st.logo(image=st.secrets.get("LOGO_LARGO", ""), size="large")

# CSS
icon_css = load_css("static/iconos/dist/css/icono-arg.css")
custom_css = """
    div[data-testid="stMetricValue"] > div {
        color: #354B6E;
    }
    div[data-testid="stMetricDelta"] > div {
        color: #FFFFFF;
    }
    .user-card {
        background: linear-gradient(90deg, #4D7AAE 0%, #354B6E 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    .admin-warning {
        border-left: 4px solid #ff6b6b;
        padding: 1rem;
        background-color: #fff5f5;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        border-left: 4px solid #51cf66;
        padding: 1rem;
        background-color: #f3f9f3;
        border-radius: 5px;
        margin: 1rem 0;
    }
"""

combined_css = f"""
<style>
{icon_css}
{custom_css}
</style>
"""

st.markdown(combined_css, unsafe_allow_html=True)


def main():
    """Función principal de la página de administración de usuarios"""
    
    # Header
    col1, col2 = st.columns([1, 9], vertical_alignment='center')
    
    with col1:
        st.markdown("""
            <div class="icon-container">
                <i class="icono-arg-usuario" style="font-size: 60px;"></i>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.header("Gestión de Usuarios del Sistema")
        st.write("Panel administrativo para la gestión completa de usuarios")
    
    st.markdown("---")
    
    # Verificar autenticación
    try:
        authenticator = st.session_state.get('authenticator')
        if not authenticator:
            st.warning("⚠️ Debe estar logueado para acceder a esta información.")
            st.stop()
        
        # Verificar si está autenticado
        if not st.session_state.get("authentication_status"):
            st.warning("⚠️ Debe estar logueado para acceder a esta información.")
            st.stop()
        
        # Verificar permisos de administrador
        user_roles = st.session_state.get("roles", [])
        if "admin" not in user_roles:
            st.error("🔒 **Acceso Denegado**")
            st.error("Esta sección requiere permisos de administrador.")
            
            st.markdown("""
            <div class="admin-warning">
                <h4>⚠️ Permisos Insuficientes</h4>
                <p>Su cuenta actual no tiene los permisos necesarios para acceder a la gestión de usuarios.</p>
                <p><strong>Roles actuales:</strong> {}</p>
                <p><strong>Rol requerido:</strong> admin</p>
                <p>Contacte al administrador del sistema si necesita acceso a esta funcionalidad.</p>
            </div>
            """.format(', '.join(user_roles) if user_roles else 'Ninguno'), unsafe_allow_html=True)

            st.stop()
        
        # Si llegamos aquí, el usuario tiene permisos de admin
        show_admin_panel()
        
    except KeyError:
        st.warning("⚠️ Debe estar logueado para acceder a esta información.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error del sistema: {e}")
        st.stop()


def show_admin_panel():
    """Muestra el panel administrativo completo"""
    
    # Información del admin actual
    st.markdown(f"""
    <div class="success-box">
        <h4>✅ Acceso Autorizado</h4>
        <p><strong>Administrador:</strong> {st.session_state.get('name', 'N/A')}</p>
        <p><strong>Usuario:</strong> {st.session_state.get('username', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Gestión de Usuarios",
        "📊 Estadísticas",
        "💾 Respaldo y Restauración",
        "⚙️ Configuración"
    ])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_user_statistics()
    
    with tab3:
        show_backup_restore()
    
    with tab4:
        show_system_config()


def show_user_management():
    """Muestra la sección de gestión de usuarios"""
    st.subheader("👥 Gestión de Usuarios")
    
    # Usar la función existente pero con mejoras visuales
    if 'user_manager' not in st.session_state:
        from usuarios import UserManager
        st.session_state.user_manager = UserManager()
    
    user_manager = st.session_state.user_manager
    users = user_manager.config["credentials"]["usernames"]
    
    if not users:
        st.info("📝 No hay usuarios registrados en el sistema")
        return
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = len(users)
    active_users = sum(1 for user_data in users.values() if user_data.get('logged_in', False))
    admin_users = sum(1 for user_data in users.values() if 'admin' in user_data.get('roles', []))
    locked_users = sum(1 for user_data in users.values() if user_data.get('failed_login_attempts', 0) >= 3)
    
    with col1:
        st.metric("👥 Total Usuarios", total_users)
    with col2:
        st.metric("✅ Conectados", active_users)
    with col3:
        st.metric("🛡️ Administradores", admin_users)
    with col4:
        st.metric("🔒 Bloqueados", locked_users)
    
    st.markdown("---")
    
    # Filtros y búsqueda
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Buscar usuario", placeholder="Nombre de usuario o email...")
    with col2:
        role_filter = st.selectbox("🛡️ Filtrar por rol", ["Todos", "admin", "director", "usuario"])
    with col3:
        status_filter = st.selectbox("📊 Filtrar por estado", ["Todos", "Activos", "Inactivos", "Bloqueados"])
    
    # Filtrar usuarios
    filtered_users = filter_users(users, search_term, role_filter, status_filter)
    
    # Mostrar usuarios filtrados
    if filtered_users:
        st.markdown(f"### Usuarios encontrados: {len(filtered_users)}")
        
        for username, user_data in filtered_users.items():
            show_user_card(username, user_data, user_manager)
    else:
        st.info("🔍 No se encontraron usuarios que coincidan con los filtros")
    
    # Acciones masivas
    st.markdown("---")
    st.subheader("🔧 Acciones Masivas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔓 Resetear todos los intentos fallidos", type="secondary"):
            count = 0
            for username in users:
                if users[username].get('failed_login_attempts', 0) > 0:
                    users[username]['failed_login_attempts'] = 0
                    count += 1
            
            if count > 0 and user_manager._save_config():
                st.success(f"✅ Se resetearon {count} usuarios bloqueados")
                st.rerun()
            elif count == 0:
                st.info("ℹ️ No hay usuarios con intentos fallidos")
    
    with col2:
        if st.button("🚪 Cerrar todas las sesiones", type="secondary"):
            count = 0
            for username in users:
                if users[username].get('logged_in', False):
                    users[username]['logged_in'] = False
                    count += 1
            
            if count > 0 and user_manager._save_config():
                st.success(f"✅ Se cerraron {count} sesiones activas")
                st.rerun()
            elif count == 0:
                st.info("ℹ️ No hay sesiones activas para cerrar")
    
    with col3:
        st.markdown("**⚠️ Zona peligrosa**")
        if st.button("🗑️ Limpiar usuarios inactivos", type="secondary"):
            show_cleanup_dialog()


def filter_users(users, search_term, role_filter, status_filter):
    """Filtra usuarios según los criterios especificados"""
    filtered = {}
    
    for username, user_data in users.items():
        # Filtro de búsqueda
        if search_term:
            search_lower = search_term.lower()
            if not (
                search_lower in username.lower() or
                search_lower in user_data.get('email', '').lower() or
                search_lower in f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".lower()
            ):
                continue
        
        # Filtro de rol
        if role_filter != "Todos":
            user_roles = user_data.get('roles', [])
            if role_filter not in user_roles:
                continue
        
        # Filtro de estado
        if status_filter != "Todos":
            failed_attempts = user_data.get('failed_login_attempts', 0)
            is_active = user_data.get('logged_in', False)
            
            if status_filter == "Activos" and not is_active:
                continue
            elif status_filter == "Inactivos" and is_active:
                continue
            elif status_filter == "Bloqueados" and failed_attempts < 3:
                continue
        
        filtered[username] = user_data
    
    return filtered


def show_user_card(username, user_data, user_manager):
    """Muestra una tarjeta individual de usuario"""
    # Determinar estado del usuario
    failed_attempts = user_data.get('failed_login_attempts', 0)
    is_logged_in = user_data.get('logged_in', False)
    is_blocked = failed_attempts >= 3
    
    # Determinar color del estado
    if is_blocked:
        status_color = "🔴"
        status_text = "Bloqueado"
    elif is_logged_in:
        status_color = "🟢"
        status_text = "Conectado"
    else:
        status_color = "🟡"
        status_text = "Desconectado"
    
    # Crear la tarjeta
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"""
            **👤 {username}**
            {user_data.get('first_name', '')} {user_data.get('last_name', '')}
            ✉️ {user_data.get('email', 'No especificado')}
            """)
        
        with col2:
            st.markdown(f"""
            **Estado:** {status_color} {status_text}
            **Roles:** {', '.join(user_data.get('roles', ['usuario']))}
            **Intentos fallidos:** {failed_attempts}
            """)
        
        with col3:
            # Acciones individuales
            if st.button("🔓 Resetear", key=f"reset_{username}", disabled=(failed_attempts == 0)):
                user_data['failed_login_attempts'] = 0
                if user_manager._save_config():
                    st.success(f"✅ Intentos reseteados para {username}")
                    st.rerun()
            
            if st.button("🚪 Cerrar sesión", key=f"logout_{username}", disabled=(not is_logged_in)):
                user_data['logged_in'] = False
                if user_manager._save_config():
                    st.success(f"✅ Sesión cerrada para {username}")
                    st.rerun()
        
        with col4:
            # Acciones avanzadas
            if st.button("✏️ Editar", key=f"edit_{username}"):
                st.session_state[f"editing_{username}"] = True
                st.rerun()
            
            if username != st.session_state["username"]:  # No permitir auto-eliminación
                if st.button("🗑️ Eliminar", key=f"delete_{username}", type="secondary"):
                    st.session_state[f"confirm_delete_{username}"] = True
                    st.rerun()
            else:
                st.info("👤 Tu cuenta")
        
        # Formularios de edición y confirmación
        if st.session_state.get(f"editing_{username}"):
            show_edit_user_form(username, user_data, user_manager)
        
        if st.session_state.get(f"confirm_delete_{username}"):
            show_delete_confirmation(username, user_manager)
        
        st.markdown("---")


def show_edit_user_form(username, user_data, user_manager):
    """Muestra formulario de edición de usuario"""
    st.subheader(f"✏️ Editando usuario: {username}")
    
    with st.form(f"edit_form_{username}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", value=user_data.get('email', ''))
            new_first_name = st.text_input("Nombre", value=user_data.get('first_name', ''))
        
        with col2:
            new_last_name = st.text_input("Apellido", value=user_data.get('last_name', ''))
            available_roles = ["usuario", "director", "admin"]
            current_roles = user_data.get('roles', ['usuario'])
            new_roles = st.multiselect("Roles", available_roles, default=current_roles)
        
        # Botones del formulario
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("✅ Guardar cambios"):
                # Validar email
                import re
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
                    st.error("❌ Formato de email inválido")
                else:
                    # Actualizar datos
                    user_data.update({
                        'email': new_email,
                        'first_name': new_first_name,
                        'last_name': new_last_name,
                        'roles': new_roles if new_roles else ['usuario']
                    })
                    
                    if user_manager._save_config():
                        st.success(f"✅ Usuario {username} actualizado")
                        del st.session_state[f"editing_{username}"]
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar cambios")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                del st.session_state[f"editing_{username}"]
                st.rerun()
        
        with col3:
            if st.form_submit_button("🔐 Resetear contraseña"):
                # Generar nueva contraseña temporal
                import secrets
                import string
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(12))
                
                # Actualizar contraseña
                from streamlit_authenticator import Hasher
                hashed_password = Hasher([temp_password]).generate()[0]
                user_data['password'] = hashed_password
                user_data['failed_login_attempts'] = 0
                
                if user_manager._save_config():
                    st.success(f"✅ Nueva contraseña para {username}: `{temp_password}`")
                    st.info("⚠️ Comparta esta contraseña de forma segura con el usuario")
                else:
                    st.error("❌ Error al resetear contraseña")


def show_delete_confirmation(username, user_manager):
    """Muestra confirmación de eliminación"""
    st.error(f"⚠️ ¿Está seguro de eliminar al usuario **{username}**?")
    st.warning("Esta acción no se puede deshacer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirmar eliminación", key=f"confirm_delete_yes_{username}", type="primary"):
            del user_manager.config["credentials"]["usernames"][username]
            if user_manager._save_config():
                st.success(f"✅ Usuario {username} eliminado")
                del st.session_state[f"confirm_delete_{username}"]
                st.rerun()
            else:
                st.error("❌ Error al eliminar usuario")
    
    with col2:
        if st.button("❌ Cancelar", key=f"confirm_delete_no_{username}"):
            del st.session_state[f"confirm_delete_{username}"]
            st.rerun()


def show_cleanup_dialog():
    """Muestra diálogo de limpieza de usuarios"""
    if 'show_cleanup_dialog' not in st.session_state:
        st.session_state.show_cleanup_dialog = True
    
    if st.session_state.get('show_cleanup_dialog'):
        st.error("⚠️ **ATENCIÓN: Operación Destructiva**")
        st.warning("Se eliminarán usuarios que cumplan TODOS estos criterios:")
        st.write("- No han iniciado sesión nunca (`logged_in: false`)")
        st.write("- Tienen intentos fallidos de login")
        st.write("- No son administradores")
        st.write("- No son el usuario actual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Confirmar limpieza", type="primary"):
                count = perform_user_cleanup()
                st.session_state.show_cleanup_dialog = False
                st.success(f"✅ Se eliminaron {count} usuarios inactivos")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.show_cleanup_dialog = False
                st.rerun()


def perform_user_cleanup():
    """Realiza la limpieza de usuarios inactivos"""
    if 'user_manager' not in st.session_state:
        return 0
    
    user_manager = st.session_state.user_manager
    users = user_manager.config["credentials"]["usernames"]
    current_user = st.session_state["username"]
    
    users_to_delete = []
    
    for username, user_data in users.items():
        if (
            username != current_user and  # No eliminar usuario actual
            not user_data.get('logged_in', False) and  # No conectados
            user_data.get('failed_login_attempts', 0) > 0 and  # Con intentos fallidos
            'admin' not in user_data.get('roles', [])  # No administradores
        ):
            users_to_delete.append(username)
    
    # Eliminar usuarios
    for username in users_to_delete:
        del users[username]
    
    if users_to_delete and user_manager._save_config():
        return len(users_to_delete)
    return 0


def show_user_statistics():
    """Muestra estadísticas detalladas de usuarios"""
    st.subheader("📊 Estadísticas del Sistema")
    
    if 'user_manager' not in st.session_state:
        from usuarios import UserManager
        st.session_state.user_manager = UserManager()
    
    users = st.session_state.user_manager.config["credentials"]["usernames"]
    
    if not users:
        st.info("📝 No hay datos para mostrar estadísticas")
        return
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = len(users)
    active_sessions = sum(1 for user_data in users.values() if user_data.get('logged_in', False))
    failed_attempts = sum(user_data.get('failed_login_attempts', 0) for user_data in users.values())
    blocked_users = sum(1 for user_data in users.values() if user_data.get('failed_login_attempts', 0) >= 3)
    
    with col1:
        st.metric("👥 Total de Usuarios", total_users)
    with col2:
        st.metric("🟢 Sesiones Activas", active_sessions)
    with col3:
        st.metric("🔴 Intentos Fallidos", failed_attempts)
    with col4:
        st.metric("🔒 Usuarios Bloqueados", blocked_users)
    
    st.markdown("---")
    
    # Distribución por roles
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛡️ Distribución por Roles")
        
        role_counts = {}
        for user_data in users.values():
            for role in user_data.get('roles', ['usuario']):
                role_counts[role] = role_counts.get(role, 0) + 1
        
        if role_counts:
            import plotly.express as px
            import pandas as pd
            
            df_roles = pd.DataFrame(list(role_counts.items()), columns=['Rol', 'Cantidad'])
            fig = px.pie(df_roles, values='Cantidad', names='Rol', title="Usuarios por Rol")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de roles para mostrar")
    
    with col2:
        st.subheader("📈 Estado de Cuentas")
        
        estados = {
            'Activos': sum(1 for user_data in users.values() if user_data.get('logged_in', False)),
            'Inactivos': sum(1 for user_data in users.values() if not user_data.get('logged_in', False) and user_data.get('failed_login_attempts', 0) < 3),
            'Bloqueados': sum(1 for user_data in users.values() if user_data.get('failed_login_attempts', 0) >= 3)
        }
        
        if any(estados.values()):
            import plotly.express as px
            import pandas as pd
            
            df_estados = pd.DataFrame(list(estados.items()), columns=['Estado', 'Cantidad'])
            fig = px.bar(df_estados, x='Estado', y='Cantidad', title="Estado de las Cuentas")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de estado para mostrar")
    
    # Tabla detallada
    st.subheader("📋 Resumen Detallado")
    
    detailed_data = []
    for username, user_data in users.items():
        detailed_data.append({
            "Usuario": username,
            "Nombre Completo": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            "Email": user_data.get('email', ''),
            "Roles": ', '.join(user_data.get('roles', ['usuario'])),
            "Estado": "🟢 Activo" if user_data.get('logged_in', False) else ("🔴 Bloqueado" if user_data.get('failed_login_attempts', 0) >= 3 else "🟡 Inactivo"),
            "Intentos Fallidos": user_data.get('failed_login_attempts', 0)
        })
    
    if detailed_data:
        import pandas as pd
        df_detailed = pd.DataFrame(detailed_data)
        st.dataframe(df_detailed, use_container_width=True, hide_index=True)


def show_backup_restore():
    """Muestra opciones de respaldo y restauración"""
    st.subheader("💾 Respaldo y Restauración")
    
    # Usar la función existente
    backup_restore_users()


def show_system_config():
    """Muestra configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")
    
    if 'user_manager' not in st.session_state:
        from usuarios import UserManager
        st.session_state.user_manager = UserManager()
    
    user_manager = st.session_state.user_manager
    
    # Configuración de cookies
    st.markdown("### 🍪 Configuración de Cookies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_expiry = user_manager.config["cookie"]["expiry_days"]
        new_expiry = st.number_input(
            "Días de expiración de cookies",
            value=float(current_expiry),
            min_value=0.1,
            max_value=365.0,
            step=0.1
        )
        
        current_name = user_manager.config["cookie"]["name"]
        new_name = st.text_input("Nombre de la cookie", value=current_name)
    
    with col2:
        st.info(f"""
        **Configuración actual:**
        - Nombre: {current_name}
        - Expiración: {current_expiry} días
        - Clave: {'*' * len(user_manager.config["cookie"]["key"])}
        """)
        
        if st.button("🔄 Generar nueva clave de cookie"):
            import secrets
            new_key = secrets.token_urlsafe(16)
            user_manager.config["cookie"]["key"] = new_key
            if user_manager._save_config():
                st.success("✅ Nueva clave generada")
                st.warning("⚠️ Todos los usuarios deberán volver a iniciar sesión")
                st.rerun()
    
    if st.button("💾 Guardar configuración de cookies"):
        user_manager.config["cookie"]["expiry_days"] = new_expiry
        user_manager.config["cookie"]["name"] = new_name
        
        if user_manager._save_config():
            st.success("✅ Configuración guardada")
            st.rerun()
        else:
            st.error("❌ Error al guardar configuración")
    
    st.markdown("---")
    
    # Configuración de seguridad
    st.markdown("### 🔐 Configuración de Seguridad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Políticas de contraseña:**")
        st.write("- Mínimo 8 caracteres")
        st.write("- Al menos una mayúscula")
        st.write("- Al menos una minúscula")
        st.write("- Al menos un número")
        
        # max_attempts = st.number_input(
        #     "Máximo intentos fallidos antes de bloqueo",
        #     value=3, min_value=1, max_value=10
        # )
    
    with col2:
        st.markdown("**Configuración actual:**")
        blocked_users = sum(
            1 for user_data in user_manager.config["credentials"]["usernames"].values()
            if user_data.get('failed_login_attempts', 0) >= 3
        )
        st.write(f"- Usuarios bloqueados: {blocked_users}")
        st.write(f"- Total de usuarios: {len(user_manager.config['credentials']['usernames'])}")
        
        if st.button("🔓 Desbloquear todos los usuarios"):
            count = 0
            for user_data in user_manager.config["credentials"]["usernames"].values():
                if user_data.get('failed_login_attempts', 0) >= 3:
                    user_data['failed_login_attempts'] = 0
                    count += 1
            
            if count > 0 and user_manager._save_config():
                st.success(f"✅ Se desbloquearon {count} usuarios")
                st.rerun()
            else:
                st.info("ℹ️ No había usuarios bloqueados")
    
    st.markdown("---")
    
    # Información del sistema
    st.markdown("### ℹ️ Información del Sistema")
    
    import streamlit as st
    from datetime import datetime
    
    system_info = {
        "Versión de Streamlit": st.__version__,
        "Archivo de configuración": str(user_manager.credentials_path),
        "Total de usuarios": len(user_manager.config["credentials"]["usernames"]),
        "Sesiones activas": sum(1 for user_data in user_manager.config["credentials"]["usernames"].values() if user_data.get('logged_in', False)),
        "Fecha actual": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}:** {value}")


if __name__ == "__main__":
    main()
