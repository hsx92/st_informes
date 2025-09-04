"""Streamlit page for displaying provincial dashboards with enhanced logging.

This module defines the :func:`panomProvincial` function, which renders
key metrics, tables, and charts for a selected province and allows
exporting the report to PDF.
"""

import streamlit as st
import time
from streamlit_extras.great_tables import great_tables
from streamlit_extras.metric_cards import style_metric_cards
from sources import get_provincias
from pdf_builder import ficha_provincial_pdf
from ficha_builder import ficha_provincial_figs, preparar_data_pdf
from css_utils import load_css
from logging_config import get_logger, setup_logging, log_execution_time

# Inicializar logging para este módulo
logger = get_logger(__name__)
_, audit_logger = setup_logging("SICyT_Portal")

st.set_page_config(page_title="Portal - SICyT", page_icon=st.secrets["LOGO_CORTO"], layout="wide")
st.logo(image=st.secrets["LOGO_LARGO"], size="large")

# ---- CSS ----
try:
    custom_streamlit_css = """
        div[data-testid="stMetricValue"] > div {
            color: #354B6E;
        }
        div[data-testid="stMetricDelta"] > div {
            color: #FFFFFF;
        }
        """
    icon_css = load_css("static/iconos/dist/css/icono-arg.css")
    combined_css = f"""
    <style>
    {icon_css}
    {custom_streamlit_css}
    </style>
    """
    
    # Inyectar el CSS en la aplicación
    st.markdown(combined_css, unsafe_allow_html=True)
    logger.debug("CSS cargado correctamente para Fichas Provinciales")
    
except Exception as e:
    logger.error(f"Error al cargar CSS: {e}")
    st.warning("Algunos estilos podrían no cargarse correctamente")


