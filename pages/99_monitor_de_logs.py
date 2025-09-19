"""
Página de monitoreo de logs mejorada para administradores.
Permite visualizar logs en tiempo real, filtrar por nivel y exportar.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
from logging_config import get_logger, get_audit_logger, log_streamlit_component
from auth_manager import get_auth_manager, menu_with_redirect
from typing import Dict, List
from css_utils import load_css

logger = get_logger('log_monitor')
audit_logger = get_audit_logger()

# Configuración de la página
st.set_page_config(
    page_title="Monitor de Logs - SICyT",
    page_icon="🔍",
    layout="wide"
)

st.logo(image=st.secrets['LOGO_LARGO'], size="large")

# Cargar CSS
icon_css = load_css("static/iconos/dist/css/icono-arg.css") if st.secrets.get("USE_ICONS", False) else ""
combined_css = f"""
<style>
{icon_css}
</style>
"""
st.markdown(combined_css, unsafe_allow_html=True)

# Inicializar AuthManager y verificar permisos
auth_manager = get_auth_manager()
auth_manager.require_role('admin')

menu_with_redirect()

# Registrar acceso a la página de logs
audit_logger.log_data_access(
    user=st.session_state.get('username', 'unknown'),
    resource='log_monitor',
    action='view'
)


class LogAnalyzer:
    """Clase para análisis avanzado de logs."""
    
    @staticmethod
    def load_json_logs(log_file: Path, hours: int = 24, filters: Dict = None) -> pd.DataFrame:
        """
        Carga logs JSON con filtros avanzados.
        
        Args:
            log_file: Ruta al archivo de log
            hours: Número de horas hacia atrás para cargar
            filters: Diccionario con filtros adicionales
        
        Returns:
            DataFrame con los logs filtrados
        """
        logs = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        
                        # Filtro temporal
                        log_time = datetime.fromisoformat(log_entry['timestamp'])
                        if log_time <= cutoff_time:
                            continue
                        
                        # Aplicar filtros adicionales
                        if filters:
                            skip = False
                            for key, value in filters.items():
                                if key in log_entry:
                                    if isinstance(value, list):
                                        if log_entry[key] not in value:
                                            skip = True
                                            break
                                    elif log_entry[key] != value:
                                        skip = True
                                        break
                            if skip:
                                continue
                        
                        logs.append(log_entry)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Error parsing log line: {e}")
                        continue
            
            df = pd.DataFrame(logs)
            
            # Convertir timestamp a datetime si existe
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
            
            return df
            
        except FileNotFoundError:
            logger.warning(f"Log file not found: {log_file}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_log_files(log_type: str = "app") -> List[Path]:
        """
        Obtiene lista de archivos de log disponibles.
        
        Args:
            log_type: Tipo de log (app, audit, errors, performance, security)
        
        Returns:
            Lista de archivos de log
        """
        log_dir = Path("logs") / log_type
        if not log_dir.exists():
            return []
        
        # Buscar archivos JSON y LOG
        json_files = list(log_dir.glob("*.json"))
        log_files = list(log_dir.glob("*.log"))
        
        all_files = json_files + log_files
        # Ordenar por fecha de modificación (más reciente primero)
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return all_files
    
    @staticmethod
    def analyze_patterns(df: pd.DataFrame) -> Dict:
        """
        Analiza patrones en los logs.
        
        Args:
            df: DataFrame con logs
        
        Returns:
            Diccionario con análisis de patrones
        """
        if df.empty:
            return {}
        
        analysis = {
            'total_events': len(df),
            'unique_users': df['user'].nunique() if 'user' in df.columns else 0,
            'error_rate': 0,
            'warning_rate': 0,
            'top_errors': [],
            'top_modules': [],
            'peak_hours': [],
            'suspicious_patterns': []
        }
        
        # Calcular tasas de error y warning
        if 'level' in df.columns:
            level_counts = df['level'].value_counts()
            total = len(df)
            analysis['error_rate'] = (level_counts.get('ERROR', 0) / total * 100) if total > 0 else 0
            analysis['warning_rate'] = (level_counts.get('WARNING', 0) / total * 100) if total > 0 else 0
        
        # Top errores
        if 'level' in df.columns and 'message' in df.columns:
            error_df = df[df['level'] == 'ERROR']
            if not error_df.empty:
                top_errors = error_df['message'].value_counts().head(5)
                analysis['top_errors'] = [(msg[:100], count) for msg, count in top_errors.items()]
        
        # Top módulos
        if 'module' in df.columns:
            top_modules = df['module'].value_counts().head(10)
            analysis['top_modules'] = list(top_modules.items())
        
        # Horas pico
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            peak_hours = df['hour'].value_counts().head(3)
            analysis['peak_hours'] = list(peak_hours.index)
        
        # Detectar patrones sospechosos
        analysis['suspicious_patterns'] = LogAnalyzer._detect_suspicious_patterns(df)
        
        return analysis
    
    @staticmethod
    def _detect_suspicious_patterns(df: pd.DataFrame) -> List[str]:
        """Detecta patrones sospechosos en los logs."""
        patterns = []
        
        # Múltiples intentos de login fallidos
        if 'audit_type' in df.columns:
            login_fails = df[(df['audit_type'] == 'login') & (df.get('success') is False)]
            if len(login_fails) > 5:
                patterns.append(f"{len(login_fails)} intentos de login fallidos detectados")
        
        # Muchos errores del mismo tipo
        if 'level' in df.columns and 'error_type' in df.columns:
            error_types = df[df['level'] == 'ERROR']['error_type'].value_counts()
            for error_type, count in error_types.head(3).items():
                if count > 10:
                    patterns.append(f"{count} errores de tipo '{error_type}'")
        
        # Accesos no autorizados
        if 'audit_type' in df.columns:
            denied = df[df['audit_type'] == 'permission_denied']
            if len(denied) > 0:
                patterns.append(f"{len(denied)} intentos de acceso denegado")
        
        # Queries muy lentas
        if 'performance_type' in df.columns:
            slow_queries = df[df['performance_type'] == 'slow_query']
            if len(slow_queries) > 0:
                avg_duration = slow_queries['duration'].mean() if 'duration' in slow_queries.columns else 0
                patterns.append(f"{len(slow_queries)} queries lentas (promedio: {avg_duration:.2f}s)")
        
        return patterns


def render_log_statistics(df: pd.DataFrame):
    """Renderiza estadísticas de logs."""
    st.markdown("### :material/finance: Estadísticas Generales")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total de Eventos",
            f"{len(df):,}",
            delta=None
        )
    
    with col2:
        if 'level' in df.columns:
            errors = len(df[df['level'] == 'ERROR'])
            st.metric(
                "Errores",
                f"{errors:,}",
                delta=f"{(errors/len(df)*100):.1f}%" if len(df) > 0 else "0%",
                delta_color="inverse"
            )
    
    with col3:
        if 'level' in df.columns:
            warnings = len(df[df['level'] == 'WARNING'])
            st.metric(
                "Advertencias",
                f"{warnings:,}",
                delta=f"{(warnings/len(df)*100):.1f}%" if len(df) > 0 else "0%",
                delta_color="inverse"
            )
    
    with col4:
        if 'user' in df.columns:
            unique_users = df['user'].nunique()
            st.metric(
                "Usuarios Únicos",
                f"{unique_users:,}"
            )
    
    with col5:
        if 'module' in df.columns:
            unique_modules = df['module'].nunique()
            st.metric(
                "Módulos Activos",
                f"{unique_modules:,}"
            )


def render_log_charts(df: pd.DataFrame):
    """Renderiza gráficos de análisis de logs."""
    if df.empty:
        st.info("No hay datos para mostrar gráficos")
        return

    tabs = st.tabs([
        ":material/stacked_line_chart: Tendencias",
        ":material/clock_loader_40: Distribución",
        ":material/search_insights: Análisis",
        ":material/electric_bolt: Rendimiento"
    ])

    # Tab 1: Tendencias temporales
    with tabs[0]:
        if 'timestamp' in df.columns and 'level' in df.columns:
            df_time = df.copy()
            df_time['hour'] = pd.to_datetime(df_time['timestamp']).dt.floor('h')
            df_grouped = df_time.groupby(['hour', 'level']).size().reset_index(name='count')
            
            fig = px.line(
                df_grouped,
                x='hour',
                y='count',
                color='level',
                title="Eventos por Hora",
                labels={'hour': 'Hora', 'count': 'Cantidad', 'level': 'Nivel'},
                color_discrete_map={
                    'DEBUG': '#636EFA',
                    'INFO': '#00CC96',
                    'WARNING': '#FFA15A',
                    'ERROR': '#EF553B',
                    'CRITICAL': '#AB63FA'
                }
            )
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            # Heatmap de actividad
            if 'user' in df.columns:
                df_time['day'] = pd.to_datetime(df_time['timestamp']).dt.date
                activity_matrix = df_time.groupby(['day', 'hour', 'user']).size().reset_index(name='events')
                fig_heatmap = px.density_heatmap(
                    activity_matrix,
                    x='hour',
                    y='day',
                    z='events',
                    title="Mapa de Calor de Actividad",
                    labels={'hour': 'Hora del Día', 'day': 'Fecha', 'events': 'Eventos'}
                )
                fig_heatmap.update_yaxes(dtick="D1", tickformat="%d-%m-%Y")
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Tab 2: Distribución
    with tabs[1]:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'level' in df.columns:
                level_counts = df['level'].value_counts()
                fig_pie = px.pie(
                    values=level_counts.values,
                    names=level_counts.index,
                    title="Distribución por Nivel de Log",
                    color_discrete_map={
                        'DEBUG': '#636EFA',
                        'INFO': '#00CC96',
                        'WARNING': '#FFA15A',
                        'ERROR': '#EF553B',
                        'CRITICAL': '#AB63FA'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if 'module' in df.columns:
                top_modules = df['module'].value_counts().head(10)
                fig_bar = px.bar(
                    x=top_modules.values,
                    y=top_modules.index,
                    orientation='h',
                    title="Top 10 Módulos con Más Logs",
                    labels={'x': 'Cantidad', 'y': 'Módulo'},
                    color=top_modules.values,
                    color_continuous_scale='Viridis'
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
    
    # Tab 3: Análisis
    with tabs[2]:
        analysis = LogAnalyzer.analyze_patterns(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### :material/monitoring: Errores y Advertencias")
            st.metric("Tasa de Error", f"{analysis.get('error_rate', 0):.2f}%")
            st.metric("Tasa de Advertencia", f"{analysis.get('warning_rate', 0):.2f}%")
            
            if analysis.get('peak_hours'):
                with st.expander("Horas Pico", icon=":material/pace:"):
                    for hour in analysis['peak_hours']:
                        st.write(f"• {hour}:00 - {hour+1}:00")
        
        with col2:
            if analysis.get('suspicious_patterns'):
                st.markdown("#### :material/mystery: Patrones Detectados")
                for pattern in analysis['suspicious_patterns']:
                    st.warning(pattern, icon=":material/warning:")
            else:
                st.success("No se detectaron patrones sospechosos", icon=":material/check_circle:")

        # Top errores
        if analysis.get('top_errors'):
            st.markdown("#### ❌ Errores Más Frecuentes")
            error_df = pd.DataFrame(analysis['top_errors'], columns=['Error', 'Cantidad'])
            st.dataframe(error_df, use_container_width=True, hide_index=True)
    
    # Tab 4: Rendimiento
    with tabs[3]:
        if 'duration_seconds' in df.columns:
            # Filtrar solo registros con duración
            perf_df = df[df['duration_seconds'].notna()]
            
            if not perf_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histograma de tiempos de respuesta
                    fig_hist = px.histogram(
                        perf_df,
                        x='duration_seconds',
                        nbins=50,
                        title="Distribución de Tiempos de Respuesta",
                        labels={'duration_seconds': 'Duración (segundos)', 'count': 'Frecuencia'}
                    )
                    fig_hist.add_vline(
                        x=perf_df['duration_seconds'].median(),
                        line_dash="dash",
                        annotation_text=f"Mediana: {perf_df['duration_seconds'].median():.2f}s"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Top operaciones lentas
                    if 'function' in perf_df.columns:
                        slow_ops = perf_df.nlargest(10, 'duration_seconds')[['function', 'duration_seconds']]
                        fig_slow = px.bar(
                            slow_ops,
                            x='duration_seconds',
                            y='function',
                            orientation='h',
                            title="Top 10 Operaciones Más Lentas",
                            labels={'duration_seconds': 'Duración (s)', 'function': 'Función'},
                            color='duration_seconds',
                            color_continuous_scale='Reds'
                        )
                        fig_slow.update_layout(showlegend=False)
                        st.plotly_chart(fig_slow, use_container_width=True)
                
                # Métricas de rendimiento
                st.markdown("#### 📊 Estadísticas de Rendimiento")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Tiempo Promedio", f"{perf_df['duration_seconds'].mean():.3f}s")
                with col2:
                    st.metric("Tiempo Mediano", f"{perf_df['duration_seconds'].median():.3f}s")
                with col3:
                    st.metric("Tiempo Máximo", f"{perf_df['duration_seconds'].max():.3f}s")
                with col4:
                    slow_count = len(perf_df[perf_df['duration_seconds'] > 1.0])
                    st.metric("Operaciones > 1s", f"{slow_count:,}")
        else:
            st.info("No hay datos de rendimiento disponibles")


def render_detailed_logs(df: pd.DataFrame):
    """Renderiza vista detallada de logs."""
    st.markdown("### :material/overview: Logs Detallados")
    
    # Filtros adicionales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'module' in df.columns:
            modules = st.multiselect(
                "Filtrar por Módulo",
                options=sorted(df['module'].dropna().unique()),
                key="filter_module"
            )
            if modules:
                df = df[df['module'].isin(modules)]
    
    with col2:
        if 'user' in df.columns:
            users = st.multiselect(
                "Filtrar por Usuario",
                options=sorted(df['user'].dropna().unique()),
                key="filter_user"
            )
            if users:
                df = df[df['user'].isin(users)]
    
    with col3:
        if 'function' in df.columns:
            functions = st.multiselect(
                "Filtrar por Función",
                options=sorted(df['function'].dropna().unique()),
                key="filter_function"
            )
            if functions:
                df = df[df['function'].isin(functions)]
    
    with col4:
        search_term = st.text_input(
            "Buscar en mensajes",
            placeholder="Término de búsqueda...",
            key="search_logs"
        )
        if search_term and 'message' in df.columns:
            df = df[df['message'].str.contains(search_term, case=False, na=False)]
    
    # Información de filtrado
    st.info(f"Mostrando {len(df):,} eventos")
    
    # Formato de visualización
    display_format = st.radio(
        "Formato de visualización",
        ["Tabla Interactiva", "JSON Expandible", "Texto Plano"],
        horizontal=True,
        key="display_format"
    )
    
    if display_format == "Tabla Interactiva":
        # Seleccionar columnas a mostrar
        available_cols = df.columns.tolist()
        default_cols = ['timestamp', 'level', 'user', 'module', 'function', 'message']
        default_cols = [c for c in default_cols if c in available_cols]
        
        selected_cols = st.multiselect(
            "Columnas a mostrar",
            available_cols,
            default=default_cols,
            key="select_columns"
        )
        
        if selected_cols:
            # Configurar display de columnas
            column_config = {}
            
            if 'timestamp' in selected_cols:
                column_config['timestamp'] = st.column_config.DatetimeColumn(
                    "Timestamp",
                    format="DD/MM/YYYY HH:mm:ss"
                )
            
            if 'level' in selected_cols:
                column_config['level'] = st.column_config.TextColumn(
                    "Nivel",
                    width="small"
                )
            
            if 'duration_seconds' in selected_cols:
                column_config['duration_seconds'] = st.column_config.ProgressColumn(
                    "Duración (s)",
                    min_value=0,
                    max_value=df['duration_seconds'].max() if 'duration_seconds' in df.columns else 10,
                    format="%.3f"
                )
            
            # Mostrar tabla
            st.dataframe(
                df[selected_cols].head(500),
                use_container_width=True,
                height=600,
                column_config=column_config,
                hide_index=True
            )
    
    elif display_format == "JSON Expandible":
        # Limitar a 100 registros para rendimiento
        for idx, row in df.head(100).iterrows():
            timestamp = row.get('timestamp', 'N/A')
            level = row.get('level', 'INFO')
            message = row.get('message', 'Sin mensaje')[:100]
            
            # Color del expander según el nivel
            level_colors = {
                'ERROR': '🔴',
                'WARNING': '🟡',
                'INFO': '🟢',
                'DEBUG': '🔵',
                'CRITICAL': '🟣'
            }
            icon = level_colors.get(level, '⚪')
            
            with st.expander(f"{icon} {timestamp} - {level} - {message}"):
                # Convertir row a dict y manejar tipos no serializables
                row_dict = {}
                for key, value in row.items():
                    # CORRECCIÓN: Manejar arrays y valores escalares correctamente
                    try:
                        # Verificar si el valor es un escalar
                        if pd.api.types.is_scalar(value):
                            # Para valores escalares, usar pd.notna normalmente
                            if pd.notna(value):
                                if isinstance(value, pd.Timestamp):
                                    row_dict[key] = value.isoformat()
                                else:
                                    row_dict[key] = value
                        else:
                            # Para arrays, listas o Series, convertir a lista
                            if hasattr(value, 'tolist'):
                                # Es un array numpy o Series pandas
                                row_dict[key] = value.tolist()
                            elif isinstance(value, (list, tuple)):
                                # Ya es una lista o tupla
                                row_dict[key] = list(value)
                            else:
                                # Intentar convertir a string como fallback
                                row_dict[key] = str(value)
                    except Exception as e:
                        # Si algo falla, convertir a string
                        logger.debug(f"Error procesando valor para key '{key}': {e}")
                        row_dict[key] = str(value) if value is not None else None
                
                st.json(row_dict)
    
    else:  # Texto Plano
        # Formatear como logs tradicionales
        log_lines = []
        for _, row in df.head(200).iterrows():
            timestamp = row.get('timestamp', 'N/A')
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            level = row.get('level', 'INFO')
            module = row.get('module', 'N/A')
            message = row.get('message', 'N/A')
            
            log_line = f"{timestamp} | {level:8} | {module:20} | {message}"
            log_lines.append(log_line)
        
        st.text_area(
            "Logs (últimos 200)",
            value='\n'.join(log_lines),
            height=600,
            key="plain_text_logs"
        )


def generate_analysis_report(df: pd.DataFrame, analysis: Dict) -> str:
    """
    Genera un reporte de análisis de logs.
    
    Args:
        df: DataFrame con logs
        analysis: Diccionario con análisis
    
    Returns:
        String con el reporte
    """
    report = []
    report.append("=" * 80)
    report.append("REPORTE DE ANÁLISIS DE LOGS - SISTEMA SICyT")
    report.append("=" * 80)
    report.append(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Usuario: {st.session_state.get('username', 'unknown')}")
    report.append("")
    
    # Resumen ejecutivo
    report.append("RESUMEN EJECUTIVO")
    report.append("-" * 40)
    report.append(f"Total de eventos analizados: {analysis.get('total_events', 0):,}")
    report.append(f"Usuarios únicos: {analysis.get('unique_users', 0)}")
    report.append(f"Tasa de error: {analysis.get('error_rate', 0):.2f}%")
    report.append(f"Tasa de advertencia: {analysis.get('warning_rate', 0):.2f}%")
    report.append("")
    
    # Distribución por nivel
    if 'level' in df.columns:
        report.append("DISTRIBUCIÓN POR NIVEL DE LOG")
        report.append("-" * 40)
        level_counts = df['level'].value_counts()
        for level, count in level_counts.items():
            percentage = (count / len(df) * 100) if len(df) > 0 else 0
            report.append(f"{level:10s}: {count:6,} ({percentage:5.2f}%)")
        report.append("")
    
    # Top errores
    if analysis.get('top_errors'):
        report.append("TOP 5 ERRORES MÁS FRECUENTES")
        report.append("-" * 40)
        for i, (error, count) in enumerate(analysis['top_errors'], 1):
            report.append(f"{i}. [{count:3}] {error}")
        report.append("")
    
    # Top módulos
    if analysis.get('top_modules'):
        report.append("TOP 10 MÓDULOS CON MÁS ACTIVIDAD")
        report.append("-" * 40)
        for i, (module, count) in enumerate(analysis['top_modules'], 1):
            report.append(f"{i:2}. {module:30s}: {count:,}")
        report.append("")
    
    # Patrones sospechosos
    if analysis.get('suspicious_patterns'):
        report.append("PATRONES SOSPECHOSOS DETECTADOS")
        report.append("-" * 40)
        for pattern in analysis['suspicious_patterns']:
            report.append(f"• {pattern}")
        report.append("")
    
    # Estadísticas temporales
    if 'timestamp' in df.columns:
        report.append("ESTADÍSTICAS TEMPORALES")
        report.append("-" * 40)
        
        timestamps = pd.to_datetime(df['timestamp'])
        report.append(f"Primer evento: {timestamps.min()}")
        report.append(f"Último evento: {timestamps.max()}")
        report.append(f"Duración total: {timestamps.max() - timestamps.min()}")
        
        if analysis.get('peak_hours'):
            report.append(f"Horas pico: {', '.join([f'{h}:00' for h in analysis['peak_hours']])}")
        report.append("")
    
    # Estadísticas de rendimiento
    if 'duration_seconds' in df.columns:
        perf_df = df[df['duration_seconds'].notna()]
        if not perf_df.empty:
            report.append("ESTADÍSTICAS DE RENDIMIENTO")
            report.append("-" * 40)
            report.append(f"Operaciones analizadas: {len(perf_df):,}")
            report.append(f"Tiempo promedio: {perf_df['duration_seconds'].mean():.3f}s")
            report.append(f"Tiempo mediano: {perf_df['duration_seconds'].median():.3f}s")
            report.append(f"Tiempo mínimo: {perf_df['duration_seconds'].min():.3f}s")
            report.append(f"Tiempo máximo: {perf_df['duration_seconds'].max():.3f}s")
            report.append(f"Desviación estándar: {perf_df['duration_seconds'].std():.3f}s")
            
            slow_ops = len(perf_df[perf_df['duration_seconds'] > 1.0])
            report.append(f"Operaciones > 1s: {slow_ops:,} ({slow_ops/len(perf_df)*100:.2f}%)")
            report.append("")
    
    # Usuarios más activos
    if 'user' in df.columns:
        report.append("TOP 10 USUARIOS MÁS ACTIVOS")
        report.append("-" * 40)
        top_users = df['user'].value_counts().head(10)
        for i, (user, count) in enumerate(top_users.items(), 1):
            percentage = (count / len(df) * 100) if len(df) > 0 else 0
            report.append(f"{i:2}. {user:20s}: {count:6,} eventos ({percentage:5.2f}%)")
        report.append("")
    
    # Recomendaciones
    report.append("RECOMENDACIONES")
    report.append("-" * 40)
    
    recommendations = []
    
    if analysis.get('error_rate', 0) > 5:
        recommendations.append("⚠️ Alta tasa de errores detectada. Revisar logs de ERROR para identificar problemas.")
    
    if analysis.get('warning_rate', 0) > 20:
        recommendations.append("⚠️ Muchas advertencias. Revisar configuración y validaciones.")
    
    if 'duration_seconds' in df.columns:
        slow_count = len(df[df['duration_seconds'] > 2.0]) if 'duration_seconds' in df.columns else 0
        if slow_count > 10:
            recommendations.append("🐌 Múltiples operaciones lentas detectadas. Considerar optimización.")
    
    if analysis.get('suspicious_patterns'):
        recommendations.append("🔒 Patrones sospechosos detectados. Revisar seguridad del sistema.")
    
    if not recommendations:
        recommendations.append("✅ No se detectaron problemas significativos.")
    
    for rec in recommendations:
        report.append(f"• {rec}")
    
    report.append("")
    report.append("=" * 80)
    report.append("FIN DEL REPORTE")
    report.append("=" * 80)
    
    return "\n".join(report)


# PÁGINA PRINCIPAL
@log_streamlit_component('log_monitor_main')
def main():
    """Función principal del monitor de logs."""
    
    # Header
    col1, col2 = st.columns([1, 9], vertical_alignment='center')
    with col1:
        if st.secrets.get("USE_ICONS", False):
            st.markdown("""
                <div class="icon-container">
                    <i class="icono-arg-lupa-engranaje" style="font-size: 76px; color: #FFFFFF;"></i>
                </div>
                """, unsafe_allow_html=True)
    with col2:
        st.header("Monitor de Logs del Sistema")
        st.write("Herramientas de monitoreo del sistema. Visualiza, filtra y analiza logs en tiempo real.")

    st.markdown("---")
    
    # Sidebar con controles principales
    with st.sidebar:
        st.markdown('### :material/page_info: Filtros:', unsafe_allow_html=True)

        # Selector de tipo de log
        log_types = ["Todos", "Aplicación", "Auditoría", "Errores", "Rendimiento", "Seguridad"]
        log_type = st.selectbox(
            "Tipo de Log",
            log_types,
            key="log_type",
            index=0
        )
        
        # Selector de archivo específico
        if log_type != "Todos":
            log_dir_map = {
                "Aplicación": "app",
                "Auditoría": "audit",
                "Errores": "errors",
                "Rendimiento": "performance",
                "Seguridad": "security"
            }
            log_dir = log_dir_map.get(log_type, "app")
            available_files = LogAnalyzer.get_log_files(log_dir)
            
            if available_files:
                selected_file = st.selectbox(
                    "Archivo de Log",
                    available_files,
                    format_func=lambda x: f"{x.name} ({x.stat().st_size / 1024:.1f} KB)",
                    key="log_file"
                )
            else:
                st.warning(f"No hay archivos de log en {log_dir}/", icon=":material/warning:")
                selected_file = None
        else:
            selected_file = None
        
        # Rango de tiempo
        time_ranges = {
            "Última hora": 1,
            "Últimas 6 horas": 6,
            "Últimas 24 horas": 24,
            "Últimos 3 días": 72,
            "Última semana": 168,
            "Último mes": 720
        }
        
        time_range = st.selectbox(
            "Rango de Tiempo",
            list(time_ranges.keys()),
            index=2,
            key="time_range"
        )
        hours = time_ranges[time_range]
        
        # Filtro por nivel
        log_levels = st.multiselect(
            "Niveles de Log",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=["INFO", "WARNING", "ERROR", "CRITICAL"],
            key="log_levels"
        )
        
        # Botón de actualización manual
        if st.button("Actualizar registros", icon=':material/autorenew:', use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # Exportar logs centrado en la barra lateral
        st.markdown('### :material/download: Descargar:', unsafe_allow_html=True)

    # Cargar logs según configuración
    all_logs = pd.DataFrame()
    
    if log_type == "Todos":
        # Cargar logs de todos los tipos
        for log_dir in ["app", "audit", "errors", "performance", "security"]:
            files = LogAnalyzer.get_log_files(log_dir)
            for file in files[:2]:  # Limitar a 2 archivos más recientes por tipo
                if file.suffix == '.json':
                    df = LogAnalyzer.load_json_logs(
                        file,
                        hours=hours,
                        filters={'level': log_levels} if log_levels else None
                    )
                    if not df.empty:
                        df['log_type'] = log_dir
                        all_logs = pd.concat([all_logs, df], ignore_index=True)
    elif selected_file:
        # Cargar archivo específico
        if selected_file.suffix == '.json':
            all_logs = LogAnalyzer.load_json_logs(
                selected_file,
                hours=hours,
                filters={'level': log_levels} if log_levels else None
            )
            if not all_logs.empty:
                all_logs['log_type'] = log_type.lower()
    
    # Verificar si hay datos
    if all_logs.empty:
        st.warning("No hay logs disponibles para el período y filtros seleccionados", icon=":material/warning:")
        
        # Mostrar información de debug
        with st.expander("🔧 Información de Debug"):
            st.write("Directorios de logs:")
            for subdir in ["app", "audit", "errors", "performance", "security"]:
                path = Path("logs") / subdir
                if path.exists():
                    files = list(path.glob("*"))
                    st.write(f"• {subdir}: {len(files)} archivos")
                else:
                    st.write(f"• {subdir}: No existe")
        return
    
    # Ordenar por timestamp
    if 'timestamp' in all_logs.columns:
        all_logs = all_logs.sort_values('timestamp', ascending=False)
    
    # Mostrar estadísticas
    render_log_statistics(all_logs)
    
    st.markdown("---")
    
    # Mostrar gráficos
    render_log_charts(all_logs)
    
    st.markdown("---")
    
    # Mostrar logs detallados
    render_detailed_logs(all_logs)
    
    # Sidebar - Sección de exportación
    with st.sidebar:
        if not all_logs.empty:
            # Preparar datos para exportación
            export_df = all_logs.copy()
            
            # Convertir timestamp a string para CSV
            if 'timestamp' in export_df.columns:
                export_df['timestamp'] = export_df['timestamp'].astype(str)
            
            # CSV
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Descargar CSV",
                icon=":material/download:",
                data=csv,
                file_name=f"logs_{datetime.now():%Y%m%d_%H%M%S}.csv",
                mime="text/csv",
                use_container_width=True,
                on_click=lambda: audit_logger.log_export(
                    user=st.session_state.get('username', 'unknown'),
                    data_type='logs',
                    format='csv',
                    records_count=len(export_df)
                )
            )
            
            # JSON
            json_data = export_df.to_json(orient='records', date_format='iso')
            st.download_button(
                label="Descargar JSON",
                icon=":material/download:",
                data=json_data,
                file_name=f"logs_{datetime.now():%Y%m%d_%H%M%S}.json",
                mime="application/json",
                use_container_width=True,
                on_click=lambda: audit_logger.log_export(
                    user=st.session_state.get('username', 'unknown'),
                    data_type='logs',
                    format='json',
                    records_count=len(export_df)
                )
            )
            
            # Reporte de análisis
            analysis = LogAnalyzer.analyze_patterns(all_logs)
            report = generate_analysis_report(all_logs, analysis)
            st.download_button(
                label="Descargar Reporte",
                icon=":material/download:",
                data=report,
                file_name=f"log_report_{datetime.now():%Y%m%d_%H%M%S}.txt",
                mime="text/plain",
                use_container_width=True,
                on_click=lambda: audit_logger.log_export(
                    user=st.session_state.get('username', 'unknown'),
                    data_type='log_report',
                    format='txt',
                    records_count=len(all_logs)
                )
            )


# Ejecutar aplicación
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error crítico en Monitor de Logs: {e}", exc_info=True)
        st.error("Error crítico. Por favor contacte al administrador.", icon=":material/close:")
        
        # Mostrar detalles del error solo a administradores
        if st.session_state.get('roles') and 'admin' in st.session_state.get('roles'):
            with st.expander("Detalles del Error"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())
