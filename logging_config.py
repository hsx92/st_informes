import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import json
from typing import Optional, Dict, Any
import traceback


class StreamlitLogHandler(logging.Handler):
    """Handler personalizado para mostrar logs en Streamlit"""
    
    def emit(self, record):
        """Emite logs a la interfaz de Streamlit según el nivel"""
        try:
            # Solo mostrar en UI si está habilitado
            if not st.session_state.get('show_logs_ui', False):
                return
                
            msg = self.format(record)
            
            if record.levelno >= logging.ERROR:
                st.error(f"🔴 Error: {msg}")
            elif record.levelno >= logging.WARNING:
                if st.secrets.get("SHOW_WARNINGS", False):
                    st.warning(f"⚠️ Advertencia: {msg}")
            elif record.levelno >= logging.INFO:
                if st.secrets.get("DEBUG_MODE", False):
                    st.info(f"ℹ️ Info: {msg}")
        except Exception:
            # Evitar errores en el handler de logging
            pass


class JSONFormatter(logging.Formatter):
    """Formatter que genera logs en formato JSON para análisis"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información adicional si existe
        if hasattr(record, 'user'):
            log_data['user'] = record.user
        if hasattr(record, 'provincia_id'):
            log_data['provincia_id'] = record.provincia_id
        if hasattr(record, 'action'):
            log_data['action'] = record.action
            
        # Agregar traceback si es una excepción
        if record.exc_info:
            log_data['exception'] = traceback.format_exception(*record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class AuditLogger:
    """Logger especializado para auditoría de acciones de usuario"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def log_action(self, action: str, user: str = None, details: Dict[str, Any] = None):
        """Registra una acción de usuario para auditoría"""
        extra = {
            'action': action,
            'user': user or st.session_state.get('username', 'anonymous'),
            'ip': st.session_state.get('remote_ip', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            extra.update(details)
            
        self.logger.info(f"AUDIT: {action}", extra=extra)
    
    def log_data_access(self, provincia_id: int, data_type: str):
        """Registra acceso a datos específicos"""
        self.log_action(
            "data_access",
            details={
                'provincia_id': provincia_id,
                'data_type': data_type,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_export(self, provincia: str, format: str):
        """Registra exportación de datos"""
        self.log_action(
            "data_export",
            details={
                'provincia': provincia,
                'format': format,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_login(self, username: str, success: bool):
        """Registra intentos de login"""
        self.log_action(
            "login_attempt",
            user=username,
            details={
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
        )


def setup_logging(app_name: str = "SICyT_Portal") -> tuple[logging.Logger, AuditLogger]:
    """
    Configura el sistema de logging completo
    
    Args:
        app_name: Nombre de la aplicación para el logger
        
    Returns:
        Tupla con (logger principal, audit_logger)
    """
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Subdirectorios para diferentes tipos de logs
    (log_dir / "app").mkdir(exist_ok=True)
    (log_dir / "audit").mkdir(exist_ok=True)
    (log_dir / "errors").mkdir(exist_ok=True)
    
    # Configurar el logger principal
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG if st.secrets.get("DEBUG_MODE", False) else logging.INFO)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # 1. Handler para archivo de aplicación (rotativo diario)
    app_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "app" / f"{app_name}_{datetime.now():%Y%m}.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    ))
    logger.addHandler(app_handler)
    
    # 2. Handler para archivo JSON (para análisis)
    json_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "app" / f"{app_name}_{datetime.now():%Y%m}.json",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JSONFormatter())
    logger.addHandler(json_handler)
    
    # 3. Handler para errores críticos
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors" / f"{app_name}_errors.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d\n'
        '%(message)s\n'
        'Traceback:\n%(exc_info)s\n' + '=' * 80
    ))
    logger.addHandler(error_handler)
    
    # 4. Handler para consola (solo en desarrollo)
    if st.secrets.get("DEBUG_MODE", False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
    
    # 5. Handler para Streamlit UI
    streamlit_handler = StreamlitLogHandler()
    streamlit_handler.setLevel(logging.WARNING)
    streamlit_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(streamlit_handler)
    
    # Configurar logger de auditoría
    audit_logger_raw = logging.getLogger(f"{app_name}_audit")
    audit_logger_raw.setLevel(logging.INFO)
    audit_logger_raw.handlers.clear()
    
    # Handler específico para auditoría
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "audit" / f"audit_{datetime.now():%Y%m}.log",
        when="midnight",
        interval=1,
        backupCount=90,  # Mantener 3 meses de auditoría
        encoding='utf-8'
    )
    audit_handler.setFormatter(JSONFormatter())
    audit_logger_raw.addHandler(audit_handler)
    
    # Crear wrapper de auditoría
    audit_logger = AuditLogger(audit_logger_raw)
    
    # Configurar niveles para librerías externas
    logging.getLogger("psycopg2").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    # Log inicial
    logger.info(f"Sistema de logging iniciado para {app_name}")
    
    return logger, audit_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtiene un logger configurado
    
    Args:
        name: Nombre del módulo/componente
        
    Returns:
        Logger configurado
    """
    if name:
        return logging.getLogger(f"SICyT_Portal.{name}")
    return logging.getLogger("SICyT_Portal")


# Funciones de utilidad para logging
def log_execution_time(func):
    """Decorador para medir tiempo de ejecución"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            if elapsed > 1:  # Log solo si toma más de 1 segundo
                logger.info(f"{func.__name__} ejecutado en {elapsed:.2f} segundos")
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} falló después de {elapsed:.2f} segundos: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


def log_database_query(query: str, params: Dict = None, execution_time: float = None):
    """Registra consultas a la base de datos"""
    logger = get_logger("database")
    
    if st.secrets.get("LOG_QUERIES", False):
        log_data = {
            'query': query[:500],  # Limitar longitud
            'params': params,
            'execution_time': execution_time
        }
        logger.debug("Query ejecutada", extra=log_data)
