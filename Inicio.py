import streamlit as st
from usuarios import login
from css_utils import load_css

# Configuración de la página
st.set_page_config(
    page_title="Portal - SICyT",
    page_icon=st.secrets.get("LOGO_CORTO", "🏛️"),
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Logo
st.logo(image=st.secrets.get('LOGO_LARGO', ''), size="large")

# CSS
icon_css = load_css("static/iconos/dist/css/icono-arg.css")

# CSS personalizado mejorado
custom_css = """
    /* Estilos generales */
    .main-header {
        background: linear-gradient(90deg, #4D7AAE 0%, #354B6E 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards de noticias */
    .news-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #4D7AAE;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Estilos de formularios */
    .auth-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
    }
    
    /* Botones mejorados */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Métricas del sistema */
    .system-metric {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    
    /* Alertas personalizadas */
    .custom-info {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    
    .custom-success {
        background: linear-gradient(90deg, #e8f5e8 0%, #f1f8e9 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        background: #354B6E;
        color: white;
        border-radius: 10px;
        margin-top: 3rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        .news-card {
            padding: 1rem;
        }
        .auth-container {
            padding: 1rem;
        }
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
"""

# Combinar estilos
combined_css = f"""
<style>
{icon_css}
{custom_css}
</style>
"""


def show_news_section():
    """Muestra la sección de noticias y novedades del sistema"""
    st.markdown("### 📰 Últimas Novedades")
    
    # Noticias del sistema
    news_items = [
        {
            "title": "🔐 Sistema de usuarios mejorado",
            "content": "Se ha implementado un sistema completo de gestión de usuarios con funcionalidades de registro, recuperación de contraseña y administración.",
            "date": "Septiembre 2025",
            "type": "feature"
        },
        {
            "title": "📊 Nuevas visualizaciones disponibles",
            "content": "Se agregaron gráficos interactivos mejorados para las fichas provinciales con mejor rendimiento y opciones de exportación.",
            "date": "Agosto 2025",
            "type": "update"
        },
        {
            "title": "🛡️ Mejoras de seguridad",
            "content": "Implementación de nuevas medidas de seguridad incluyendo validación robusta de contraseñas y protección contra ataques de fuerza bruta.",
            "date": "Agosto 2025",
            "type": "security"
        },
        {
            "title": "📱 Interfaz móvil mejorada",
            "content": "La aplicación ahora cuenta con una interfaz optimizada para dispositivos móviles y tabletas.",
            "date": "Julio 2025",
            "type": "ui"
        }
    ]
    
    for item in news_items:
        icon_map = {
            "feature": "🚀",
            "update": "🔄",
            "security": "🛡️",
            "ui": "🎨"
        }
        
        icon = icon_map.get(item["type"], "📢")
        
        st.markdown(f"""
        <div class="news-card fade-in">
            <h4>{icon} {item["title"]}</h4>
            <p style="color: #666; margin: 0.5rem 0;">{item["date"]}</p>
            <p style="line-height: 1.6;">{item["content"]}</p>
        </div>
        """, unsafe_allow_html=True)


def show_system_status():
    """Muestra el estado general del sistema"""
    st.markdown("### 📊 Estado del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="system-metric">
            <h3 style="color: #4D7AAE; margin: 0;">✅</h3>
            <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Sistema</p>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Operativo</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="system-metric">
            <h3 style="color: #4D7AAE; margin: 0;">🔒</h3>
            <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Seguridad</p>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Activa</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="system-metric">
            <h3 style="color: #4D7AAE; margin: 0;">📊</h3>
            <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Base de Datos</p>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Conectada</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="system-metric">
            <h3 style="color: #4D7AAE; margin: 0;">⚡</h3>
            <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Rendimiento</p>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Óptimo</p>
        </div>
        """, unsafe_allow_html=True)


def show_quick_access():
    """Muestra accesos rápidos para usuarios autenticados"""
    if st.session_state.get("authentication_status"):
        st.markdown("### ⚡ Acceso Rápido")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Fichas Provinciales", use_container_width=True):
                st.switch_page("pages/1_📊_Fichas Provinciales.py")
        
        with col2:
            user_roles = st.session_state.get("roles", [])
            if "admin" in user_roles:
                if st.button("👥 Gestión de Usuarios", use_container_width=True):
                    st.switch_page("pages/Admin_Usuarios.py")
            else:
                st.button("👥 Gestión de Usuarios", disabled=True, help="Requiere permisos de administrador")
        
        with col3:
            if st.button("⚙️ Configuración", use_container_width=True):
                st.info("🔧 Configuración de perfil disponible en el panel de usuario")


def show_help_section():
    """Muestra sección de ayuda y contacto"""
    st.markdown("### 📞 Ayuda y Contacto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="custom-info">
            <h4>🆘 ¿Necesita ayuda?</h4>
            <p>Si tiene problemas para acceder al sistema o necesita asistencia técnica:</p>
            <ul>
                <li>📧 Email: dgicyt@sicyt.gob.ar</li>
                <li>📱 Teléfono: [Número de contacto]</li>
                <li>🕒 Horario: Lunes a Viernes 9:00 - 18:00</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-success">
            <h4>📚 Recursos Útiles</h4>
            <p>Enlaces y recursos importantes:</p>
            <ul>
                <li>📖 Manual de usuario</li>
                <li>🎥 Tutoriales en video</li>
                <li>❓ Preguntas frecuentes</li>
                <li>📋 Formularios de solicitud</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Función principal del portal de inicio"""
    try:
        # Inyectar CSS
        st.markdown(combined_css, unsafe_allow_html=True)
        
        # Header principal
        st.markdown("""
        <div class="main-header fade-in">
            <h1 style="margin: 0; font-size: 2.5rem;">🏛️ Portal SICyT</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                Secretaría de Innovación, Ciencia y Tecnología
            </p>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">
                Sistema de Información y Gestión Científico-Tecnológica
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Contenedor principal para el login
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            # Sistema de autenticación
            login()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Mostrar contenido adicional basado en el estado de autenticación
        if st.session_state.get("authentication_status"):
            # Usuario autenticado - mostrar accesos rápidos
            show_quick_access()
            
            # Información del usuario actual
            col1, col2 = st.columns([2, 1])
            with col1:
                show_news_section()
            with col2:
                show_system_status()
        
        else:
            # Usuario no autenticado - mostrar información general
            col1, col2 = st.columns([2, 1])
            
            with col1:
                show_news_section()
            
            with col2:
                show_system_status()
        
        # Sección de ayuda (siempre visible)
        st.markdown("---")
        show_help_section()
        
        # Footer
        st.markdown("""
        <div class="footer">
            <p style="margin: 0; font-size: 0.9rem;">
                <strong>Secretaría de Innovación, Ciencia y Tecnología</strong><br>
                República Argentina • 2025<br>
                <small>Versión del sistema: 2.1.0</small>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    except KeyError as e:
        st.error(f"❌ Error de configuración: {e}")
        st.info("💡 Verifique que el archivo de configuración esté correctamente configurado.")
        
        # Mostrar información básica incluso con errores
        st.markdown("### ℹ️ Información del Sistema")
        st.write("Portal de la Secretaría de Innovación, Ciencia y Tecnología")
        st.write("Sistema de gestión científico-tecnológica")
        
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        st.info("🔄 Recargue la página o contacte al administrador del sistema.")


if __name__ == "__main__":
    main()
