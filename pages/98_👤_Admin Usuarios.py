"""
Página de administración de usuarios utilizando streamlit-authenticator correctamente.
"""

import streamlit as st
import pandas as pd
import time
from auth_manager import get_auth_manager
from css_utils import load_css
from logging_config import get_logger

logger = get_logger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Administración de Usuarios - SICyT",
    page_icon=st.secrets.get("LOGO_CORTO", "🔐"),
    layout="wide"
)

st.logo(image=st.secrets.get('LOGO_LARGO', ''), size="large")

# Cargar CSS
icon_css = load_css("static/iconos/dist/css/icono-arg.css") if st.secrets.get("USE_ICONS", False) else ""
combined_css = f"""
<style>
{icon_css}
/* Estilos personalizados para la página de admin */
.user-card {{
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}}
.role-badge {{
    background-color: #354B6E;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    margin-right: 0.25rem;
    display: inline-block;
}}
</style>
"""
st.markdown(combined_css, unsafe_allow_html=True)

# Inicializar AuthManager
auth_manager = get_auth_manager()
auth_manager.require_role('admin')

# Header
col1, col2 = st.columns([1, 9], vertical_alignment='center')
with col1:
    if st.secrets.get("USE_ICONS", False):
        st.markdown("""
            <div class="icon-container">
                <i class="icono-arg-usuarios" style="font-size: 60px;"></i>
            </div>
            """, unsafe_allow_html=True)
with col2:
    st.header("Administración de Usuarios")
    st.write("Gestión completa de usuarios del sistema")

st.markdown("---")

# Tabs para diferentes funcionalidades
tabs = st.tabs([
    "👥 Lista de Usuarios",
    "➕ Nuevo Usuario",
    "✏️ Editar Usuario",
    "🔑 Gestión de Contraseñas",
    "🎭 Gestión de Roles",
    "📊 Estadísticas"
])

# Tab 1: Lista de Usuarios
with tabs[0]:
    st.subheader("Usuarios del Sistema")
    
    # Obtener todos los usuarios
    users = auth_manager.get_all_users()
    
    if users:
        # Crear DataFrame para mostrar usuarios
        user_data = []
        for username, info in users.items():
            user_data.append({
                'Usuario': username,
                'Nombre': f"{info.get('first_name', '')} {info.get('last_name', '')}".strip() or info.get('name', 'N/A'),
                'Email': info.get('email', 'N/A'),
                'Roles': ', '.join(info.get('roles', [])) if info.get('roles') else 'Sin roles',
                'Sesión Activa': '✅' if info.get('logged_in', False) else '❌',
                'Intentos Fallidos': info.get('failed_login_attempts', 0)
            })
        
        df_users = pd.DataFrame(user_data)
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            search_user = st.text_input("🔍 Buscar usuario", placeholder="Nombre o email...")
        with col2:
            filter_role = st.selectbox("Filtrar por rol", ["Todos"] + list(set(
                role for user in users.values()
                for role in user.get('roles', [])
            )))
        with col3:
            show_active = st.checkbox("Solo usuarios activos", value=False)
        
        # Aplicar filtros
        if search_user:
            mask = (
                df_users['Usuario'].str.contains(search_user, case=False) |
                df_users['Email'].str.contains(search_user, case=False) |
                df_users['Nombre'].str.contains(search_user, case=False)
            )
            df_users = df_users[mask]
        
        if filter_role != "Todos":
            df_users = df_users[df_users['Roles'].str.contains(filter_role)]
        
        if show_active:
            df_users = df_users[df_users['Sesión Activa'] == '✅']
        
        # Mostrar tabla
        st.dataframe(
            df_users,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sesión Activa": st.column_config.TextColumn("Sesión Activa", width="small"),
                "Intentos Fallidos": st.column_config.NumberColumn("Intentos Fallidos", width="small")
            }
        )
        
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Usuarios", len(users))
        with col2:
            active_users = sum(1 for u in users.values() if u.get('logged_in', False))
            st.metric("Usuarios Activos", active_users)
        with col3:
            admin_count = sum(1 for u in users.values() if 'admin' in u.get('roles', []))
            st.metric("Administradores", admin_count)
        with col4:
            blocked_users = sum(1 for u in users.values() if u.get('failed_login_attempts', 0) >= 5)
            st.metric("Usuarios Bloqueados", blocked_users)
    else:
        st.info("No hay usuarios registrados en el sistema.")

