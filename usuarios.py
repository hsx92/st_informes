import streamlit as st
import streamlit_authenticator as stauth
import yaml
from streamlit_authenticator.utilities import LoginError
from yaml import SafeLoader
from pathlib import Path
import re
from datetime import datetime
import secrets


class UserManager:
    """Clase para manejar la gestión completa de usuarios"""
    
    def __init__(self):
        self.credentials_path = Path(__file__).parent / ".streamlit" / "credentials.yaml"
        self.config = self._load_config()
        self.authenticator = self._init_authenticator()
    
    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        try:
            with self.credentials_path.open("r", encoding="utf-8") as file:
                return yaml.load(file, Loader=SafeLoader)
        except FileNotFoundError:
            st.error("❌ No se encontró el archivo de configuración de usuarios")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error al cargar configuración: {e}")
            st.stop()
    
    def _init_authenticator(self):
        """Inicializa el autenticador"""
        return stauth.Authenticate(
            self.config["credentials"],
            self.config["cookie"]["name"],
            self.config["cookie"]["key"],
            self.config["cookie"]["expiry_days"],
        )
    
    def _save_config(self):
        """Guarda la configuración actualizada al archivo YAML"""
        try:
            with self.credentials_path.open("w", encoding="utf-8") as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            st.error(f"❌ Error al guardar configuración: {e}")
            return False
    
    def _validate_email(self, email):
        """Valida el formato del email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password_strength(self, password):
        """Valida la fortaleza de la contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe tener al menos una mayúscula"
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe tener al menos una minúscula"
        if not re.search(r'\d', password):
            return False, "La contraseña debe tener al menos un número"
        return True, "Contraseña válida"
    
    def login(self):
        """Función de login principal"""
        try:
            self.authenticator.login(
                fields={
                    'Form name': 'Iniciar Sesión',
                    'Username': 'Usuario',
                    'Password': 'Contraseña',
                    'Login': 'Ingresar'
                },
                location='main'
            )
        except LoginError as e:
            st.error(f"❌ {e}")

        if st.session_state.get("authentication_status"):
            st.session_state["authenticator"] = self.authenticator
            self._show_welcome_dashboard()
            
        elif st.session_state.get("authentication_status") is False:
            st.error('❌ Usuario o contraseña incorrectos')
            self._show_additional_options()
            
        elif st.session_state.get("authentication_status") is None:
            st.warning('⚠️ Por favor ingrese sus credenciales')
            self._show_additional_options()
    
    def _show_welcome_dashboard(self):
        """Muestra el dashboard de bienvenida para usuarios autenticados"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(f"🎉 ¡Bienvenido/a {st.session_state['name']}!")
            st.subheader("Portal - Secretaría de Innovación, Ciencia y Tecnología")
            
            # Información del usuario
            user_info = self.config["credentials"]["usernames"].get(st.session_state["username"], {})
            st.info(f"""
            **Información de su cuenta:**
            - 👤 Usuario: {st.session_state['username']}
            - ✉️ Email: {user_info.get('email', 'No especificado')}
            - 🛡️ Roles: {', '.join(user_info.get('roles', ['Usuario']))}
            """)
        
        with col2:
            st.markdown("### Opciones de cuenta")
            if st.button("🔐 Cambiar contraseña", use_container_width=True):
                st.session_state.show_password_reset = True
                st.rerun()
            
            if st.button("👤 Actualizar perfil", use_container_width=True):
                st.session_state.show_update_profile = True
                st.rerun()
            
            self.authenticator.logout('🚪 Cerrar sesión', 'sidebar')
        
        st.markdown("---")
        st.subheader("◀️ Seleccione una opción del menú lateral")
        
        # Mostrar opciones adicionales si está activado
        if st.session_state.get("show_password_reset"):
            self._show_password_reset_form()
        
        if st.session_state.get("show_update_profile"):
            self._show_update_profile_form()
    
    def _show_additional_options(self):
        """Muestra opciones adicionales para usuarios no autenticados"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔑 ¿Olvidó su contraseña?", use_container_width=True):
                st.session_state.show_forgot_password = True
                st.rerun()
        
        with col2:
            if st.button("👤 Crear cuenta nueva", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        
        with col3:
            if st.button("🏠 Volver al inicio", use_container_width=True):
                # Limpiar estados
                for key in ['show_forgot_password', 'show_register']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Mostrar formularios según el estado
        if st.session_state.get("show_forgot_password"):
            self._show_forgot_password_form()
        
        if st.session_state.get("show_register"):
            self._show_register_form()
    
    def _show_register_form(self):
        """Muestra el formulario de registro"""
        st.markdown("---")
        st.subheader("📝 Crear Nueva Cuenta")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("👤 Nombre de usuario*", key="reg_username")
                new_name = st.text_input("🏷️ Nombre completo*", key="reg_name")
                new_email = st.text_input("✉️ Correo electrónico*", key="reg_email")
            
            with col2:
                new_password = st.text_input("🔐 Contraseña*", type="password", key="reg_password")
                confirm_password = st.text_input("🔐 Confirmar contraseña*", type="password", key="reg_confirm_password")
                user_role = st.selectbox("🛡️ Rol solicitado", ["usuario", "director"], key="reg_role")
            
            st.markdown("*Campos obligatorios")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                register_btn = st.form_submit_button("✅ Registrar cuenta", use_container_width=True)
            
            if register_btn:
                self._process_registration(new_username, new_name, new_email, new_password, confirm_password, user_role)
    
    def _process_registration(self, username, name, email, password, confirm_password, role):
        """Procesa el registro de nuevo usuario"""
        # Validaciones
        if not all([username, name, email, password, confirm_password]):
            st.error("❌ Todos los campos son obligatorios")
            return
        
        if username in self.config["credentials"]["usernames"]:
            st.error("❌ El nombre de usuario ya existe")
            return
        
        if password != confirm_password:
            st.error("❌ Las contraseñas no coinciden")
            return
        
        if not self._validate_email(email):
            st.error("❌ El formato del email no es válido")
            return
        
        is_valid, message = self._validate_password_strength(password)
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        # Verificar si el email ya está registrado
        for user_data in self.config["credentials"]["usernames"].values():
            if user_data.get("email") == email:
                st.error("❌ El correo electrónico ya está registrado")
                return
        
        try:
            # Crear hash de la contraseña
            hashed_password = stauth.Hasher([password]).generate()[0]
            
            # Agregar nuevo usuario
            self.config["credentials"]["usernames"][username] = {
                "email": email,
                "failed_login_attempts": 0,
                "first_name": name.split()[0] if name.split() else name,
                "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "logged_in": False,
                "password": hashed_password,
                "roles": [role]
            }
            
            # Guardar configuración
            if self._save_config():
                st.success(f"✅ Cuenta creada exitosamente para {name}")
                st.info("🔄 Actualizando sistema...")
                st.balloons()
                
                # Limpiar estado de registro
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("❌ Error al guardar el nuevo usuario")
                
        except Exception as e:
            st.error(f"❌ Error durante el registro: {e}")
    
    def _show_forgot_password_form(self):
        """Muestra el formulario de recuperación de contraseña"""
        st.markdown("---")
        st.subheader("🔑 Recuperar Contraseña")
        
        with st.form("forgot_password_form"):
            st.markdown("Ingrese su nombre de usuario para generar una nueva contraseña temporal:")
            
            username_recovery = st.text_input("👤 Nombre de usuario", key="recovery_username")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                recovery_btn = st.form_submit_button("🔄 Generar nueva contraseña", use_container_width=True)
            
            if recovery_btn:
                self._process_password_recovery(username_recovery)
    
    def _process_password_recovery(self, username):
        """Procesa la recuperación de contraseña"""
        if not username:
            st.error("❌ Por favor ingrese su nombre de usuario")
            return
        
        if username not in self.config["credentials"]["usernames"]:
            st.error("❌ Usuario no encontrado")
            return
        
        try:
            # Generar contraseña temporal
            temp_password = self._generate_temp_password()
            hashed_password = stauth.Hasher([temp_password]).generate()[0]
            
            # Actualizar contraseña
            self.config["credentials"]["usernames"][username]["password"] = hashed_password
            self.config["credentials"]["usernames"][username]["failed_login_attempts"] = 0
            
            if self._save_config():
                user_email = self.config["credentials"]["usernames"][username]["email"]
                
                st.success("✅ Contraseña temporal generada exitosamente")
                st.info(f"""
                **Nueva contraseña temporal:** `{temp_password}`
                
                **Importante:**
                - Guarde esta contraseña en un lugar seguro
                - Cambie la contraseña después de iniciar sesión
                - La contraseña temporal es válida hasta que la cambie
                - Se envió un recordatorio a: {user_email}
                """)
                
                # Limpiar estado
                st.session_state.show_forgot_password = False
                st.balloons()
            else:
                st.error("❌ Error al actualizar la contraseña")
                
        except Exception as e:
            st.error(f"❌ Error durante la recuperación: {e}")
    
    def _generate_temp_password(self):
        """Genera una contraseña temporal segura"""
        import string
        characters = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(characters) for _ in range(12))
    
    def _show_password_reset_form(self):
        """Muestra formulario para cambio de contraseña"""
        st.markdown("---")
        st.subheader("🔐 Cambiar Contraseña")
        
        with st.form("password_reset_form"):
            current_password = st.text_input("🔒 Contraseña actual", type="password")
            new_password = st.text_input("🔐 Nueva contraseña", type="password")
            confirm_new_password = st.text_input("🔐 Confirmar nueva contraseña", type="password")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                reset_btn = st.form_submit_button("✅ Cambiar contraseña", use_container_width=True)
            
            if reset_btn:
                self._process_password_reset(current_password, new_password, confirm_new_password)
    
    def _process_password_reset(self, current_password, new_password, confirm_password):
        """Procesa el cambio de contraseña"""
        if not all([current_password, new_password, confirm_password]):
            st.error("❌ Todos los campos son obligatorios")
            return
        
        if new_password != confirm_password:
            st.error("❌ Las nuevas contraseñas no coinciden")
            return
        
        is_valid, message = self._validate_password_strength(new_password)
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        try:
            # Verificar contraseña actual
            username = st.session_state["username"]
            stored_password = self.config["credentials"]["usernames"][username]["password"]
            
            if not stauth.Hasher([current_password]).check([stored_password])[0]:
                st.error("❌ La contraseña actual es incorrecta")
                return
            
            # Actualizar contraseña
            hashed_new_password = stauth.Hasher([new_password]).generate()[0]
            self.config["credentials"]["usernames"][username]["password"] = hashed_new_password
            
            if self._save_config():
                st.success("✅ Contraseña cambiada exitosamente")
                st.session_state.show_password_reset = False
                st.rerun()
            else:
                st.error("❌ Error al actualizar la contraseña")
                
        except Exception as e:
            st.error(f"❌ Error durante el cambio de contraseña: {e}")
    
    def _show_update_profile_form(self):
        """Muestra formulario para actualizar perfil"""
        st.markdown("---")
        st.subheader("👤 Actualizar Perfil")
        
        username = st.session_state["username"]
        current_data = self.config["credentials"]["usernames"][username]
        
        with st.form("update_profile_form"):
            new_email = st.text_input("✉️ Correo electrónico",
                                      value=current_data.get("email", ""))
            new_first_name = st.text_input("👤 Nombre",
                                           value=current_data.get("first_name", ""))
            new_last_name = st.text_input("👥 Apellido",
                                          value=current_data.get("last_name", ""))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                update_btn = st.form_submit_button("✅ Actualizar perfil", use_container_width=True)
            
            if update_btn:
                self._process_profile_update(username, new_email, new_first_name, new_last_name)
    
    def _process_profile_update(self, username, email, first_name, last_name):
        """Procesa la actualización del perfil"""
        if not email:
            st.error("❌ El email es obligatorio")
            return
        
        if not self._validate_email(email):
            st.error("❌ El formato del email no es válido")
            return
        
        try:
            # Verificar si el email ya está en uso por otro usuario
            for user, data in self.config["credentials"]["usernames"].items():
                if user != username and data.get("email") == email:
                    st.error("❌ El correo electrónico ya está registrado por otro usuario")
                    return
            
            # Actualizar información
            self.config["credentials"]["usernames"][username].update({
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            })
            
            if self._save_config():
                st.success("✅ Perfil actualizado exitosamente")
                st.session_state.show_update_profile = False
                st.rerun()
            else:
                st.error("❌ Error al actualizar el perfil")
                
        except Exception as e:
            st.error(f"❌ Error durante la actualización: {e}")


