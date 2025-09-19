"""Streamlit page for displaying provincial dashboards.

This module defines the :func:`panomProvincial` function, which renders
key metrics, tables, and charts for a selected province and allows
exporting the report to PDF.
"""

import streamlit as st
from streamlit_extras.great_tables import great_tables
from streamlit_extras.metric_cards import style_metric_cards
from sources import get_provincias
from pdf_builder import ficha_provincial_pdf
from ficha_builder import ficha_provincial_figs, preparar_data_pdf
from css_utils import load_css, get_metric_css
from auth_manager import get_auth_manager, menu_with_redirect
from logging_config import get_logger, get_audit_logger, log_streamlit_component
from typing import Optional, Dict


logger = get_logger('fichas_provinciales')
audit_logger = get_audit_logger()


def log_export_action(format_type: str):
    """Log export/download actions."""
    user = st.session_state.get("username", "unknown")
    provincia = st.session_state.get('provincia', 'unknown')
    logger.info(f"User '{user}' exported {format_type} for provincia '{provincia}'")


# Configuración de la página
st.set_page_config(
    page_title="Fichas Provinciales - SICyT",
    page_icon=st.secrets["LOGO_CORTO"],
    layout="wide"
)
st.logo(image=st.secrets["LOGO_LARGO"], size="large")

# ---- CSS MEJORADO ----
icon_css = load_css("static/iconos/dist/css/icono-arg.css")
metric_css = get_metric_css("dark")

# CSS adicional específico para esta página
page_specific_css = """
/* Tabs mejorados */
.stTabs [data-baseweb="tab-list"] {
    background-color: rgba(53, 75, 110, 0.3);
    border-radius: 8px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    color: #B4C6DB;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="false"][data-baseweb="tab"]:hover {
    background-color: #54698B !important;
    color: #FFFFFF !important;
    border-radius: 4px;
}

/* Selectbox mejorado */
.stSelectbox > div > div {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid #7589A3 !important;
}

/* Captions con mejor visibilidad */
.stCaption {
    color: #8B9DC3 !important;
    font-style: italic;
    font-size: 0.85rem;
}

/* Contenedor de métricas mejorado */
div[data-testid="metric-container"] {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(117, 137, 163, 0.2);
    padding: 1rem;
    border-radius: 8px;
    transition: all 0.3s ease;
}

div[data-testid="metric-container"]:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border-color: rgba(117, 137, 163, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Headers mejorados */
h2 {
    color: #E3E7ED !important;
    border-bottom: 2px solid #54698B;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Botón de exportar con estilo destacado */
.export-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    transition: all 0.3s ease !important;
}

.export-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

/* Loading spinner mejorado */
.stSpinner > div {
    border-color: #7DD3C0 !important;
}
"""

combined_css = f"""
<style>
{icon_css}
{metric_css}
{page_specific_css}
</style>
"""

# Inyectar el CSS en la aplicación
st.markdown(combined_css, unsafe_allow_html=True)

# Inicializar AuthManager
auth_manager = get_auth_manager()
auth_manager.require_any_role(['admin', 'director'])

menu_with_redirect()


# ---- FUNCIONES AUXILIARES ----
def load_provincial_data(provincia_id: int, provincia: str, anio: str) -> Optional[Dict]:
    """Load and process provincial data with error handling and logging."""
    try:
        with st.spinner(f"Cargando datos para {provincia}..."):
            DFs = ficha_provincial_figs(
                provincia_id=provincia_id,
                provincia=provincia,
                anio=anio
            )
        logger.info(f"Successfully loaded data for {provincia} ({provincia_id})")
        return DFs
    except Exception as e:
        logger.error(f"Failed to load data for {provincia}: {str(e)}")
        st.error(f"Error al cargar los datos de {provincia}. Por favor, intente nuevamente.", icon=":material/close:")
        return None


def render_metric_with_icon(icon: str, title: str, value: str, delta: str = None, help_text: str = None):
    """Render a metric with an icon and optional help text."""
    col1, col2 = st.columns([1, 11])
    with col1:
        st.markdown(
            f'<i class="{icon}" style="font-size: 24px; color: #7DD3C0;"></i>',
            unsafe_allow_html=True
        )
    with col2:
        if help_text:
            st.metric(label=f":primary[{title}]", value=value, delta=delta, help=help_text)
        else:
            st.metric(label=f":primary[{title}]", value=value, delta=delta)


def render_chart_with_source(component: Dict, use_container_width: bool = True):
    """Render a chart with its source caption."""
    if component.get('figura') is not None:
        st.plotly_chart(component['figura'], use_container_width=use_container_width)
        if component.get('fuente'):
            st.caption(f"Fuente: {component['fuente']}")