# Tab 2: Nuevo Usuario
with tabs[1]:
    st.subheader("Registrar Nuevo Usuario")
    
    # Configuración de roles disponibles
    available_roles = ['viewer', 'editor', 'director', 'admin']
    
    # Formulario de registro usando el widget de streamlit-authenticator
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Complete el formulario para registrar un nuevo usuario.")
        
        # Roles para el nuevo usuario
        selected_roles = st.multiselect(
            "Roles del usuario",
            available_roles,
            default=['viewer'],
            help="Seleccione los roles que tendrá el nuevo usuario"
        )
        
        # Widget de registro
        email, username, name = auth_manager.register_user(
            location='main',
            pre_authorized=False,
            roles=selected_roles
        )
        
        if email:
            logger.info(f"Nuevo usuario registrado: {username} ({email}) con roles: {selected_roles}. Creado por: {st.session_state.get('username', 'sistema')}")
            st.success(f"✅ Usuario '{username}' registrado exitosamente")
            st.balloons()
    
    with col2:
        st.markdown("### 📋 Instrucciones")
        st.markdown("""
        1. Complete todos los campos requeridos
        2. La contraseña debe cumplir con:
           - Entre 8 y 20 caracteres
           - Al menos una mayúscula
           - Al menos una minúscula
           - Al menos un número
           - Al menos un carácter especial
        3. Asigne los roles apropiados
        4. El usuario recibirá sus credenciales
        """)

