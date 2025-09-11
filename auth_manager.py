"""
Gestor centralizado de autenticación para el sistema de informes con logging completo.
Utiliza streamlit-authenticator de forma correcta y completa.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from logging_config import get_logger, get_audit_logger, log_execution

# Inicializar loggers
logger = get_logger(__name__)
audit_logger = get_audit_logger()


class AuthManager:
    """
    Gestor centralizado de autenticación que encapsula toda la lógica
    de streamlit-authenticator con logging completo.
    """
    
    @log_execution(log_args=False)
    def __init__(self, config_path: str = ".streamlit/credentials.yaml"):
        """
        Inicializa el gestor de autenticación.
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = Path(config_path)
        logger.info(f"Inicializando AuthManager con configuración: {config_path}")
        
        try:
            self.config = self._load_config()
            self.authenticator = self._initialize_authenticator()
            logger.info("AuthManager inicializado exitosamente")
        except Exception as e:
            logger.critical(f"Error crítico al inicializar AuthManager: {e}")
            raise
        
    def _load_config(self) -> Dict:
        """Carga la configuración desde el archivo YAML."""
        try:
            logger.debug(f"Cargando configuración desde {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.load(file, Loader=SafeLoader)
                
            # Log estadísticas de configuración
            user_count = len(config.get('credentials', {}).get('usernames', {}))
            logger.info(f"Configuración cargada: {user_count} usuarios registrados")
            
            return config
            
        except FileNotFoundError:
            logger.critical(f"Archivo de configuración no encontrado: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.critical(f"Error al parsear YAML: {e}")
            raise
        except Exception as e:
            logger.critical(f"Error inesperado al cargar configuración: {e}")
            raise
    
    @log_execution(log_args=False)
    def _save_config(self) -> None:
        """Guarda la configuración actualizada al archivo YAML."""
        try:
            logger.debug("Guardando configuración actualizada")
            
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
                
            logger.info("Configuración guardada exitosamente")
            
        except PermissionError:
            logger.error(f"Sin permisos para escribir en {self.config_path}")
            raise
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            raise

    def _initialize_authenticator(self) -> stauth.Authenticate:
        """Inicializa el objeto authenticator de streamlit-authenticator."""
        try:
            logger.debug("Inicializando objeto Authenticate")
            
            authenticator = stauth.Authenticate(
                self.config['credentials'],
                self.config['cookie']['name'],
                self.config['cookie']['key'],
                self.config['cookie']['expiry_days'],
                api_key=self.config['api_key']
            )
            
            logger.debug("Authenticator inicializado correctamente")
            return authenticator
            
        except KeyError as e:
            logger.error(f"Configuración incompleta, falta clave: {e}")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar authenticator: {e}")
            raise

    def login(self, location: str = 'main') -> (Tuple[str | None, bool | None, str | None] | None):
        """
        Renderiza el widget de login.
        
        Args:
            location: Ubicación del widget ('main', 'sidebar', 'unrendered')
        """
        if 'name' not in st.session_state:
            st.session_state['name'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = None
        if 'logout' not in st.session_state:
            st.session_state['logout'] = None

        result = self.authenticator.login(location='unrendered', key='login check')
        logger.debug(f"Login no renderizado, resultado devuelto: {result}")

        try:
            if location == 'unrendered':
                return result
            else:
                logger.debug(f"Renderizando widget de login en ubicación: {location}")
                
                self.authenticator.login(
                    location=location,
                    fields={
                        'Username': 'Usuario',
                        'Password': 'Contraseña',
                        'Login': 'Iniciar Sesión'
                    },
                )
                
                if st.session_state.get('authentication_status') is True:
                    audit_logger.log_login(st.session_state['username'], success=True)
                elif st.session_state.get('authentication_status') is False:
                    st.error("Usuario o contraseña incorrectos.")
                    audit_logger.log_login(username='unknown', success=False)
                elif st.session_state.get('authentication_status') is None:
                    st.warning("Por favor, ingrese sus credenciales.")
                    
        except stauth.LoginError as e:
            logger.error(f"Error de login: {e}")
            st.error("Error de login. Por favor, inténtelo de nuevo.")
        except Exception as e:
            logger.critical(f"Error inesperado en login: {e}")
            st.error("Error inesperado en login. Por favor, contacte al administrador.")
            st.stop()
    
    def logout(self, location: str = 'sidebar', key: str = 'logout_sidebar') -> None:
        """
        Renderiza el botón de logout.
        
        Args:
            location: Ubicación del botón ('main', 'sidebar')
            key: Clave única para el widget
        """
        if st.session_state.get('authentication_status'):
            username = st.session_state['username']
            logger.debug(f"Renderizando botón de logout para usuario: {username}")
            
            try:
                self.authenticator.logout(
                    location=location,
                    key=key,
                    button_name='Cerrar Sesión',
                    callback=lambda username=username: audit_logger.log_logout(username.get('username', 'unknown'))
                )
                    
            except Exception as e:
                logger.critical(f"Error inesperado en logout: {e}")

    @log_execution(log_result=False, sensitive_args=['password'])
    def register_user(
        self,
        location: str = 'main',
        pre_authorized: bool = True,
        roles: Optional[List[str]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Renderiza el widget de registro de nuevos usuarios.
        
        Args:
            location: Ubicación del widget
            pre_authorized: Lista de emails pre-autorizados
            roles: Roles a asignar al nuevo usuario
            
        Returns:
            Tupla con (email, username, name) del usuario registrado
        """
        try:
            logger.debug(f"Iniciando proceso de registro de usuario con roles: {roles}")
            
            result = self.authenticator.register_user(
                location=location,
                pre_authorized=self.config.get('pre-authorized', {}).get('emails') if pre_authorized else None,
                fields={
                    'Form name': 'Nuevo Usuario',
                    'First name': 'Nombre',
                    'Last name': 'Apellido',
                    'Username': 'Usuario',
                    'Password': 'Contraseña',
                    'Repeat password': 'Repetir Contraseña',
                    'Register': 'Crear usuario',
                },
                roles=roles,
                password_hint=False
            )
            
            if result[0]:  # Si se registró exitosamente
                email, username, name = result
                audit_logger.log_user_registration(
                    new_user=username,
                    email=email,
                    roles=roles or [],
                    requested_by=st.session_state.get('username', 'self')
                )
                self._save_config()
                
            return result
            
        except stauth.RegisterError as e:
            logger.warning(f"Error de registro de usuario: {e}")
            st.warning(f"Error de registro de usuario: {e}")
            return None, None, None
        except Exception as e:
            logger.critical(f"Error inesperado en registro de usuario: {e}")
            st.error("Error inesperado en registro de usuario. Por favor, contacte al administrador.")
            st.stop()
            return None, None, None
    
    @log_execution(sensitive_args=['password', 'new_password'])
    def reset_password(self, username: str, location: str = 'main') -> bool:
        """
        Widget para resetear contraseña del usuario actual.
        
        Args:
            username: Nombre de usuario
            location: Ubicación del widget
            
        Returns:
            True si la contraseña se cambió exitosamente
        """
        try:
            logger.debug(f"Iniciando reset de contraseña para usuario: {username}")
            
            result = self.authenticator.reset_password(
                username,
                location=location,
                fields={
                    'Form name': 'Actualizar Contraseña de Usuario actual',
                    'Current password': 'Contraseña Actual',
                    'New password': 'Nueva Contraseña',
                    'Repeat password': 'Repetir Nueva Contraseña',
                    'Reset': 'Actualizar'
                }
            )
            if result:
                audit_logger.log_password_change(
                    user=username,
                    requested_by=st.session_state.get('username', username)
                )
                self._save_config()

            return result
            
        except (stauth.CredentialsError, stauth.ResetError) as e:
            logger.warning(f"Error al cambiar contraseña para {username}: {e}")
            st.warning(f"Error al cambiar contraseña: {e}")
            return False
        except Exception as e:
            logger.critical(f"Error inesperado al cambiar contraseña: {e}")
            st.error("Error inesperado al cambiar contraseña. Por favor, inténtelo nuevamente.")
            return False
    
    @log_execution(sensitive_args=['new_password'])
    def forgot_password(
        self,
        location: str = 'main',
        send_email: bool = False
    ) -> Tuple[str | None, str | None, str | None]:
        """
        Widget para recuperación de contraseña olvidada.
        
        Args:
            location: Ubicación del widget
            send_email: Si enviar la nueva contraseña por email
            
        Returns:
            Tupla con (username, email, new_password)
            o (None, None, None) en caso de error
        """
        try:
            logger.debug("Iniciando proceso de recuperación de contraseña")
            
            result = self.authenticator.forgot_password(
                location=location,
                send_email=send_email,
                fields={
                    'Username': 'Usuario',
                    'Form name': 'Recuperar contraseña',
                    'Submit': 'Enviar por email'
                }
            )
            if result[0]:  # Si se generó nueva contraseña
                username, email, new_password = result
                audit_logger.log_password_change(
                    user=username,
                    requested_by=st.session_state.get('username', 'unknown')
                )
                self._save_config()

            return result
            
        except stauth.ForgotError as e:
            logger.warning(f"Error en recuperación de contraseña: {e}")
            st.warning(f"Error: {e}")
            return None, None, None
        except TypeError:
            logger.warning("Usuario inexistente en recuperación de contraseña.")
            st.warning("Usuario inexistente.")
            return None, None, None
        except Exception as e:
            logger.critical(f"Error inesperado en recuperación de contraseña: {e}")
            st.error("Error en recuperación de contraseña. Por favor, inténtelo nuevamente.")
            st.stop()
            return None, None, None
    
    def forgot_username(
        self,
        location: str = 'main',
        send_email: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Widget para recuperación de username olvidado.
        
        Args:
            location: Ubicación del widget
            send_email: Si enviar el username por email
            
        Returns:
            Tupla con (username, email)
        """
        try:
            logger.debug("Iniciando proceso de recuperación de username")
            
            result = self.authenticator.forgot_username(
                location=location,
                send_email=send_email,
                fields={
                    'Email': 'Email',
                    'Form name': 'Recuperar usuario',
                    'Submit': 'Recuperar'
                }
            )
            
            if result[0]:
                username, email = result
                logger.info(f"Username recuperado: {username} para email: {email}")
                audit_logger.log_username_recovery(
                    user=username,
                    email=email,
                    requested_by=st.session_state.get('username', 'unknown')
                )
                
            return result
            
        except stauth.ForgotError as e:
            logger.warning(f"Error en recuperación de username: {e}")
            st.warning(f"Error en recuperación de username: {e}")
            return None, None
        except stauth.CloudError as e:
            logger.warning(f"Error en recuperación de username: {e}")
            st.warning("Email inválido.")
            return None, None
        except Exception as e:
            logger.critical(f"Error inesperado en recuperación de username: {e}")
            st.error("Error en recuperación de username. Por favor, inténtelo nuevamente.")
            st.stop()
            return None, None
    
    @log_execution()
    def update_user_details(self, username: str, location: str = 'main') -> bool:
        """
        Widget para actualizar detalles del usuario.
        
        Args:
            username: Nombre de usuario
            location: Ubicación del widget
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            logger.debug(f"Actualizando detalles para usuario: {username}")
            
            result = self.authenticator.update_user_details(
                username,
                location=location,
                fields={
                    'Form name': 'Actualizar detalles',
                    'First name': 'Nombre',
                    'Last name': 'Apellido',
                    'Update': 'Actualizar',
                    'Field': 'Campo',
                    'New value': 'Nuevo valor'
                }
            )
            
            if result:
                audit_logger.log_user_update(
                    user=username,
                    requested_by=st.session_state.get('username', 'system')
                )
                self._save_config()
                
            return result
            
        except stauth.UpdateError as e:
            logger.warning(f"Error al actualizar detalles de {username}: {e}")
            st.warning(f"Error al actualizar datos de {username}: {e}")
            return False
        except Exception as e:
            logger.critical(f"Error inesperado al actualizar usuario: {e}")
            st.error(f"Error al actualizar datos de {username}.")
            st.stop()
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Obtiene la información de un usuario específico.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con la información del usuario o None
        """
        try:
            user_info = self.config['credentials']['usernames'].get(username)
            
            if user_info:
                logger.debug(f"Información obtenida para usuario: {username}")
            else:
                logger.warning(f"Usuario no encontrado: {username}")
                
            return user_info
            
        except Exception as e:
            logger.error(f"Error al obtener información de usuario {username}: {e}")
            return None
    
    def get_all_users(self) -> Dict:
        """
        Obtiene todos los usuarios del sistema.
        
        Returns:
            Diccionario con todos los usuarios
        """
        try:
            users = self.config['credentials']['usernames']
            logger.debug(f"Obteniendo lista de {len(users)} usuarios")
            return users
        except Exception as e:
            logger.error(f"Error al obtener lista de usuarios: {e}")
            return {}
    
    @log_execution()
    def delete_user(self, username: str) -> bool:
        """
        Elimina un usuario del sistema.
        
        Args:
            username: Nombre de usuario a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if username in self.config['credentials']['usernames']:
                del self.config['credentials']['usernames'][username]
                self._save_config()
                
                logger.info(f"Usuario eliminado: {username}")
                audit_logger.log_user_deletion(
                    user=username,
                    requested_by=st.session_state.get('username', 'system')
                )
                return True
            else:
                logger.warning(f"Intento de eliminar usuario inexistente: {username}")
                return False
                
        except Exception as e:
            logger.error(f"Error al eliminar usuario {username}: {e}")
            return False
    
    @log_execution()
    def add_role_to_user(self, username: str, role: str) -> bool:
        """
        Agrega un rol a un usuario.
        
        Args:
            username: Nombre de usuario
            role: Rol a agregar
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            user = self.get_user_info(username)
            if user:
                if 'roles' not in user:
                    user['roles'] = []
                if role not in user['roles']:
                    user['roles'].append(role)
                    self._save_config()

                    audit_logger.log_role_update(
                        user=username,
                        roles=user['roles'],
                        requested_by=st.session_state.get('username', 'system')
                    )
                    return True
                else:
                    logger.debug(f"Usuario {username} ya tiene el rol '{role}'")
                    
            return False
            
        except Exception as e:
            logger.critical(f"Error inesperado al agregar rol '{role}' a usuario {username}: {e}")
            st.error(f"Error al agregar rol '{role}' a usuario {username}. {e}")
            return False
    
    @log_execution()
    def remove_role_from_user(self, username: str, role: str) -> bool:
        """
        Elimina un rol de un usuario.
        
        Args:
            username: Nombre de usuario
            role: Rol a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            user = self.get_user_info(username)
            if user and 'roles' in user and role in user['roles']:
                user['roles'].remove(role)
                self._save_config()
                
                audit_logger.log_role_update(
                    user=username,
                    roles=user['roles'],
                    requested_by=st.session_state.get('username', 'system')
                )
                return True
                
            return False
            
        except Exception as e:
            logger.critical(f"Error inesperado al eliminar rol '{role}' de usuario {username}: {e}")
            st.error(f"Error al eliminar rol '{role}' de usuario {username}. {e}")
            return False
    
    @log_execution()
    def update_user_roles(self, username: str, roles: List[str]) -> bool:
        """
        Actualiza completamente los roles de un usuario.
        
        Args:
            username: Nombre de usuario
            roles: Nueva lista de roles
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            user = self.get_user_info(username)
            if user:
                user['roles'] = roles
                self._save_config()
                
                audit_logger.log_role_update(
                    user=username,
                    roles=roles,
                    requested_by=st.session_state.get('username', 'system')
                )
                return True
                
            return False
            
        except Exception as e:
            logger.critical(f"Error inesperado al actualizar roles de usuario {username}: {e}")
            st.error(f"Error al actualizar roles de usuario {username}. {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado."""
        is_auth = st.session_state.get('authentication_status', False)
        logger.debug(f"Estado de autenticación: {is_auth}")
        return is_auth
    
    def has_role(self, role: str) -> bool:
        """
        Verifica si el usuario actual tiene un rol específico.
        
        Args:
            role: Rol a verificar
            
        Returns:
            True si el usuario tiene el rol
        """
        roles = st.session_state.get('roles', [])
        has_it = role in roles if roles else False
        
        if not has_it:
            username = st.session_state.get('username', 'unknown')
            logger.debug(f"Usuario {username} no tiene rol '{role}'")
            
        return has_it
    
    def has_any_role(self, roles: List[str]) -> bool:
        """
        Verifica si el usuario tiene alguno de los roles especificados.
        
        Args:
            roles: Lista de roles a verificar
            
        Returns:
            True si el usuario tiene al menos uno de los roles
        """
        user_roles = st.session_state.get('roles', [])
        has_any = any(role in user_roles for role in roles) if user_roles else False
        
        if not has_any:
            username = st.session_state.get('username', 'unknown')
            logger.debug(f"Usuario {username} no tiene ninguno de los roles: {roles}")
            
        return has_any
    
    def require_authentication(self) -> bool:
        """
        Verifica autenticación y muestra mensaje si no está autenticado.
        
        Returns:
            True si está autenticado, False en caso contrario
        """
        if not self.is_authenticated():
            audit_logger.log_permission_denied(
                user='anonymous',
                resource='protected_resource',
                required_permission='authentication'
            )
            st.warning("Debe estar logueado para acceder a esta información.")
            st.stop()
            return False
        return True
    
    def require_role(self, role: str) -> bool:
        """
        Verifica que el usuario tenga un rol específico.
        
        Args:
            role: Rol requerido
            
        Returns:
            True si tiene el rol, False y detiene la app en caso contrario
        """
        self.require_authentication()
        
        username = st.session_state.get('username', 'unknown')
        
        if not self.has_role(role):
            audit_logger.log_permission_denied(
                user=username,
                resource='role_protected_resource',
                required_permission=role
            )
            st.error("Acceso no autorizado.")
            st.stop()
            return False
        
        logger.debug(f"Acceso concedido a {username} con rol '{role}'")
        return True
    
    def require_any_role(self, roles: List[str]) -> bool:
        """
        Verifica que el usuario tenga al menos uno de los roles especificados.
        
        Args:
            roles: Lista de roles permitidos
            
        Returns:
            True si tiene algún rol, False y detiene la app en caso contrario
        """
        self.require_authentication()
        
        username = st.session_state.get('username', 'unknown')
        
        if not self.has_any_role(roles):
            audit_logger.log_permission_denied(
                user=username,
                resource='role_protected_resource',
                required_permission=','.join(roles)
            )
            st.error("Acceso no autorizado.")
            st.stop()
            return False
        
        logger.debug(f"Acceso concedido a {username} con roles permitidos")
        return True


# Utilidades menu
def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.markdown("###")
    st.sidebar.page_link("Inicio.py")
    st.sidebar.page_link("pages/1_fichas_provinciales.py", label="Fichas Provinciales", icon=":material/analytics:")
    if 'admin' in st.session_state['roles']:
        st.sidebar.page_link("pages/98_admin_usuarios.py", label="Administar Usuarios", icon=":material/manage_accounts:")
        st.sidebar.page_link("pages/99_monitor_de_logs.py", label="Monitor de Logs", icon=":material/monitor_heart:")
    st.sidebar.markdown("---")


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.markdown("###")
    st.sidebar.page_link("Inicio.py", label="Log in")
    st.sidebar.markdown("---")


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if st.session_state.get("authentication_status") is not True:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if st.session_state.get("authentication_status") is not True:
        st.switch_page("Inicio.py")
    menu()


# Singleton para mantener una única instancia del AuthManager
_auth_manager_instance = None


def get_auth_manager(config_path: str = ".streamlit/credentials.yaml") -> AuthManager:
    """
    Obtiene o crea una instancia única del AuthManager.
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Instancia del AuthManager
    """
    global _auth_manager_instance
    
    if _auth_manager_instance is None:
        logger.info("Creando nueva instancia de AuthManager")
        _auth_manager_instance = AuthManager(config_path)
    else:
        logger.debug("Reutilizando instancia existente de AuthManager")
        
    return _auth_manager_instance
