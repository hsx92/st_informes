#!/usr/bin/env python
"""
Script de prueba para el sistema de logging.
Ejecutar con: python test_logging.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from logging_config import setup_logging, get_logger, log_execution_time

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def test_basic_logging():
    """Prueba logging básico en diferentes niveles"""
    print("🧪 Probando logging básico...")
    
    logger = get_logger("test_module")
    
    logger.debug("Mensaje de DEBUG - Solo visible en modo debug")
    logger.info("Mensaje de INFO - Operación normal")
    logger.warning("Mensaje de WARNING - Advertencia")
    logger.error("Mensaje de ERROR - Error recuperable")
    
    try:
        raise ValueError("Error de prueba intencional")
    except ValueError as e:
        logger.error(f"Error capturado con traceback: {e}", exc_info=True)

    print("✅ Logging básico completado")


def test_audit_logging():
    """Prueba el sistema de auditoría"""
    print("🧪 Probando logging de auditoría...")
    
    _, audit_logger = setup_logging("TestApp")
    
    # Simular acciones de usuario
    audit_logger.log_login("usuario_test", success=True)
    audit_logger.log_data_access(provincia_id=1, data_type="ficha_provincial")
    audit_logger.log_export(provincia="Buenos Aires", format="PDF")
    audit_logger.log_action(
        "custom_action",
        user="admin",
        details={"key": "value", "timestamp": datetime.now().isoformat()}
    )
    
    print("✅ Logging de auditoría completado")


@log_execution_time
def slow_function():
    """Función lenta para probar el decorador de tiempo"""
    print("Ejecutando función lenta...")
    time.sleep(2)
    return "Completado"


def test_performance_logging():
    """Prueba el logging de rendimiento"""
    print("🧪 Probando logging de rendimiento...")
    
    result = slow_function()
    print(f"Resultado: {result}")
    
    print("✅ Logging de rendimiento completado")


def test_structured_logging():
    """Prueba logging estructurado con información adicional"""
    print("🧪 Probando logging estructurado...")
    
    logger = get_logger("structured_test")
    
    # Log con información extra
    extra_data = {
        'user': 'test_user',
        'provincia_id': 1,
        'action': 'test_action',
        'metadata': {'key1': 'value1', 'key2': 123}
    }
    
    logger.info("Evento con datos estructurados", extra=extra_data)
    
    print("✅ Logging estructurado completado")


def verify_log_files():
    """Verifica que los archivos de log se hayan creado"""
    print("🔍 Verificando archivos de log...")
    
    log_dir = Path("logs")
    
    if not log_dir.exists():
        print("❌ Directorio de logs no existe")
        return False
    
    # Verificar subdirectorios
    subdirs = ["app", "audit", "errors"]
    for subdir in subdirs:
        path = log_dir / subdir
        if path.exists():
            print(f"✅ Directorio {subdir} existe")
            
            # Listar archivos en el directorio
            files = list(path.glob("*"))
            if files:
                print(f"   Archivos encontrados: {len(files)}")
                for file in files[:3]:  # Mostrar máximo 3 archivos
                    size = file.stat().st_size
                    print(f"   - {file.name} ({size:,} bytes)")
        else:
            print(f"⚠️ Directorio {subdir} no existe")
    
    return True


def test_error_handling():
    """Prueba el manejo de errores en el sistema de logging"""
    print("🧪 Probando manejo de errores...")
    
    logger = get_logger("error_test")
    
    # Intentar diferentes tipos de errores
    errors = [
        (ZeroDivisionError, lambda: 1 / 0),
        (KeyError, lambda: {}['no_existe']),
        (TypeError, lambda: "string" + 123),
        (AttributeError, lambda: None.no_existe())
    ]
    
    for error_type, error_func in errors:
        try:
            error_func()
        except error_type as e:
            logger.error(f"Error tipo {error_type.__name__}: {e}", exc_info=True)
    
    print("✅ Manejo de errores completado")


def main():
    """Función principal de pruebas"""
    print("=" * 60)
    print("SISTEMA DE PRUEBAS DE LOGGING - SICyT Portal")
    print("=" * 60)
    print(f"Iniciando pruebas: {datetime.now()}")
    print()
    
    # Configurar el sistema de logging
    logger, audit_logger = setup_logging("TestSystem")
    logger.info("Sistema de pruebas iniciado")
    
    # Ejecutar todas las pruebas
    tests = [
        test_basic_logging,
        test_audit_logging,
        test_performance_logging,
        test_structured_logging,
        test_error_handling,
    ]
    
    for test_func in tests:
        try:
            test_func()
            print()
        except Exception as e:
            print(f"❌ Error en {test_func.__name__}: {e}")
            logger.error(f"Test falló: {test_func.__name__}", exc_info=True)
    
    # Verificar archivos
    print()
    verify_log_files()
    
    print()
    print("=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("Revisa los archivos en el directorio 'logs/' para ver los resultados")
    print("=" * 60)


if __name__ == "__main__":
    main()