# Tab 3: Editar Usuario
with tabs[2]:
    st.subheader("Editar Información de Usuario")
    
    # Selector de usuario
    users_list = list(auth_manager.get_all_users().keys())
    
    if users_list:
        selected_user = st.selectbox(
            "Seleccione un usuario para editar",
            users_list,
            format_func=lambda x: f"{x} - {auth_manager.get_user_info(x).get('email', 'Sin email')}"
        )
        
        if selected_user:
            user_info = auth_manager.get_user_info(selected_user)
            
            col1, col2, col3 = st.columns([1, 3, 1], vertical_alignment='center')
            
            with col2:
                with st.container(border=True):
                    st.markdown("### Información Actual")
                    st.markdown(f"**Usuario:** {selected_user}")
                    st.markdown(f"**Nombre:** {user_info.get('first_name', '')} {user_info.get('last_name', '')}")
                    st.markdown(f"**Email:** {user_info.get('email', 'N/A')}")
                    st.markdown(f"**Roles:** {', '.join(user_info.get('roles', [])) if user_info.get('roles') else 'Sin roles'}")
                    st.markdown(f"**Estado:** {'Activo' if user_info.get('logged_in', False) else 'Inactivo'}")
            
                # Widget para actualizar detalles del usuario
                if st.button(f"Editar detalles de {selected_user}", icon="✏️", use_container_width=True):
                    with st.container():
                        result = auth_manager.update_user_details(selected_user)
                        if result:
                            st.success("✅ Información actualizada exitosamente")
                            time.sleep(1)
                            st.rerun()
            
            # Sección para eliminar usuario
            st.markdown("---")
            st.markdown("### Eliminación de Usuario ⚠️")
            st.warning(f"Eliminar permanentemente al usuario: **{selected_user}**")
            
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                if st.button("🗑️ Eliminar Usuario", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete') != selected_user:
                        st.session_state['confirm_delete'] = selected_user
                        st.error("Presione nuevamente para confirmar, esta acción es irreversible.")
                    else:
                        if auth_manager.delete_user(selected_user):
                            st.success(f"Usuario {selected_user} eliminado")
                            del st.session_state['confirm_delete']
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Error al eliminar usuario")
    else:
        st.info("No hay usuarios para editar")

# Tab 4: Gestión de Contraseñas
with tabs[3]:
    st.subheader("Gestión de Contraseñas")
    
    password_option = st.radio(
        "Seleccione una opción:",
        ["Reset de Contraseña (Usuario Logueado)", "Contraseña Olvidada", "Usuario Olvidado"]
    )
    
    if password_option == "Reset de Contraseña (Usuario Logueado)":
        st.markdown("### Cambiar Contraseña de Usuario Actual")
        
        if st.session_state.get('username'):
            result = auth_manager.reset_password(st.session_state['username'])
            if result:
                st.success("✅ Contraseña actualizada exitosamente")
        else:
            st.warning("No hay usuario logueado actualmente")
    
    elif password_option == "Contraseña Olvidada":
        st.markdown("### Recuperación de Contraseña")
        st.info("Ingrese el nombre de usuario para generar una nueva contraseña")
        
        username, email, new_password = auth_manager.forgot_password(send_email=True)
        
        if username:
            st.success(f"✅ Nueva contraseña generada para {username}, enviada a: {email}")
            with st.expander("Ver detalles"):
                st.code(f"""
                Usuario: {username}
                Email: {email}
                Nueva Contraseña: {new_password}
                """)
                st.warning("⚠️ Comunique esta contraseña al usuario de forma segura")
        elif username is False:
            st.error("Usuario no encontrado")
    
    else:  # Usuario Olvidado
        st.markdown("### Recuperación de Nombre de Usuario")
        st.info("Ingrese el email para recuperar el nombre de usuario")
        
        username, email = auth_manager.forgot_username()
        
        if username:
            st.success("✅ Usuario encontrado")
            with st.expander("Ver detalles"):
                st.code(f"""
                Usuario: {username}
                Email: {email}
                """)
        elif username is False:
            st.error("Email no encontrado")

# Tab 5: Gestión de Roles
with tabs[4]:
    users_list = list(auth_manager.get_all_users().keys())
    
    if users_list:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Gestión de Roles")
    
            selected_user = st.selectbox(
                "Seleccione un usuario",
                users_list,
                key="role_user_select"
            )
            if selected_user:
                user_info = auth_manager.get_user_info(selected_user)
                current_roles = user_info.get('roles', [])
            
            st.markdown("### Roles Actuales")
            if current_roles:
                for role in current_roles:
                    st.badge(role)
            else:
                st.info("Sin roles asignados")

        # Actualización masiva de roles
        st.markdown("---")
        st.markdown("### Actualización de Roles")
        
        new_roles = st.multiselect(
            "Seleccione todos los roles para este usuario",
            ['viewer', 'editor', 'director', 'admin'],
            default=current_roles
        )
        
        if st.button("🔄 Actualizar Roles"):
            if auth_manager.update_user_roles(selected_user, new_roles):
                st.success("Roles actualizados exitosamente")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Error al actualizar roles")
    else:
        st.info("No hay usuarios disponibles")

# Tab 6: Estadísticas
with tabs[5]:
    st.subheader("Estadísticas del Sistema")
    
    users = auth_manager.get_all_users()
    
    if users:
        # Preparar datos para estadísticas
        total_users = len(users)
        active_users = sum(1 for u in users.values() if u.get('logged_in', False))
        failed_attempts = sum(u.get('failed_login_attempts', 0) for u in users.values())
        
        # Conteo por roles
        role_counts = {}
        for user in users.values():
            for role in user.get('roles', []):
                role_counts[role] = role_counts.get(role, 0) + 1
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Usuarios",
                total_users,
                delta=f"{active_users} activos"
            )
        
        with col2:
            st.metric(
                "Tasa de Actividad",
                f"{(active_users/total_users*100):.1f}%" if total_users > 0 else "0%"
            )
        
        with col3:
            st.metric(
                "Intentos Fallidos",
                failed_attempts,
                delta="Total acumulado"
            )
        
        with col4:
            blocked = sum(1 for u in users.values() if u.get('failed_login_attempts', 0) >= 5)
            st.metric(
                "Usuarios Bloqueados",
                blocked,
                delta=f"-{(blocked/total_users*100):.1f}%" if total_users > 0 else "0%"
            )
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Distribución por Roles")
            if role_counts:
                df_roles = pd.DataFrame(
                    list(role_counts.items()),
                    columns=['Rol', 'Cantidad']
                )
                st.bar_chart(df_roles.set_index('Rol'))
            else:
                st.info("No hay roles asignados")
        
        with col2:
            st.markdown("### Estado de Usuarios")
            status_data = {
                'Estado': ['Activos', 'Inactivos', 'Bloqueados'],
                'Cantidad': [
                    active_users,
                    total_users - active_users - blocked,
                    blocked
                ]
            }
            df_status = pd.DataFrame(status_data)
            st.bar_chart(df_status.set_index('Estado'))
        
        # Tabla de actividad reciente
        st.markdown("---")
        st.markdown("### Actividad de Usuarios")
        
        user_activity = []
        for username, info in users.items():
            user_activity.append({
                'Usuario': username,
                'Email': info.get('email', 'N/A'),
                'Estado': '🟢 Activo' if info.get('logged_in', False) else '🔴 Inactivo',
                'Intentos Fallidos': info.get('failed_login_attempts', 0),
                'Roles': len(info.get('roles', []))
            })
        
        df_activity = pd.DataFrame(user_activity)
        
        # Ordenar por intentos fallidos (descendente)
        df_activity = df_activity.sort_values('Intentos Fallidos', ascending=False)
        
        st.dataframe(
            df_activity,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn("Estado", width="small"),
                "Intentos Fallidos": st.column_config.ProgressColumn(
                    "Intentos Fallidos",
                    min_value=0,
                    max_value=10,
                    format="%d"
                ),
                "Roles": st.column_config.NumberColumn("# Roles", width="small")
            }
        )
        
        # Exportar datos
        st.markdown("---")
        st.markdown("### Exportar Datos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df_activity.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Lista de Usuarios (CSV)",
                data=csv,
                file_name='usuarios_sistema.csv',
                mime='text/csv',
            )
        
        with col2:
            # Crear resumen para exportar
            resumen = f"""
RESUMEN DE USUARIOS DEL SISTEMA
================================
Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

ESTADÍSTICAS GENERALES:
- Total de usuarios: {total_users}
- Usuarios activos: {active_users}
- Usuarios bloqueados: {blocked}
- Intentos fallidos totales: {failed_attempts}

DISTRIBUCIÓN POR ROLES:
{chr(10).join(f'- {rol}: {cant} usuarios' for rol, cant in role_counts.items())}

USUARIOS CON MÁS INTENTOS FALLIDOS:
{chr(10).join(f'- {row["Usuario"]}: {row["Intentos Fallidos"]} intentos' for _, row in df_activity.head(5).iterrows())}
            """
            
            st.download_button(
                label="📄 Descargar Resumen (TXT)",
                data=resumen,
                file_name='resumen_usuarios.txt',
                mime='text/plain',
            )
        
        with col3:
            if st.button("🔄 Actualizar Estadísticas"):
                st.rerun()
    else:
        st.info("No hay datos de usuarios para mostrar estadísticas")

# Footer con información adicional
st.markdown("---")
with st.expander("ℹ️ Información del Sistema"):
    st.markdown("""
    ### Roles y Permisos
    
    - **Viewer**: Solo puede ver información
    - **Editor**: Puede ver y editar contenido
    - **Director**: Acceso a funciones de gestión
    - **Admin**: Control total del sistema
    
    ### Políticas de Seguridad
    
    - Las contraseñas deben tener entre 8-20 caracteres
    - Después de 5 intentos fallidos, el usuario es bloqueado
    - Las sesiones expiran después de 30 días de inactividad
    - Todas las acciones son registradas para auditoría
    
    ### Soporte
    
    Para asistencia, contacte a: dgicyt@sicyt.gob.ar
    """)

# Guardar estado de la sesión
if st.session_state.get('username'):
    st.sidebar.markdown(f"**Usuario actual:** {st.session_state['username']}")
    st.sidebar.markdown(f"**Rol:** {', '.join(st.session_state.get('roles', ['Sin rol']))}")
    auth_manager.logout(location='sidebar', key='logout_admin')
