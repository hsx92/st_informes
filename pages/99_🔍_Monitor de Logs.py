"""
Página de monitoreo de logs para administradores.
Permite visualizar logs en tiempo real, filtrar por nivel y exportar.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
from logging_config import get_logger
from auth_manager import get_auth_manager

logger = get_logger(__name__)

st.set_page_config(
    page_title="Monitor de Logs - SICyT",
    page_icon="🔍",
    layout="wide"
)

st.logo(image=st.secrets['LOGO_LARGO'], size="large")

# Inicializar AuthManager
auth_manager = get_auth_manager()
auth_manager.require_role('admin')


def load_json_logs(log_file: Path, hours: int = 24) -> pd.DataFrame:
    """Carga logs JSON de las últimas N horas"""
    logs = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    log_time = datetime.fromisoformat(log_entry['timestamp'])
                    
                    if log_time > cutoff_time:
                        logs.append(log_entry)
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        return pd.DataFrame(logs)
    except FileNotFoundError:
        return pd.DataFrame()


def load_audit_logs(hours: int = 24) -> pd.DataFrame:
    """Carga logs de auditoría"""
    audit_dir = Path("logs/audit")
    current_file = audit_dir / f"audit_{datetime.now():%Y%m}.log"
    
    if current_file.exists():
        return load_json_logs(current_file, hours)
    return pd.DataFrame()


# ---- AUTENTICACIÓN Y AUTORIZACIÓN ----
try:
    st.title("🔍 Monitor de Logs del Sistema")
    
    # Verificar permisos de administrador
    if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
        st.warning("Debe estar autenticado para acceder a esta página")
        st.stop()
        
    if 'admin' not in st.session_state.get('roles', []):
        st.error("Acceso restringido a administradores")
        logger.warning(f"Intento de acceso no autorizado al monitor de logs por {st.session_state.get('username')}")
        st.stop()
    
    # Controles de filtrado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        log_type = st.selectbox(
            "Tipo de Log",
            ["Aplicación", "Auditoría", "Errores", "Todos"]
        )
    
    with col2:
        time_range = st.selectbox(
            "Rango de Tiempo",
            ["Última hora", "Últimas 6 horas", "Últimas 24 horas", "Última semana"]
        )
    
    with col3:
        log_level = st.multiselect(
            "Nivel de Log",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=["INFO", "WARNING", "ERROR", "CRITICAL"]
        )
    
    with col4:
        auto_refresh = st.checkbox("Auto-actualizar (30s)")
    
    # Mapear rango de tiempo a horas
    time_map = {
        "Última hora": 1,
        "Últimas 6 horas": 6,
        "Últimas 24 horas": 24,
        "Última semana": 168
    }
    hours = time_map[time_range]
    
    # Auto-refresh
    if auto_refresh:
        st.empty()
        import time
        time.sleep(30)
        st.rerun()
    
    # Cargar logs según el tipo seleccionado
    if log_type == "Auditoría":
        df_logs = load_audit_logs(hours)
        st.subheader("📋 Logs de Auditoría")
    else:
        # Cargar logs de aplicación
        log_dir = Path("logs/app")
        current_file = log_dir / f"SICyT_Portal_{datetime.now():%Y%m}.json"
        df_logs = load_json_logs(current_file, hours) if current_file.exists() else pd.DataFrame()
        st.subheader("📊 Logs de Aplicación")
    
    if df_logs.empty:
        st.info("No hay logs disponibles para el período seleccionado")
    
    # Filtrar por nivel
    if 'level' in df_logs.columns and log_level:
        df_logs = df_logs[df_logs['level'].isin(log_level)]
    
    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Eventos", len(df_logs))
    
    with col2:
        if 'level' in df_logs.columns:
            errors = len(df_logs[df_logs['level'] == 'ERROR'])
            st.metric("Errores", errors, delta=None if errors == 0 else "⚠️")
    
    with col3:
        if 'level' in df_logs.columns:
            warnings = len(df_logs[df_logs['level'] == 'WARNING'])
            st.metric("Advertencias", warnings)
    
    with col4:
        if 'user' in df_logs.columns:
            unique_users = df_logs['user'].nunique()
            st.metric("Usuarios Únicos", unique_users)
    
    # Gráficos de análisis
    st.markdown("---")
    
    if not df_logs.empty:
        # Convertir timestamp a datetime si es string
        if 'timestamp' in df_logs.columns:
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
        
        tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📊 Distribución", "📝 Logs Detallados"])
        
        with tab1:
            if 'timestamp' in df_logs.columns and 'level' in df_logs.columns:
                # Gráfico de tendencia temporal
                df_time = df_logs.copy()
                df_time['hour'] = df_time['timestamp'].dt.floor('H')
                df_grouped = df_time.groupby(['hour', 'level']).size().reset_index(name='count')
                
                fig = px.line(
                    df_grouped,
                    x='hour',
                    y='count',
                    color='level',
                    title="Eventos por Hora",
                    labels={'hour': 'Hora', 'count': 'Cantidad', 'level': 'Nivel'},
                    color_discrete_map={
                        'DEBUG': '#808080',
                        'INFO': "#83A2EB",
                        'WARNING': '#FFA500',
                        'ERROR': '#FF0000',
                        'CRITICAL': "#680202"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                if 'level' in df_logs.columns:
                    # Distribución por nivel
                    level_counts = df_logs['level'].value_counts()
                    fig_pie = px.pie(
                        values=level_counts.values,
                        names=level_counts.index,
                        title="Distribución por Nivel de Log",
                        color_discrete_map={
                            'DEBUG': 'gray',
                            'INFO': 'blue',
                            'WARNING': 'orange',
                            'ERROR': 'red',
                            'CRITICAL': 'darkred'
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                if 'module' in df_logs.columns:
                    # Top módulos con más logs
                    top_modules = df_logs['module'].value_counts().head(10)
                    fig_bar = px.bar(
                        x=top_modules.values,
                        y=top_modules.index,
                        orientation='h',
                        title="Top 10 Módulos con Más Logs",
                        labels={'x': 'Cantidad', 'y': 'Módulo'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab3:
            # Filtros adicionales para logs detallados
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'module' in df_logs.columns:
                    modules = st.multiselect(
                        "Filtrar por Módulo",
                        df_logs['module'].unique()
                    )
                    if modules:
                        df_logs = df_logs[df_logs['module'].isin(modules)]
            
            with col2:
                if 'user' in df_logs.columns:
                    users = st.multiselect(
                        "Filtrar por Usuario",
                        df_logs['user'].dropna().unique()
                    )
                    if users:
                        df_logs = df_logs[df_logs['user'].isin(users)]
            
            with col3:
                search_term = st.text_input("Buscar en mensajes", "")
                if search_term and 'message' in df_logs.columns:
                    df_logs = df_logs[df_logs['message'].str.contains(search_term, case=False, na=False)]
            
            # Mostrar logs
            st.subheader(f"Mostrando {len(df_logs)} eventos")
            
            # Formato de visualización
            display_format = st.radio(
                "Formato de visualización",
                ["Tabla", "JSON", "Texto plano"],
                horizontal=True
            )
            
            if display_format == "Tabla":
                # Seleccionar columnas a mostrar
                available_cols = df_logs.columns.tolist()
                default_cols = ['timestamp', 'level', 'message', 'module', 'user']
                default_cols = [c for c in default_cols if c in available_cols]
                
                selected_cols = st.multiselect(
                    "Columnas a mostrar",
                    available_cols,
                    default=default_cols
                )
                
                if selected_cols:
                    st.dataframe(
                        df_logs[selected_cols].sort_values('timestamp', ascending=False),
                        use_container_width=True,
                        height=600
                    )
            
            elif display_format == "JSON":
                # Mostrar como JSON expandible
                for idx, row in df_logs.sort_values('timestamp', ascending=False).head(100).iterrows():
                    with st.expander(f"{row.get('timestamp', 'N/A')} - {row.get('level', 'N/A')} - {row.get('message', 'N/A')[:100]}"):
                        st.json(row.to_dict())
            
            else:  # Texto plano
                # Formatear como logs tradicionales
                log_text = []
                for _, row in df_logs.sort_values('timestamp', ascending=False).head(100).iterrows():
                    log_line = f"{row.get('timestamp', 'N/A')} | {row.get('level', 'INFO'):8} | {row.get('module', 'N/A'):20} | {row.get('message', 'N/A')}"
                    log_text.append(log_line)
                
                st.text_area(
                    "Logs (últimos 100)",
                    value='\n'.join(log_text),
                    height=600
                )
    
    # Exportar logs
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if not df_logs.empty:
            csv = df_logs.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Logs (CSV)",
                data=csv,
                file_name=f"logs_{datetime.now():%Y%m%d_%H%M%S}.csv",
                mime="text/csv"
            )

except Exception as e:
    logger.critical(f"Error crítico en página Monitor de Logs: {e}", exc_info=True)
    st.error("Error crítico. Por favor contacte al administrador.")
    st.stop()
