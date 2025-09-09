"""
Sistema centralizado de logging mejorado para la aplicación de Informes SICyT.
Incluye logging de aplicación, auditoría y monitoreo de rendimiento.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional, Any, Callable, Dict, List
import json
import traceback
import streamlit as st
from contextlib import contextmanager
import threading
import re

# Configuración de directorios
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"

# Crear estructura de directorios
LOG_SUBDIRS = ["app", "audit", "errors", "performance", "security"]
for subdir in LOG_SUBDIRS:
    (LOGS_DIR / subdir).mkdir(parents=True, exist_ok=True)

# Configuración de niveles
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Obtener nivel de log del entorno o usar INFO por defecto
LOG_LEVEL = LOG_LEVELS.get(os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

# Thread-local storage para contexto
_log_context = threading.local()


class SecurityFilter(logging.Filter):
    """Filtro para sanitizar información sensible en los logs."""
    
    # Patrones de información sensible
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'password: ***REDACTED***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'token: ***REDACTED***'),
        (r'api_key["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'api_key: ***REDACTED***'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '***SSN***'),
        (r'\b\d{16}\b', '***CARD***'),
    ]
    
    def filter(self, record):
        """Sanitiza el mensaje del log."""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
            record.msg = msg
        return True


class CustomJSONFormatter(logging.Formatter):
    """Formateador personalizado para logs en formato JSON."""
    
    def format(self, record):
        # Obtener contexto del thread local
        context = getattr(_log_context, 'context', {})
        
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "user": context.get('user') or st.session_state.get('username') or 'invitado',
            "session_id": context.get('session_id') or getattr(st.session_state, 'session_id', None),
            "request_id": context.get('request_id'),
            "ip_address": context.get('ip_address'),
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Agregar campos extra
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                'getMessage'
            ]:
                log_obj[key] = value
                
        return json.dumps(log_obj, ensure_ascii=False, default=str)


class CustomTextFormatter(logging.Formatter):
    """Formateador personalizado para logs en formato texto legible."""
    
    # Colores ANSI para la consola
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarillo
        'ERROR': '\033[31m',    # Rojo
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Formato base
        if sys.stdout.isatty():  # Si es consola interactiva, usar colores
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            levelname = f"{color}{record.levelname:8s}{reset}"
        else:
            levelname = f"{record.levelname:8s}"
            
        # Usuario actual
        context = getattr(_log_context, 'context', {})
        user = context.get('user')
        if not user:
            user = st.session_state.get('username')
        if not user:
            user = 'invitado'
        
        # Construir mensaje
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        message = f"{timestamp} | {levelname} | {user:15s} | {record.name:20s} | {record.funcName:20s} | {record.getMessage()}"
        
        # Agregar información de excepción si existe
        if record.exc_info:
            message += f"\nException: {record.exc_info[0].__name__}: {record.exc_info[1]}"
            if sys.stdout.isatty():
                message += f"\n{self.COLORS['ERROR']}{traceback.format_exc()}{self.COLORS['RESET']}"
            else:
                message += f"\n{traceback.format_exc()}"
            
        return message


class AuditLogger:
    """Logger especializado para auditoría de seguridad."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(f"InformesApp.{logger_name}")
        
    def log_login(self, username: str, success: bool, ip_address: str = None, details: Dict = None):
        """Registra intentos de login."""
        extra = {
            'audit_type': 'login',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        if success:
            self.logger.info(f"Login exitoso: {username}", extra=extra)
        else:
            self.logger.warning(f"Login fallido: {username}", extra=extra)
    
    def log_logout(self, username: str):
        """Registra logout de usuarios."""
        self.logger.info(f"Logout exitoso: {username.get('username')}", extra={'audit_type': 'logout', 'user': username})
    
    def log_data_access(self, user: str, resource: str, action: str = "read", details: Dict = None):
        """Registra acceso a datos."""
        extra = {
            'audit_type': 'data_access',
            'user': user,
            'resource': resource,
            'action': action,
            'details': details or {}
        }
        self.logger.info(f"Acceso a datos: {user} -> {resource} ({action})", extra=extra)
    
    def log_permission_denied(self, user: str, resource: str, required_permission: str):
        """Registra intentos de acceso denegado."""
        extra = {
            'audit_type': 'permission_denied',
            'user': user,
            'resource': resource,
            'required_permission': required_permission
        }
        self.logger.warning(f"Acceso denegado: {user} -> {resource}", extra=extra)
    
    def log_configuration_change(self, user: str, setting: str, old_value: Any, new_value: Any):
        """Registra cambios de configuración."""
        # Sanitizar valores sensibles
        if 'password' in setting.lower() or 'key' in setting.lower():
            old_value = '***REDACTED***'
            new_value = '***REDACTED***'
            
        extra = {
            'audit_type': 'config_change',
            'user': user,
            'setting': setting,
            'old_value': old_value,
            'new_value': new_value
        }
        self.logger.info(f"Cambio de configuración: {setting}", extra=extra)
    
    def log_export(self, user: str, data_type: str, format: str, records_count: int = None):
        """Registra exportación de datos."""
        extra = {
            'audit_type': 'data_export',
            'user': user,
            'data_type': data_type,
            'format': format,
            'records_count': records_count
        }
        self.logger.info(f"Exportación: {user} exportó {data_type} como {format}", extra=extra)

    def log_user_registration(self, new_user: str, email: str, roles: List[str], requested_by: str = 'self'):
        """Registra el registro de un nuevo usuario."""
        extra = {
            'audit_type': 'user_registration',
            'user': new_user,
            'email': email,
            'roles': roles,
            'requested_by': requested_by
        }
        self.logger.info(f"Registro de usuario: {new_user} ({email}) con roles {roles} por {requested_by}", extra=extra)

    def log_user_update(self, user: str, requested_by: str = 'self'):
        """Registra actualizaciones en la información del usuario."""
                
        extra = {
            'audit_type': 'user_update',
            'user': user,
            'requested_by': requested_by
        }
        self.logger.info(f"Actualización de datos de usuario: {user} por {requested_by}", extra=extra)

    def log_user_deletion(self, user: str, requested_by: str):
        """Registra la eliminación de un usuario."""
        extra = {
            'audit_type': 'user_deletion',
            'user': user,
            'requested_by': requested_by
        }
        self.logger.warning(f"Eliminación de usuario: {user} por {requested_by}", extra=extra)

    def log_password_change(self, user: str = 'unknown', requested_by: str = 'self', failed: bool = False):
        """Registra cambios de contraseña."""
        extra = {
            'audit_type': 'password_change',
            'user': user,
            'requested_by': requested_by
        }
        if failed:
            self.logger.warning(f"Intento fallido de cambio de contraseña para usuario: {user} por {requested_by}", extra=extra)
        else:
            self.logger.info(f"Cambio de contraseña para usuario: {user} por {requested_by}", extra=extra)

    def log_role_update(self, user: str, roles: List[str], requested_by: str = 'self'):
        """Registra cambios en los roles de un usuario."""
        extra = {
            'audit_type': 'role_change',
            'user': user,
            'roles': roles,
            'requested_by': requested_by
        }
        self.logger.info(f"Cambio de roles para usuario: {user} a {roles} por {requested_by}", extra=extra)

    def log_username_recovery(self, user: str = 'unknown', email: str = 'unknown', requested_by: str = 'unknown', failed: bool = False):
        """Registra intentos de recuperación de nombre de usuario."""
        extra = {
            'audit_type': 'username_recovery',
            'user': user,
            'email': email,
            'requested_by': requested_by
        }
        if failed:
            self.logger.warning(f"Recuperación de nombre de usuario fallida: {user} ({email}) por {requested_by}", extra=extra)
        else:
            self.logger.info(f"Recuperación de nombre de usuario: {user} ({email}) por {requested_by}", extra=extra)


class PerformanceLogger:
    """Logger especializado para métricas de rendimiento."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(f"InformesApp.{logger_name}")
    
    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Registra queries lentas."""
        if duration > threshold:
            extra = {
                'performance_type': 'slow_query',
                'query': query[:500],  # Limitar longitud
                'duration': duration,
                'threshold': threshold
            }
            self.logger.warning(f"Query lenta detectada ({duration:.2f}s)", extra=extra)
    
    def log_memory_usage(self, usage_mb: float, threshold_mb: float = 500):
        """Registra uso excesivo de memoria."""
        if usage_mb > threshold_mb:
            extra = {
                'performance_type': 'high_memory',
                'usage_mb': usage_mb,
                'threshold_mb': threshold_mb
            }
            self.logger.warning(f"Alto uso de memoria: {usage_mb:.2f} MB", extra=extra)
    
    def log_response_time(self, endpoint: str, duration: float, status_code: int = 200):
        """Registra tiempos de respuesta."""
        extra = {
            'performance_type': 'response_time',
            'endpoint': endpoint,
            'duration': duration,
            'status_code': status_code
        }
        
        if duration > 3.0:
            self.logger.warning(f"Respuesta lenta en {endpoint}: {duration:.2f}s", extra=extra)
        else:
            self.logger.info(f"Respuesta en {endpoint}: {duration:.2f}s", extra=extra)


def setup_logger(
    name: str = "InformesApp",
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = True,
    include_security_filter: bool = True
) -> logging.Logger:
    """
    Configura y retorna un logger personalizado.
    
    Args:
        name: Nombre del logger
        log_file: Nombre del archivo de log (sin extensión)
        console_output: Si mostrar logs en consola
        json_format: Si usar formato JSON (True) o texto (False)
        include_security_filter: Si incluir filtro de seguridad
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    
    # Agregar filtro de seguridad si está habilitado
    if include_security_filter:
        security_filter = SecurityFilter()
        logger.addFilter(security_filter)
    
    # Handler para archivo principal (JSON)
    if log_file:
        # Determinar subdirectorio basado en el tipo de log
        if 'audit' in name.lower():
            subdir = 'audit'
        elif 'error' in name.lower():
            subdir = 'errors'
        elif 'performance' in name.lower():
            subdir = 'performance'
        elif 'security' in name.lower():
            subdir = 'security'
        else:
            subdir = 'app'
            
        json_file = LOGS_DIR / subdir / f"{log_file}_{datetime.now():%Y%m}.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setFormatter(CustomJSONFormatter())
        json_handler.setLevel(LOG_LEVEL)
        logger.addHandler(json_handler)
        
        # Handler para archivo de texto legible
        text_file = LOGS_DIR / subdir / f"{log_file}_{datetime.now():%Y%m}.log"
        text_handler = logging.handlers.RotatingFileHandler(
            text_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        text_handler.setFormatter(CustomTextFormatter())
        text_handler.setLevel(LOG_LEVEL)
        logger.addHandler(text_handler)
        
        # Handler para errores críticos
        if LOG_LEVEL <= logging.ERROR:
            error_file = LOGS_DIR / 'errors' / f"critical_{datetime.now():%Y%m}.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=10,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(CustomTextFormatter())
            logger.addHandler(error_handler)
    
    # Handler para consola
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        if json_format and not sys.stdout.isatty():
            console_handler.setFormatter(CustomJSONFormatter())
        else:
            console_handler.setFormatter(CustomTextFormatter())
        console_handler.setLevel(LOG_LEVEL)
        logger.addHandler(console_handler)
    
    return logger


@contextmanager
def log_context(**kwargs):
    """
    Context manager para agregar contexto a los logs.
    
    Uso:
        with log_context(user='admin', request_id='123'):
            logger.info('Operación realizada')  # Incluirá user y request_id
    """
    if not hasattr(_log_context, 'context'):
        _log_context.context = {}
    
    old_context = _log_context.context.copy()
    _log_context.context.update(kwargs)
    
    try:
        yield
    finally:
        _log_context.context = old_context


# Decoradores mejorados

def log_execution(
    logger: Optional[logging.Logger] = None,
    log_args: bool = True,
    log_result: bool = False,
    sensitive_args: List[str] = None
):
    """
    Decorador para loguear automáticamente la ejecución de funciones.
    
    Args:
        logger: Logger a usar (si None, usa el logger por defecto)
        log_args: Si loguear los argumentos de la función
        log_result: Si loguear el resultado de la función
        sensitive_args: Lista de nombres de argumentos sensibles a ocultar
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
                
            func_name = func.__name__
            
            # Preparar argumentos para logging
            if log_args:
                # Ocultar argumentos sensibles
                safe_kwargs = kwargs.copy()
                if sensitive_args:
                    for arg in sensitive_args:
                        if arg in safe_kwargs:
                            safe_kwargs[arg] = '***REDACTED***'
                
                logger.debug(
                    f"Ejecutando {func_name}",
                    extra={
                        "function": func_name,
                        "args": str(args)[:200] if args else None,
                        "kwargs": str(safe_kwargs)[:200] if safe_kwargs else None
                    }
                )
            else:
                logger.debug(f"Ejecutando {func_name}")
            
            try:
                # Ejecutar función
                start_time = datetime.now()
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Log de éxito
                log_msg = f"Completado {func_name} en {duration:.3f}s"
                if log_result and result is not None:
                    result_str = str(result)[:100]
                    log_msg += f" - Resultado: {result_str}"
                
                logger.debug(
                    log_msg,
                    extra={
                        "function": func_name,
                        "duration_seconds": duration,
                        "success": True
                    }
                )
                return result
                
            except Exception as e:
                # Log de error
                logger.error(
                    f"Error en {func_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        "function": func_name,
                        "error_type": type(e).__name__,
                        "success": False
                    }
                )
                raise
                
        return wrapper
    return decorator


