from logging_config import (
    get_logger,
    get_audit_logger,
    get_performance_logger,
    get_security_logger,
    get_error_logger,
    performance_tracking
)
import time


def test_logging_distribution():
    """Prueba que cada tipo de log vaya a su carpeta correcta."""
    
    # Test app logger
    app_logger = get_logger("test_module")
    app_logger.info("Test message to app/")
    
    # Test audit logger
    audit = get_audit_logger()
    audit.log_login("test_user", success=True)
    
    # Test performance logger
    perf = get_performance_logger()
    perf.log_slow_query("SELECT * FROM test", 2.5)
    
    # Test security logger
    security = get_security_logger()
    security.log_security_event("test_event", {"detail": "test"})
    
    # Test error logger
    error = get_error_logger()
    try:
        raise ValueError("Test error")
    except Exception as e:
        error.log_error(e, {"context": "test"})
    
    # Test performance tracking
    with performance_tracking("test_operation"):
        time.sleep(0.1)
    
    print("✅ Test completado. Verificar las carpetas:")
    print("  - logs/app/ -> mensajes generales")
    print("  - logs/audit/ -> eventos de login")
    print("  - logs/performance/ -> queries y operaciones")
    print("  - logs/security/ -> eventos de seguridad")
    print("  - logs/errors/ -> errores del sistema")


if __name__ == "__main__":
    test_logging_distribution()