# Función principal para mantener compatibilidad
def login():
    """Función principal de login - mantiene compatibilidad con código existente"""
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    st.session_state.user_manager.login()


# Funciones adicionales para gestión de usuarios (para uso administrativo)
def manage_users():
    """Interfaz administrativa para gestión de usuarios"""
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Debe estar autenticado para acceder a esta función")
        return
    
    # Verificar permisos de administrador
    user_roles = st.session_state.get("roles", [])
    if "admin" not in user_roles:
        st.error("❌ No tiene permisos para gestionar usuarios")
        return
    
    st.subheader("👥 Gestión de Usuarios")
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    user_manager = st.session_state.user_manager
    users = user_manager.config["credentials"]["usernames"]
    
    # Mostrar tabla de usuarios
    if users:
        st.markdown("### Usuarios registrados:")
        
        users_data = []
        for username, data in users.items():
            users_data.append({
                "Usuario": username,
                "Nombre": f"{data.get('first_name', '')} {data.get('last_name', '')}",
                "Email": data.get('email', ''),
                "Roles": ', '.join(data.get('roles', [])),
                "Intentos fallidos": data.get('failed_login_attempts', 0),
                "Conectado": "✅" if data.get('logged_in', False) else "❌"
            })
        
        st.dataframe(users_data, use_container_width=True)
        
        # Opciones administrativas
        st.markdown("### Acciones administrativas:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user = st.selectbox("Seleccionar usuario:", list(users.keys()))
            
            if st.button("🔓 Resetear intentos fallidos"):
                user_manager.config["credentials"]["usernames"][selected_user]["failed_login_attempts"] = 0
                if user_manager._save_config():
                    st.success(f"✅ Intentos fallidos reseteados para {selected_user}")
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Eliminar usuario seleccionado"):
                if selected_user != st.session_state["username"]:  # No permitir auto-eliminación
                    del user_manager.config["credentials"]["usernames"][selected_user]
                    if user_manager._save_config():
                        st.success(f"✅ Usuario {selected_user} eliminado")
                        st.rerun()
                else:
                    st.error("❌ No puede eliminar su propia cuenta")
    else:
        st.info("No hay usuarios registrados")


# Función para exportar/importar configuración (uso administrativo)
def backup_restore_users():
    """Funciones de respaldo y restauración de usuarios"""
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Debe estar autenticado para acceder a esta función")
        return
    
    user_roles = st.session_state.get("roles", [])
    if "admin" not in user_roles:
        st.error("❌ No tiene permisos para esta función")
        return
    
    st.subheader("💾 Respaldo y Restauración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 Crear respaldo")
        if st.button("Descargar configuración actual"):
            if 'user_manager' not in st.session_state:
                st.session_state.user_manager = UserManager()
            
            config_yaml = yaml.dump(
                st.session_state.user_manager.config,
                default_flow_style=False, allow_unicode=True
            )
            
            st.download_button(
                label="💾 Descargar archivo YAML",
                data=config_yaml,
                file_name=f"backup_usuarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                mime="text/yaml"
            )
    
    with col2:
        st.markdown("### 📥 Restaurar respaldo")
        st.warning("⚠️ Esta acción sobrescribirá la configuración actual")
        
        uploaded_file = st.file_uploader("Seleccionar archivo de respaldo", type=['yaml', 'yml'])
        
        if uploaded_file and st.button("🔄 Restaurar configuración"):
            try:
                config_data = yaml.safe_load(uploaded_file)
                # Validar estructura básica
                if "credentials" in config_data and "cookie" in config_data:
                    if 'user_manager' not in st.session_state:
                        st.session_state.user_manager = UserManager()
                    
                    st.session_state.user_manager.config = config_data
                    if st.session_state.user_manager._save_config():
                        st.success("✅ Configuración restaurada exitosamente")
                        st.info("🔄 Reinicie la aplicación para aplicar los cambios")
                    else:
                        st.error("❌ Error al guardar la configuración restaurada")
                else:
                    st.error("❌ Formato de archivo inválido")
            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {e}")