def render_table_with_source(component: Dict):
    """Render a great_tables table with its source caption."""
    if component.get('figura') is not None:
        great_tables(component['figura'])
        if component.get('fuente'):
            st.caption(f"Fuente: {component['fuente']}")


def generate_pdf_report(provincia: str, data: Dict) -> bool:
    """Generate PDF report with error handling and logging."""
    try:
        with st.spinner("Generando reporte PDF..."):
            processed_data = preparar_data_pdf(data)
            output_path = f"output/Ficha Provincial - {provincia}.pdf"
            ficha_provincial_pdf(provincia, processed_data, output_path)
            
        log_export_action("PDF")
        st.success(f"Reporte PDF generado exitosamente: {output_path}", icon=":material/check_circle:")
        logger.info(f"PDF report generated successfully for {provincia}")
        
        # Mostrar botón de descarga si el archivo existe
        try:
            with open(output_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Descargar PDF",
                    icon=":material/download:",
                    data=pdf_bytes,
                    file_name=f"Ficha_Provincial_{provincia}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
        except FileNotFoundError:
            logger.error(f"PDF file not found: {output_path}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error generating PDF for {provincia}: {str(e)}")
        st.error(f"Error al generar el reporte PDF: {str(e)}", icon=":material/close:")
        return False


# ---- PÁGINA PRINCIPAL ----
@log_streamlit_component('fichas_provinciales_main')
def main():
    audit_logger.log_data_access(
        user=st.session_state.get("username", "unknown"),
        resource="ficha_provincial",
        action="view"
    )

    # Cargar datos de provincias
    try:
        provinciasDF = get_provincias()
        # Eliminar entrada where 'provincia' is 'C.A.B.A.' or 'Tierra del Fuego, Antártida e Islas del Atlántico Sur'
        provinciasDF = provinciasDF[provinciasDF['provincia'] != 'C.A.B.A.']
        provinciasDF = provinciasDF[provinciasDF['provincia'] != 'Tierra del Fuego, Antártida e Islas del Atlántico Sur']

        logger.info(f"Loaded {len(provinciasDF)} provinces")
    except Exception as e:
        logger.error(f"Failed to load provinces: {str(e)}")
        st.error("Error al cargar la lista de provincias. Por favor, contacte al administrador.", icon=":material/close:")
        st.stop()
    # Header con ícono
    col1, col2 = st.columns([1, 9], vertical_alignment='center')
    with col1:
        st.markdown("""
            <div class="icon-container">
                <i class="icono-arg-ciencia-publicacion" style="font-size: 76px; color: #FFFFFF;"></i>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        st.header("Ficha Provincial")
        st.markdown("")
        st.write("Secretaría de Innovación, Ciencia y Tecnología")

    st.markdown("""---""")

    # Selector de provincia con placeholder mejorado
    provincia = st.selectbox(
        "Seleccione una provincia:",
        options=provinciasDF['nombre_iso'].sort_values(),
        label_visibility="collapsed",
        index=None,
        placeholder="Seleccione una provincia para visualizar los datos",
        help="Seleccione una provincia para ver sus indicadores de ciencia y tecnología"
    )

    if provincia:
        # Guardar selección en session state
        st.session_state.provincia = provincia
        st.session_state.provincia_id = provinciasDF[provinciasDF['nombre_iso'] == provincia]['id'].values[0]
        st.session_state.region = provinciasDF[provinciasDF['nombre_iso'] == provincia]['region'].values[0]
        st.session_state.pais = 'Argentina'
        st.session_state.anio = '2023'
        
        logger.info(f"Province selected: {st.session_state.provincia} (ID: {st.session_state.provincia_id})")

        # Cargar datos de la provincia
        DFs = load_provincial_data(
            provincia_id=st.session_state.provincia_id,
            provincia=st.session_state.provincia,
            anio=st.session_state.anio
        )

        if DFs is None:
            st.stop()

        # Título de la provincia con información adicional
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"## {provincia}")
        with col2:
            st.info(f"Región: {st.session_state.region}", icon=":material/location_on:")
        with col3:
            st.info(f"Año: {st.session_state.anio}", icon=":material/calendar_today:")

        # Tabs para las diferentes secciones
        tabs = st.tabs([
            "Indicadores de contexto",
            "Inversión en I+D",
            "Proyectos",
            "Infraestructura",
            "Capital Humano",
            "Resultados",
            "Ciencia y Sociedad"
        ],
            width='stretch'
        )

        # Tab 1: Indicadores de contexto
        with tabs[0]:
            st.markdown("")
            
            # Métricas principales
            col1, col2, col3, col4, col5 = st.columns([1, 3.75, .5, 3.75, 1])
            with col2:
                st.subheader("Provincial :material/location_on:")
                for key in ['kpi_poblacion_prov', 'kpi_tasa_actividad_prov', 'kpi_tasa_desempleo_prov']:
                    comp = DFs['componentes'][key]
                    st.metric(
                        label=f":primary[{comp['titulo']}]",
                        value=comp['valor'],
                        delta=None,
                    )
            with col4:
                st.subheader("Nacional :material/flag:")
                for key in ['kpi_densidad_prov', 'kpi_tasa_actividad_nac', 'kpi_tasa_desempleo_nac']:
                    comp = DFs['componentes'][key]
                    st.metric(
                        label=f":primary[{comp['titulo']}]",
                        value=comp['valor'],
                        delta=None,
                    )
            
            st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_actividad_nac']['fuente']}")
            st.markdown("")
            
            # Gráfico de exportaciones
            render_chart_with_source(DFs['componentes']['grafico_expo_top5'])

        # Tab 2: Inversión en I+D
        with tabs[1]:
            render_chart_with_source(DFs['componentes']['grafico_evolucion_presupuesto_apn'])
            st.markdown("---")
            st.markdown("##### Ejecución del gasto en I+D del Presupuesto de la Administración Pública Nacional (APN)")
            st.text(" crédito devengado en millones de pesos a valores corrientes")
            col1, col2, col3 = st.columns(3)
            with col1:
                comp = DFs['componentes']['kpi_apn_devengado_prov']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            with col2:
                comp = DFs['componentes']['kpi_apn_devengado_region']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            with col3:
                comp = DFs['componentes']['kpi_apn_devengado_nac']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            st.caption(f"Fuente: {DFs['componentes']['kpi_apn_devengado_nac']['fuente']} - Actualizado al 21/05/2025")
            st.markdown("---")
            render_table_with_source(DFs['componentes']['tabla_apn_jurisdiccion_entidad_programa_prov'])
            st.markdown("---")
            render_chart_with_source(DFs['componentes']['grafico_evolucion_regional'])
            st.markdown("---")
            render_chart_with_source(DFs['componentes']['grafico_inv_por_investigador'])
            st.markdown("---    ")
            render_chart_with_source(DFs['componentes']['grafico_inv_empresaria_sector'])

        # Tab 3: Proyectos
        with tabs[2]:
            st.markdown("")
            
            # KPIs de proyectos
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Provincial :material/location_on:")
                for key in ['kpi_pfi_provincial', 'kpi_porc_privada_provincial']:
                    comp = DFs['componentes'][key]
                    st.metric(
                        label=f":primary[{comp['titulo']}]",
                        value=comp['valor'],
                        delta=None,
                    )
            with col2:
                st.subheader("Regional :material/explore_nearby:")
                for key in ['kpi_pfi_regional', 'kpi_porc_privada_regional']:
                    comp = DFs['componentes'][key]
                    st.metric(
                        label=f":primary[{comp['titulo']}]",
                        value=comp['valor'],
                        delta=None,
                    )
            with col3:
                st.subheader("Nacional :material/flag:")
                for key in ['kpi_pfi_nacional', 'kpi_porc_privada_nacional']:
                    comp = DFs['componentes'][key]
                    st.metric(
                        label=f":primary[{comp['titulo']}]",
                        value=comp['valor'],
                        delta=None,
                    )
            
            st.caption("*PFI: Proyectos Federales de Innovación")
            st.caption(f"Fuente: {DFs['componentes']['kpi_pfi_provincial']['fuente']}")
            st.markdown("")
            
            # Tabla de proyectos
            if DFs['componentes']['tabla_pfi_cruce']['figura'] is not None:
                render_table_with_source(DFs['componentes']['tabla_pfi_cruce'])

        # Tab 4: Infraestructura
        with tabs[3]:
            st.markdown("")
            
            # KPI central
            colA, colB, colC = st.columns(3)
            with colB:
                comp = DFs['componentes']['kpi_unidades_id_prov']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            
            render_chart_with_source(DFs['componentes']['grafico_unidades_por_inst'])
            st.markdown("---")
            
            # KPIs de equipos
            col1, col2, col3 = st.columns(3)
            with col1:
                comp = DFs['componentes']['kpi_equipos_provincial']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            with col2:
                comp = DFs['componentes']['kpi_equipos_regional']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            with col3:
                comp = DFs['componentes']['kpi_equipos_nacional']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            
            st.caption(f"Fuente: {DFs['componentes']['kpi_equipos_nacional']['fuente']}")
            st.markdown("")
            
            render_chart_with_source(DFs['componentes']['grafico_equipos_por_tipo'])

        # Tab 5: Capital Humano
        with tabs[4]:
            st.markdown("")
            
            render_chart_with_source(DFs['componentes']['grafico_distribucion_investigadores'])
            st.markdown("")
            
            # KPIs comparativos
            col1, col2, col3 = st.columns(3, border=True)
            with col1:
                st.markdown(f"#### {st.session_state.provincia}")
                comp = DFs['componentes']['kpi_tasa_pea_provincial']
                st.metric(
                    label=":primary[Investigadores cada 1000 habs.]",
                    value=comp['valor'],
                    delta=None,
                )
            with col2:
                st.markdown(f"#### {st.session_state.region}")
                comp = DFs['componentes']['kpi_tasa_pea_regional']
                st.metric(
                    label=":primary[Investigadores cada 1000 habs.]",
                    value=comp['valor'],
                    delta=None,
                )
            with col3:
                st.markdown(f"#### {st.session_state.pais}")
                comp = DFs['componentes']['kpi_tasa_pea_nacional']
                st.metric(
                    label=":primary[Investigadores cada 1000 habs.]",
                    value=comp['valor'],
                    delta=None
                )
            
            st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_pea_nacional']['fuente']}")
            st.markdown("")
            
            if DFs['componentes']['tabla_personas_por_funcion']['figura'] is not None:
                render_table_with_source(DFs['componentes']['tabla_personas_por_funcion'])
                st.markdown("---")
            
            render_chart_with_source(DFs['componentes']['grafico_evolucion_investigadores'])

        # Tab 6: Resultados
        with tabs[5]:
            st.markdown("")
            
            render_chart_with_source(DFs['componentes']['grafico_expo_intensidad'])
            st.markdown("")
            render_chart_with_source(DFs['componentes']['grafico_expo_evolucion'])
            st.markdown("")
            render_chart_with_source(DFs['componentes']['grafico_expo_destino'])
            st.markdown("---")
            
            # KPIs de patentes
            col1, col2, col3 = st.columns([6, 1, 3], vertical_alignment="center")
            with col1:
                comp = DFs['componentes']['kpi_patentes_cyt_prov']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None,
                )
            
            col1b, col2b, col3b = st.columns([2, 6, 2])
            with col2b:
                comp = DFs['componentes']['kpi_patentes_cyt_arg']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None
                )
            
            col1c, col2c, col3c = st.columns([2, 2, 6])
            with col3c:
                comp = DFs['componentes']['kpi_patentes_arg']
                st.metric(
                    label=f":primary[{comp['titulo']}]",
                    value=comp['valor'],
                    delta=None
                )
            
            st.caption(f"Fuente: {DFs['componentes']['kpi_patentes_arg']['fuente']}")
            st.markdown("---")
            
            # Gráficos y tablas de resultados
            if DFs['componentes']['grafico_patentes_evolucion']['figura'] is not None:
                render_chart_with_source(DFs['componentes']['grafico_patentes_evolucion'])
                st.markdown("---")
            
            if DFs['componentes']['tabla_patentes_sector']['figura'] is not None:
                render_table_with_source(DFs['componentes']['tabla_patentes_sector'])
                st.markdown("---")
            
            render_chart_with_source(DFs['componentes']['grafico_produccion_evolucion'])
            st.markdown("---")
            render_chart_with_source(DFs['componentes']['grafico_produccion_tipo'])
            st.markdown("---")
            render_chart_with_source(DFs['componentes']['grafico_publicaciones_area'])
            st.markdown("---")
            
            if DFs['componentes']['tabla_articulos_q1_q2']['figura'] is not None:
                render_table_with_source(DFs['componentes']['tabla_articulos_q1_q2'])

        # Tab 7: Ciencia y Sociedad
        with tabs[6]:
            st.markdown("")
            render_chart_with_source(DFs['componentes']['grafico_percepcion_temas_prioritarios'])
            st.markdown("---")
            render_chart_with_source(DFs['componentes']['grafico_percepcion_calidad_vida'])
            st.markdown("")

        # Aplicar estilos a las metric cards
        style_metric_cards()
        st.markdown("---")

        # --- SECCIÓN DE EXPORTACIÓN PDF ---
        # st.markdown("### 📄 Exportar Reporte")
        
        # col1, col2, col3 = st.columns([1, 2, 1])
        # with col2:
        #     if st.button(
        #         "🎯 Generar Reporte PDF",
        #         use_container_width=True,
        #         help="Generar un reporte PDF completo con todos los datos de la provincia",
        #         type="primary"
        #     ):
        #         generate_pdf_report(st.session_state.provincia, DFs)

    else:
        # Mensaje cuando no hay provincia seleccionada
        st.info("Por favor, seleccione una provincia del menú desplegable para visualizar sus datos.", icon=":material/info:")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error crítico en Fichas Provinciales: {e}", exc_info=True)
        st.error("Error crítico. Por favor contacte al administrador.", icon=":material/close:")
        
        if st.session_state.get('roles') and 'admin' in st.session_state.get('roles'):
            with st.expander("Detalles del Error"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())
