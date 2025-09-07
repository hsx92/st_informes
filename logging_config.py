"""Centralized logging configuration for the SICyT application.

This module provides a unified logging setup with rotation, formatting,
and different log levels for development and production environments.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Crear directorio de logs si no existe
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configuración de niveles de log
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    app_name: str = "SICyT",
    log_level: str = None,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Configure and return a logger with rotation and formatting.
    
    Args:
        app_name: Name of the application/module for the logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output logs to console
        file_output: Whether to output logs to file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Determinar el nivel de log desde variable de entorno o parámetro
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    level = LOG_LEVELS.get(log_level, logging.INFO)
    
    # Crear logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Formato para los logs
    detailed_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para archivo con rotación
    if file_output:
        timestamp = datetime.now().strftime("%Y%m%d")
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / f"{app_name}_{timestamp}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_format)
        logger.addHandler(file_handler)
    
    # Handler para consola con colores
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Usar formato con colores si es posible
        if os.name != 'nt':  # No Windows
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
        else:
            console_handler.setFormatter(simple_format)
        
        logger.addHandler(console_handler)
    
    # Handler especial para errores críticos
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / f"{app_name}_errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the app's configuration.
    
    Args:
        name: Name for the logger (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"SICyT.{name}")


# Logging decorators
def log_execution(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution with parameters and results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            func_name = func.__name__
            logger.debug(f"Executing {func_name} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed with error: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_database_operation(operation_type: str):
    """Decorator to log database operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            operation_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            
            logger.info(f"[{operation_id}] Starting {operation_type} operation: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"[{operation_id}] {operation_type} operation completed successfully")
                return result
            except Exception as e:
                logger.error(f"[{operation_id}] {operation_type} operation failed: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_user_activity(activity_type: str):
    """Decorator to log user activities."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import streamlit as st
            logger = get_logger(func.__module__)
            
            user = st.session_state.get("username", "anonymous")
            session_id = st.session_state.get("session_id", "unknown")
            
            logger.info(f"User '{user}' (session: {session_id}) - {activity_type}: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Activity '{activity_type}' completed for user '{user}'")
                return result
            except Exception as e:
                logger.error(f"Activity '{activity_type}' failed for user '{user}': {str(e)}")
                raise
        
        return wrapper
    return decorator


# Funciones auxiliares para análisis de logs
def get_recent_errors(hours: int = 24, app_name: str = "SICyT") -> list:
    """Get recent error messages from log files.
    
    Args:
        hours: Number of hours to look back
        app_name: Name of the application
        
    Returns:
        List of recent error log entries
    """
    from datetime import datetime, timedelta
    
    errors = []
    error_log = LOG_DIR / f"{app_name}_errors.log"
    
    if error_log.exists():
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with open(error_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    # Parse timestamp from log line
                    timestamp_str = line.split(' - ')[0]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if timestamp >= cutoff_time:
                        errors.append(line.strip())
                except Exception:
                    continue
    
    return errors


def get_user_activity_summary(username: str = None) -> dict:
    """Get summary of user activities from logs.
    
    Args:
        username: Username to filter (None for all users)
        
    Returns:
        Dictionary with activity summary
    """
    summary = {
        "total_activities": 0,
        "activities_by_type": {},
        "recent_activities": []
    }
    
    # Parse main log file for user activities
    for log_file in LOG_DIR.glob("SICyT_*.log"):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "User" in line and (username is None or username in line):
                    summary["total_activities"] += 1
                    
                    # Extract activity type if present
                    if " - " in line:
                        parts = line.split(" - ")
                        if len(parts) > 2:
                            activity = parts[2].strip()
                            summary["activities_by_type"][activity] = \
                                summary["activities_by_type"].get(activity, 0) + 1
                    
                    # Add to recent activities (last 100)
                    if len(summary["recent_activities"]) < 100:
                        summary["recent_activities"].append(line.strip())
    
    return summary


# Configuración inicial del logger principal
main_logger = setup_logging("SICyT")
main_logger.info("Logging system initialized")

# Export principal
__all__ = [
    'setup_logging',
    'get_logger',
    'log_execution',
    'log_database_operation',
    'log_user_activity',
    'get_recent_errors',
    'get_user_activity_summary'
]