# ---- MAINPAGE ----
@log_execution_time
def panomProvincial():
    """Render the provincial dashboard page with full logging support.

    Loads provincial data, displays metrics and tables, and provides the
    option to export the report as a PDF.

    Returns:
        None: This function renders the page but does not return a value.
    """
    logger.info("Iniciando renderizado de Fichas Provinciales")
    
    try:
        # Cargar datos de provincias
        provinciasDF = get_provincias()
        logger.debug(f"Cargadas {len(provinciasDF)} provincias")

        col1, col2 = st.columns([1, 9], vertical_alignment='center')

        with col1:
            st.markdown("""
                <div class="icon-container">
                    <i class="icono-arg-ciencia-publicacion" style="font-size: 60px;"></i>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.header("Ficha provincial")
            st.write("Secretaría de Innovación, Ciencia y Tecnología")

        st.markdown("""---""")

        provincia = st.selectbox(
            "Seleccione una provincia:",
            options=provinciasDF['nombre_iso'].sort_values(),
            label_visibility="collapsed",
            index=None,
            placeholder="Seleccione una provincia para visualizar los datos"
        )

        if provincia:
            # Log de acceso a datos provinciales
            logger.info(f"Usuario seleccionó provincia: {provincia}")
            
            # Configurar variables de sesión
            st.session_state.provincia = provinciasDF[provinciasDF['nombre_iso'] == provincia]['provincia'].values[0]
            st.session_state.provincia_id = provinciasDF[provinciasDF['nombre_iso'] == provincia]['id'].values[0]
            st.session_state.region = provinciasDF[provinciasDF['nombre_iso'] == provincia]['region'].values[0]
            st.session_state.pais = 'Argentina'
            st.session_state.anio = '2023'
            
            # Auditar acceso a datos
            audit_logger.log_data_access(
                provincia_id=st.session_state.provincia_id,
                data_type="ficha_provincial"
            )
            
            # Indicadores de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Cargando datos de la provincia...")
                progress_bar.progress(10)
                logger.debug(f"Iniciando carga de datos para {provincia}")
                
                # Medir tiempo de carga
                start_time = time.time()
                
                # Cache de datos con logging
                @st.cache_data(ttl=3600, show_spinner=False)
                def load_provincial_data(provincia_id, provincia, anio):
                    logger.debug(f"Cargando datos desde caché o BD para provincia_id={provincia_id}")
                    return ficha_provincial_figs(
                        provincia_id=provincia_id,
                        provincia=provincia,
                        anio=anio
                    )
                
                progress_bar.progress(30)
                status_text.text("📊 Generando visualizaciones...")
                
                DFs = load_provincial_data(
                    st.session_state.provincia_id,
                    st.session_state.provincia,
                    st.session_state.anio
                )
                
                load_time = time.time() - start_time
                logger.info(f"Datos cargados para {provincia} en {load_time:.2f} segundos")
                
                progress_bar.progress(90)
                status_text.text("✅ Datos cargados exitosamente")
                time.sleep(0.5)
                
                # Limpiar indicadores
                progress_bar.empty()
                status_text.empty()
                
                # Log de componentes cargados
                componentes_con_datos = sum(
                    1 for c in DFs['componentes'].values()
                    if c.get('figura') is not None or c.get('valor') is not None
                )
                logger.info(f"Componentes con datos: {componentes_con_datos}/{len(DFs['componentes'])}")

                st.markdown(f"## {provincia}")

                # Crear tabs con manejo de errores
                try:
                    indicadoresTab, inversionTab, proyectosTab, infraestructuraTab, capitalHumanoTab, resultadosTab, ciencia_sociedadTab = st.tabs(
                        ["Indicadores de contexto", "Inversión en I+D", "Proyectos", "Infraestructura", "Capital Humano", "Resultados", "Ciencia y Sociedad"]
                    )
                    
                    # TAB: Indicadores de Contexto
                    with indicadoresTab:
                        render_indicadores_tab(DFs)
                    
                    # TAB: Inversión en I+D
                    with inversionTab:
                        render_inversion_tab(DFs)
                    
                    # TAB: Proyectos
                    with proyectosTab:
                        render_proyectos_tab(DFs)
                    
                    # TAB: Infraestructura
                    with infraestructuraTab:
                        render_infraestructura_tab(DFs)
                    
                    # TAB: Capital Humano
                    with capitalHumanoTab:
                        render_capital_humano_tab(DFs)
                    
                    # TAB: Resultados
                    with resultadosTab:
                        render_resultados_tab(DFs)
                    
                    # TAB: Ciencia y Sociedad
                    with ciencia_sociedadTab:
                        render_ciencia_sociedad_tab(DFs)
                    
                    style_metric_cards()
                    
                except Exception as e:
                    logger.error(f"Error renderizando tabs: {e}", exc_info=True)
                    st.error("Error al mostrar algunos componentes. Por favor recargue la página.")

                st.markdown("---")

                # --- EXPORTAR PDF con logging ---
                col1, col2, col3 = st.columns(3)
                with col2:
                    exportar = st.button("Exportar a PDF", use_container_width=True)
                    if exportar:
                        try:
                            logger.info(f"Iniciando exportación PDF para {st.session_state.provincia}")
                            
                            with st.spinner("Generando PDF..."):
                                start_pdf = time.time()
                                
                                data = preparar_data_pdf(DFs)
                                filename = f"output/Ficha Provincial - {st.session_state.provincia}.pdf"
                                ficha_provincial_pdf(st.session_state.provincia, data, filename)
                                
                                pdf_time = time.time() - start_pdf
                                
                                # Auditar exportación
                                audit_logger.log_export(
                                    provincia=st.session_state.provincia,
                                    format="PDF"
                                )
                                
                                logger.info(f"PDF generado exitosamente en {pdf_time:.2f} segundos: {filename}")
                                st.success("✅ PDF exportado exitosamente")
                                
                                # Ofrecer descarga
                                with open(filename, "rb") as pdf_file:
                                    st.download_button(
                                        label="📥 Descargar PDF",
                                        data=pdf_file.read(),
                                        file_name=filename.split('/')[-1],
                                        mime="application/pdf"
                                    )
                                    
                        except Exception as e:
                            logger.error(f"Error al generar PDF: {e}", exc_info=True)
                            st.error("⚠️ Error al generar el PDF. Por favor intente nuevamente.")
                            
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                logger.error(f"Error cargando datos para {provincia}: {e}", exc_info=True)
                st.error("⚠️ Error al cargar los datos de la provincia.")
                st.info("Por favor, intente con otra provincia o contacte al administrador.")
                
    except Exception as e:
        logger.critical(f"Error crítico en panomProvincial: {e}", exc_info=True)
        st.error("Error crítico en la aplicación. Por favor contacte al administrador.")


# Funciones auxiliares para renderizar cada tab con manejo de errores
def render_indicadores_tab(DFs):
    """Renderiza el tab de indicadores con logging de errores"""
    try:
        st.markdown("")
        col1, col2, col3, col4, col5 = st.columns([1, 3.75, .5, 3.75, 1])
        
        # Renderizar métricas con validación
        with col2:
            for kpi_name in ['kpi_poblacion_prov', 'kpi_tasa_actividad_prov', 'kpi_tasa_desempleo_prov']:
                try:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi:
                        st.metric(
                            label=f":primary[{kpi.get('titulo', 'N/A')}]",
                            value=kpi.get('valor', 'N/A'),
                            delta=None,
                        )
                except Exception as e:
                    logger.warning(f"Error mostrando KPI {kpi_name}: {e}")
                    st.metric(label=":primary[Error]", value="N/A")
        
        with col4:
            for kpi_name in ['kpi_densidad_prov', 'kpi_tasa_actividad_nac', 'kpi_tasa_desempleo_nac']:
                try:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi:
                        st.metric(
                            label=f":primary[{kpi.get('titulo', 'N/A')}]",
                            value=kpi.get('valor', 'N/A'),
                            delta=None,
                        )
                except Exception as e:
                    logger.warning(f"Error mostrando KPI {kpi_name}: {e}")
                    st.metric(label=":primary[Error]", value="N/A")

        # Mostrar fuente
        if DFs['componentes'].get('kpi_tasa_actividad_nac'):
            st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_actividad_nac'].get('fuente', 'N/A')}")
        st.markdown("")
        
        # Gráfico con validación
        try:
            if DFs['componentes'].get('grafico_expo_top5', {}).get('figura'):
                st.plotly_chart(DFs['componentes']['grafico_expo_top5']['figura'], use_container_width=True)
                st.caption(f"Fuente: {DFs['componentes']['grafico_expo_top5'].get('fuente', 'N/A')}")
            else:
                st.info("Gráfico de exportaciones no disponible")
        except Exception as e:
            logger.error(f"Error mostrando gráfico expo_top5: {e}")
            st.warning("No se pudo cargar el gráfico de exportaciones")
            
    except Exception as e:
        logger.error(f"Error en tab de indicadores: {e}", exc_info=True)
        st.error("Error al cargar indicadores de contexto")


def render_inversion_tab(DFs):
    """Renderiza el tab de inversión con manejo de errores"""
    try:
        graficos = [
            'grafico_evolucion_regional',
            'grafico_inv_por_investigador',
            'grafico_inv_empresaria_sector'
        ]
        
        for grafico_name in graficos:
            try:
                grafico = DFs['componentes'].get(grafico_name, {})
                if grafico.get('figura'):
                    st.plotly_chart(grafico['figura'], use_container_width=True)
                    st.caption(f"Fuente: {grafico.get('fuente', 'N/A')}")
                    st.markdown("")
                else:
                    logger.warning(f"Gráfico {grafico_name} no tiene figura")
                    
            except Exception as e:
                logger.error(f"Error mostrando gráfico {grafico_name}: {e}")
                st.warning("No se pudo cargar el gráfico")
                
    except Exception as e:
        logger.error(f"Error en tab de inversión: {e}", exc_info=True)
        st.error("Error al cargar datos de inversión")


# Optimizar funciones para los demás tabs...
def render_proyectos_tab(DFs):
    """Renderiza el tab de proyectos"""
    logger.debug("Renderizando tab de proyectos")
    try:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_pfi_provincial']['titulo']}]",
                value=DFs['componentes']['kpi_pfi_provincial']['valor'],
                delta=None,
            )
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_porc_privada_provincial']['titulo']}]",
                value=DFs['componentes']['kpi_porc_privada_provincial']['valor'],
                delta=None,
            )
        with col2:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_pfi_regional']['titulo']}]",
                value=DFs['componentes']['kpi_pfi_regional']['valor'],
                delta=None,
            )
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_porc_privada_regional']['titulo']}]",
                value=DFs['componentes']['kpi_porc_privada_regional']['valor'],
                delta=None,
            )
        with col3:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_pfi_nacional']['titulo']}]",
                value=DFs['componentes']['kpi_pfi_nacional']['valor'],
                delta=None,
            )
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_porc_privada_nacional']['titulo']}]",
                value=DFs['componentes']['kpi_porc_privada_nacional']['valor'],
                delta=None,
            )
        st.caption("*PFI: Proyectos Federales de Innovación")
        st.caption(f"Fuente: {DFs['componentes']['kpi_pfi_provincial']['fuente']}")
        st.markdown("")

        if DFs['componentes']['tabla_pfi_cruce']['figura'] is not None:
            great_tables(DFs['componentes']['tabla_pfi_cruce']['figura'])
            st.caption(f"Fuente: {DFs['componentes']['tabla_pfi_cruce']['fuente']}")
            st.markdown("")
    except Exception as e:
        logger.error(f"Error en tab de proyectos: {e}", exc_info=True)
        st.error("Error al cargar datos de proyectos")


def render_infraestructura_tab(DFs):
    """Renderiza el tab de infraestructura"""
    logger.debug("Renderizando tab de infraestructura")
    try:
        colA, colB, colC = st.columns(3)
        with colB:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_unidades_id_prov']['titulo']}]",
                value=DFs['componentes']['kpi_unidades_id_prov']['valor'],
                delta=None,
            )

        st.plotly_chart(DFs['componentes']['grafico_unidades_por_inst']['figura'], use_container_width=True)
        st.caption(f"Fuente: {DFs['componentes']['grafico_unidades_por_inst']['fuente']}")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_equipos_provincial']['titulo']}]",
                value=DFs['componentes']['kpi_equipos_provincial']['valor'],
                delta=None,
            )
        with col2:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_equipos_regional']['titulo']}]",
                value=DFs['componentes']['kpi_equipos_regional']['valor'],
                delta=None,
            )
        with col3:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_equipos_nacional']['titulo']}]",
                value=DFs['componentes']['kpi_equipos_nacional']['valor'],
                delta=None,
            )
        st.caption(f"Fuente: {DFs['componentes']['kpi_equipos_nacional']['fuente']}")
        st.markdown("")

        st.plotly_chart(DFs['componentes']['grafico_equipos_por_tipo']['figura'], use_container_width=True)
        st.caption(f"Fuente: {DFs['componentes']['grafico_equipos_por_tipo']['fuente']}")
    except Exception as e:
        logger.error(f"Error en tab de infraestructura: {e}", exc_info=True)
        st.error("Error al cargar datos de infraestructura")


def render_capital_humano_tab(DFs):
    """Renderiza el tab de capital humano"""
    logger.debug("Renderizando tab de capital humano")
    try:
        st.plotly_chart(DFs['componentes']['grafico_distribucion_investigadores']['figura'], use_container_width=True)
        st.caption(f"Fuente: {DFs['componentes']['grafico_distribucion_investigadores']['fuente']}")
        st.markdown("")

        col1, col2, col3 = st.columns(3, border=True)
        with col1:
            st.markdown(f"#### {st.session_state.provincia}")
            st.metric(
                label=":primary[Investigadores cada 1000 habs.]",
                value=DFs['componentes']['kpi_tasa_pea_provincial']['valor'],
                delta=None,
            )
        with col2:
            st.markdown(f"#### {st.session_state.region}")
            st.metric(
                label=":primary[Investigadores cada 1000 habs.]",
                value=DFs['componentes']['kpi_tasa_pea_regional']['valor'],
                delta=None,
            )
        with col3:
            st.markdown(f"#### {st.session_state.pais}")
            st.metric(label=":primary[Investigadores cada 1000 habs.]", value=DFs['componentes']['kpi_tasa_pea_nacional']['valor'], delta=None)
        st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_pea_nacional']['fuente']}")
        st.markdown("")

        if DFs['componentes']['tabla_personas_por_funcion']['figura'] is not None:
            great_tables(DFs['componentes']['tabla_personas_por_funcion']['figura'])
            st.caption(f"Fuente: {DFs['componentes']['tabla_personas_por_funcion']['fuente']}")
            st.markdown("---")

        st.plotly_chart(DFs['componentes']['grafico_evolucion_investigadores']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_evolucion_investigadores']['fuente']}")
    except Exception as e:
        logger.error(f"Error en tab de capital humano: {e}", exc_info=True)
        st.error("Error al cargar datos de capital humano")


def render_resultados_tab(DFs):
    """Renderiza el tab de resultados"""
    logger.debug("Renderizando tab de resultados")
    try:
        st.plotly_chart(DFs['componentes']['grafico_expo_intensidad']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_expo_intensidad']['fuente']}")
        st.markdown("")

        st.plotly_chart(DFs['componentes']['grafico_expo_evolucion']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_expo_evolucion']['fuente']}")
        st.markdown("")

        st.plotly_chart(DFs['componentes']['grafico_expo_destino']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_expo_destino']['fuente']}")
        st.markdown("---")

        col1, col2, col3 = st.columns([6, 1, 3], vertical_alignment="center")
        with col1:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_patentes_cyt_prov']['titulo']}]",
                value=DFs['componentes']['kpi_patentes_cyt_prov']['valor'],
                delta=None,
            )
        col1b, col2b, col3b = st.columns([2, 6, 2])
        with col2b:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_patentes_cyt_arg']['titulo']}]",
                value=DFs['componentes']['kpi_patentes_cyt_arg']['valor'],
                delta=None
            )
        col1c, col2c, col3c = st.columns([2, 2, 6])
        with col3c:
            st.metric(
                label=f":primary[{DFs['componentes']['kpi_patentes_arg']['titulo']}]",
                value=DFs['componentes']['kpi_patentes_arg']['valor'],
                delta=None
            )
        st.caption(f"Fuente: {DFs['componentes']['kpi_patentes_arg']['fuente']}")
        st.markdown("---")

        if DFs['componentes']['grafico_patentes_evolucion']['figura'] is not None:
            st.plotly_chart(DFs['componentes']['grafico_patentes_evolucion']['figura'])
            st.caption(f"Fuente: {DFs['componentes']['grafico_patentes_evolucion']['fuente']}")
            st.markdown("---")

        if DFs['componentes']['tabla_patentes_sector']['figura'] is not None:
            great_tables(DFs['componentes']['tabla_patentes_sector']['figura'])
            st.caption(f"Fuente: {DFs['componentes']['tabla_patentes_sector']['fuente']}")

            st.markdown("---")

        st.plotly_chart(DFs['componentes']['grafico_produccion_evolucion']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_produccion_evolucion']['fuente']}")
        st.markdown("---")

        st.plotly_chart(DFs['componentes']['grafico_produccion_tipo']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_produccion_tipo']['fuente']}")
        st.markdown("---")

        st.plotly_chart(DFs['componentes']['grafico_publicaciones_area']['figura'])
        st.caption(f"Fuente: {DFs['componentes']['grafico_publicaciones_area']['fuente']}")
        st.markdown("---")

        if DFs['componentes']['tabla_articulos_q1_q2']['figura'] is not None:
            great_tables(DFs['componentes']['tabla_articulos_q1_q2']['figura'])
            st.caption(f"Fuente: {DFs['componentes']['tabla_articulos_q1_q2']['fuente']}")
    except Exception as e:
        logger.error(f"Error en tab de resultados: {e}", exc_info=True)
        st.error("Error al cargar datos de resultados")


def render_ciencia_sociedad_tab(DFs):
    """Renderiza el tab de ciencia y sociedad"""
    logger.debug("Renderizando tab de ciencia y sociedad")
    try:
        st.plotly_chart(DFs['componentes']['grafico_percepcion_temas_prioritarios']['figura'], use_container_width=True)
        st.caption(f"Fuente: {DFs['componentes']['grafico_percepcion_temas_prioritarios']['fuente']}")
        st.markdown("---")

        st.plotly_chart(DFs['componentes']['grafico_percepcion_calidad_vida']['figura'], use_container_width=True)
        st.caption(f"Fuente: {DFs['componentes']['grafico_percepcion_calidad_vida']['fuente']}")
    except Exception as e:
        logger.error(f"Error en tab de ciencia y sociedad: {e}", exc_info=True)
        st.error("Error al cargar datos de ciencia y sociedad")


# ---- AUTENTICACIÓN Y AUTORIZACIÓN ----
try:
    st.session_state.authenticator.login(location='unrendered')
    
    if 'authentication_status' in st.session_state:
        if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
            logger.warning("Intento de acceso no autenticado a Fichas Provinciales")
            st.warning("Debe estar logueado para acceder a esta información.")
            st.stop()
            
        elif 'admin' not in st.session_state["roles"] and 'director' not in st.session_state["roles"]:
            username = st.session_state.get('username', 'unknown')
            logger.warning(f"Acceso no autorizado de usuario {username} a Fichas Provinciales")
            st.error('Acceso no autorizado.')
            st.stop()
            
        else:
            username = st.session_state.get('username', 'unknown')
            logger.info(f"Usuario {username} accedió a Fichas Provinciales")
            panomProvincial()
            
except AttributeError as e:
    logger.error(f"Error de autenticación: {e}")
    st.warning("Debe estar logueado para acceder a esta información.")
    st.stop()
    
except Exception as e:
    logger.critical(f"Error crítico en página Fichas Provinciales: {e}", exc_info=True)
    st.error("Error crítico. Por favor contacte al administrador.")
    st.stop()
