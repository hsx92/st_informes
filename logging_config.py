"""
Sistema centralizado de logging para la aplicación de Informes SICyT.
Autor: Secretaría de Innovación, Ciencia y Tecnología
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional, Any, Callable
import json
import traceback
import streamlit as st


# Configuración de directorios
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

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


class CustomJSONFormatter(logging.Formatter):
    """Formateador personalizado para logs en formato JSON."""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "user": getattr(st.session_state, 'username', 'sistema'),
            "session_id": getattr(st.session_state, 'session_id', None)
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Agregar campos extra si existen
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                           'levelname', 'levelno', 'lineno', 'module', 'msecs',
                           'pathname', 'process', 'processName', 'relativeCreated',
                           'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_obj[key] = value
                
        return json.dumps(log_obj, ensure_ascii=False)


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
        user = getattr(st.session_state, 'username', 'sistema')
        
        # Construir mensaje
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        message = f"{timestamp} | {levelname} | {user:15s} | {record.name:20s} | {record.funcName:20s} | {record.getMessage()}"
        
        # Agregar información de excepción si existe
        if record.exc_info:
            message += f"\nException: {record.exc_info[0].__name__}: {record.exc_info[1]}"
            
        return message


def setup_logger(
    name: str = "InformesApp",
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = True
) -> logging.Logger:
    """
    Configura y retorna un logger personalizado.
    
    Args:
        name: Nombre del logger
        log_file: Nombre del archivo de log (sin extensión)
        console_output: Si mostrar logs en consola
        json_format: Si usar formato JSON (True) o texto (False)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    
    # Handler para archivo principal (JSON)
    if log_file:
        json_file = LOGS_DIR / f"{log_file}.json"
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
        text_file = LOGS_DIR / f"{log_file}.log"
        text_handler = logging.handlers.RotatingFileHandler(
            text_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        text_handler.setFormatter(CustomTextFormatter())
        text_handler.setLevel(LOG_LEVEL)
        logger.addHandler(text_handler)
    
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


# Decoradores para logging automático
def log_execution(logger: Optional[logging.Logger] = None, log_args: bool = True):
    """
    Decorador para loguear automáticamente la ejecución de funciones.
    
    Args:
        logger: Logger a usar (si None, usa el logger por defecto)
        log_args: Si loguear los argumentos de la función
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
                
            func_name = func.__name__
            
            # Log de entrada
            if log_args:
                logger.debug(
                    f"Ejecutando {func_name}",
                    extra={
                        "function": func_name,
                        "args": str(args)[:200] if args else None,
                        "kwargs": str(kwargs)[:200] if kwargs else None
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
                logger.debug(
                    f"Completado {func_name}",
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


# Funciones auxiliares
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
    
    return setup_logger(name, log_file="informes_app")


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
    logger.info(message, extra=extra)


def log_warning(message: str, **extra):
    """
    Función auxiliar para loguear advertencias rápidamente.
    
    Args:
        message: Mensaje de advertencia
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    logger.warning(message, extra=extra)


def log_debug(message: str, **extra):
    """
    Función auxiliar para loguear debug rápidamente.
    
    Args:
        message: Mensaje de debug
        **extra: Campos adicionales para el log
    """
    logger = get_logger()
    logger.debug(message, extra=extra)


# Inicializar logger principal al importar el módulo
main_logger = setup_logger("InformesApp", log_file="informes_app")
log_info("Sistema de logging inicializado", version="1.0.0")
