"""
Gestor centralizado de autenticación para el sistema de informes.
Utiliza streamlit-authenticator de forma correcta y completa.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from logging_config import get_logger, log_user_activity

logger = get_logger(__name__)


class AuthManager:
    """
    Gestor centralizado de autenticación que encapsula toda la lógica
    de streamlit-authenticator.
    """
    
    def __init__(self, config_path: str = ".streamlit/credentials.yaml"):
        """
        Inicializa el gestor de autenticación.
        ed to
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.authenticator = self._initialize_authenticator()
        
    def _load_config(self) -> Dict:
        """Carga la configuración desde el archivo YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.load(file, Loader=SafeLoader)
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado: {self.config_path}")
            raise
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            raise
    
    def _save_config(self) -> None:
        """Guarda la configuración actualizada al archivo YAML."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            logger.info("Configuración guardada exitosamente")
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            raise

    def _initialize_authenticator(self) -> stauth.Authenticate:
        """Inicializa el objeto authenticator de streamlit-authenticator."""
        return stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days'],
            api_key=self.config['api_key']
        )

    def login(self, location: str = 'main') -> None:
        """
        Renderiza el widget de login.
        
        Args:
            location: Ubicación del widget ('main', 'sidebar', 'unrendered')
        """
        try:
            self.authenticator.login(location=location)
        except stauth.LoginError as e:
            st.error(f"Error de login: {e}")
    
    def logout(self, location: str = 'sidebar', key: str = 'logout_sidebar') -> None:
        """
        Renderiza el botón de logout.
        
        Args:
            location: Ubicación del botón ('main', 'sidebar')
            key: Clave única para el widget
        """
        if st.session_state.get('authentication_status'):
            self.authenticator.logout(location=location, key=key)
    
    @log_user_activity(activity_type="register_user")
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
            result = self.authenticator.register_user(
                location=location,
                pre_authorized=self.config.get('pre-authorized', {}).get('emails') if pre_authorized else None,
                roles=roles,
                password_hint=False
            )
            if result[0]:  # Si se registró exitosamente
                self._save_config()
            return result
        except stauth.RegisterError as e:
            st.error(f"Error de registro: {e}")
            return None, None, None
    
    @log_user_activity(activity_type="reset_password")
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
            result = self.authenticator.reset_password(username, location=location)
            if result:
                self._save_config()
            return result
        except (stauth.CredentialsError, stauth.ResetError) as e:
            st.error(f"Error al resetear contraseña: {e}")
            return False
    
    @log_user_activity(activity_type="forgot_password")
    def forgot_password(
        self,
        location: str = 'main',
        send_email: bool = False
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Widget para recuperación de contraseña olvidada.
        
        Args:
            location: Ubicación del widget
            send_email: Si enviar la nueva contraseña por email
            
        Returns:
            Tupla con (username, email, new_password)
        """
        try:
            result = self.authenticator.forgot_password(
                location=location,
                send_email=send_email
            )
            if result[0]:  # Si se generó nueva contraseña
                self._save_config()
            return result
        except stauth.ForgotError as e:
            st.error(f"Error: {e}")
            return None, None, None
    
    @log_user_activity(activity_type="forgot_username")
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
            result = self.authenticator.forgot_username(
                location=location,
                send_email=send_email
            )
            return result
        except stauth.ForgotError as e:
            st.error(f"Error: {e}")
            return None, None
    
    @log_user_activity(activity_type="update_user_details")
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
            result = self.authenticator.update_user_details(username, location=location)
            if result:
                self._save_config()
            return result
        except stauth.UpdateError as e:
            st.error(f"Error al actualizar: {e}")
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Obtiene la información de un usuario específico.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con la información del usuario o None
        """
        return self.config['credentials']['usernames'].get(username)
    
    def get_all_users(self) -> Dict:
        """
        Obtiene todos los usuarios del sistema.
        
        Returns:
            Diccionario con todos los usuarios
        """
        return self.config['credentials']['usernames']
    
    @log_user_activity(activity_type="delete_user")
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
                logger.info(f"Usuario {username} eliminado exitosamente")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar usuario: {e}")
            return False
    
    @log_user_activity(activity_type="add_role")
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
                    return True
            return False
        except Exception as e:
            logger.error(f"Error al agregar rol: {e}")
            return False
    
    @log_user_activity(activity_type="remove_role")
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
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar rol: {e}")
            return False
    
    @log_user_activity(activity_type="update_roles")
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
                return True
            return False
        except Exception as e:
            logger.error(f"Error al actualizar roles: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado."""
        return st.session_state.get('authentication_status', False)
    
    def has_role(self, role: str) -> bool:
        """
        Verifica si el usuario actual tiene un rol específico.
        
        Args:
            role: Rol a verificar
            
        Returns:
            True si el usuario tiene el rol
        """
        roles = st.session_state.get('roles', [])
        return role in roles if roles else False
    
    def has_any_role(self, roles: List[str]) -> bool:
        """
        Verifica si el usuario tiene alguno de los roles especificados.
        
        Args:
            roles: Lista de roles a verificar
            
        Returns:
            True si el usuario tiene al menos uno de los roles
        """
        user_roles = st.session_state.get('roles', [])
        return any(role in user_roles for role in roles) if user_roles else False
    
    def require_authentication(self) -> bool:
        """
        Verifica autenticación y muestra mensaje si no está autenticado.
        
        Returns:
            True si está autenticado, False en caso contrario
        """
        if not self.is_authenticated():
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
        if not self.has_role(role):
            st.error("Acceso no autorizado.")
            st.stop()
            return False
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
        if not self.has_any_role(roles):
            st.error("Acceso no autorizado.")
            st.stop()
            return False
        return True


# Singleton para mantener una única instancia del AuthManager
def get_auth_manager(config_path: str = ".streamlit/credentials.yaml") -> AuthManager:
    """
    Obtiene o crea una instancia única del AuthManager.
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Instancia del AuthManager
    """
    return AuthManager(config_path)