def log_database_operation(operation_type: str = "query"):
    """
    Decorador específico para operaciones de base de datos.
    
    Args:
        operation_type: Tipo de operación (query, insert, update, delete)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger("database")
            perf_logger = PerformanceLogger()
            
            # Extraer información SQL si está disponible
            sql = None
            if len(args) > 1 and isinstance(args[1], str):
                sql = args[1][:500]  # Limitar longitud del SQL
            elif 'plantilla_sql' in kwargs:
                sql = str(kwargs.get('plantilla_sql', ''))[:500]
                
            logger.info(
                f"Operación DB: {operation_type}",
                extra={
                    "operation": operation_type,
                    "function": func.__name__,
                    "sql_preview": sql
                }
            )
            
            try:
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Log de rendimiento para queries lentas
                if sql and duration > 1.0:
                    perf_logger.log_slow_query(sql, duration)
                
                # Log resultado
                rows_affected = 0
                if hasattr(result, '__len__'):
                    rows_affected = len(result)
                    
                logger.info(
                    f"Operación DB completada: {operation_type}",
                    extra={
                        "operation": operation_type,
                        "duration_seconds": duration,
                        "rows_affected": rows_affected,
                        "success": True
                    }
                )
                return result
                
            except Exception as e:
                logger.error(
                    f"Error en operación DB: {operation_type}",
                    exc_info=True,
                    extra={
                        "operation": operation_type,
                        "error_type": type(e).__name__,
                        "sql_preview": sql,
                        "success": False
                    }
                )
                raise
                
        return wrapper
    return decorator


def log_user_activity(activity_type: str):
    """
    Decorador para registrar actividades de usuario en auditoría.
    
    Args:
        activity_type: Tipo de actividad (login, logout, export, etc.)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            audit_logger = AuditLogger()
            
            # Obtener información del usuario
            user = getattr(st.session_state, 'username', 'anónimo')
            
            # Log de inicio de actividad
            logger = get_logger("audit")
            logger.info(
                f"Actividad de usuario: {activity_type}",
                extra={
                    "activity_type": activity_type,
                    "user": user,
                    "function": func.__name__
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Registrar en auditoría según el tipo de actividad
                if activity_type == "login" and result:
                    audit_logger.log_login(user, success=True)
                elif activity_type == "logout":
                    audit_logger.log_logout(user)
                elif activity_type == "export":
                    # Extraer información de exportación si está disponible
                    format_type = kwargs.get('format', 'unknown')
                    audit_logger.log_export(user, "data", format_type)
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Error en actividad de usuario: {activity_type}",
                    exc_info=True,
                    extra={
                        "activity_type": activity_type,
                        "user": user,
                        "error": str(e)
                    }
                )
                raise
                
        return wrapper
    return decorator


def log_streamlit_interaction(interaction_type: str = "click"):
    """
    Decorador para loguear interacciones de usuario en Streamlit.
    
    Args:
        interaction_type: Tipo de interacción (click, input, select, etc.)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger("ui")
            
            # Información del usuario
            user = getattr(st.session_state, 'username', 'anónimo')
            page = getattr(st.session_state, 'current_page', 'desconocida')
            
            with log_context(user=user, page=page, interaction=interaction_type):
                logger.info(
                    f"Interacción UI: {interaction_type}",
                    extra={
                        "interaction": interaction_type,
                        "function": func.__name__,
                        "page": page,
                        "user": user
                    }
                )
                
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"Interacción completada: {func.__name__}")
                    return result
                    
                except Exception as e:
                    logger.error(
                        f"Error en interacción UI: {func.__name__}. Error: {str(e)}",
                        exc_info=True,
                        extra={
                            "interaction": interaction_type,
                            "page": page
                        }
                    )
                    raise
                    
        return wrapper
    return decorator


# Funciones auxiliares mejoradas

def get_logger(name: str = None) -> logging.Logger:
    """
    Obtiene un logger configurado.
    
    Args:
        name: Nombre del logger (si None, usa el nombre por defecto)
    
    Returns:
        Logger configurado
    """
    if name is None:
        name = "InformesApp"
    
    # Si es un módulo específico, crear logger hijo
    if name != "InformesApp" and not name.startswith("InformesApp."):
        name = f"InformesApp.{name}"
    
    # Determinar archivo de log basado en el nombre
    log_file = name.replace("InformesApp.", "").replace(".", "_") or "app"
    
    return setup_logger(name, log_file=log_file)


def log_error(message: str, error: Exception = None, **extra):
    """
    Función auxiliar para loguear errores rápidamente.
    
    Args:
        message: Mensaje de error
        error: Excepción capturada (opcional)
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    if error:
        logger.error(message, exc_info=True, extra=extra)
    else:
        logger.error(message, extra=extra)


def log_info(message: str, **extra):
    """
    Función auxiliar para loguear información rápidamente.
    
    Args:
        message: Mensaje informativo
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    with log_context(**extra):
        logger.info(message)


def log_warning(message: str, **extra):
    """
    Función auxiliar para loguear advertencias rápidamente.
    
    Args:
        message: Mensaje de advertencia
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    with log_context(**extra):
        logger.warning(message)


def log_debug(message: str, **extra):
    """
    Función auxiliar para loguear debug rápidamente.
    
    Args:
        message: Mensaje de debug
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    with log_context(**extra):
        logger.debug(message)


def get_audit_logger() -> AuditLogger:
    """Obtiene una instancia del logger de auditoría."""
    return AuditLogger()


def get_performance_logger() -> PerformanceLogger:
    """Obtiene una instancia del logger de rendimiento."""
    return PerformanceLogger()


# Inicializar loggers principales al importar el módulo
main_logger = setup_logger("InformesApp", log_file="app")
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

# Log de inicialización
log_info("Sistema de logging inicializado", version="2.0.0",
         features=["security_filter", "audit", "performance", "context_manager"])

# Exportar funciones y clases principales
__all__ = [
    'setup_logger',
    'get_logger',
    'get_audit_logger',
    'get_performance_logger',
    'AuditLogger',
    'PerformanceLogger',
    'log_context',
    'log_execution',
    'log_database_operation',
    'log_user_activity',
    'log_streamlit_interaction',
    'log_error',
    'log_info',
    'log_warning',
    'log_debug',
]
