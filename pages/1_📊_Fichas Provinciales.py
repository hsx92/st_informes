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


# Funciones auxiliares para renderizar cada tab
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


def render_proyectos_tab(DFs):
    """Renderiza el tab de proyectos con manejo robusto de errores"""
    try:
        logger.debug("Renderizando tab de proyectos")
        st.markdown("")
        
        # KPIs en 3 columnas
        col1, col2, col3 = st.columns(3)
        
        # KPIs Provinciales
        with col1:
            try:
                for kpi_name in ['kpi_pfi_provincial', 'kpi_porc_privada_provincial']:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi and kpi.get('titulo') and kpi.get('valor'):
                        st.metric(
                            label=f":primary[{kpi['titulo']}]",
                            value=kpi['valor'],
                            delta=None,
                        )
                        logger.debug(f"KPI {kpi_name} renderizado: {kpi['valor']}")
                    else:
                        logger.warning(f"KPI {kpi_name} sin datos completos")
                        st.metric(label=":primary[Sin datos]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPIs provinciales: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # KPIs Regionales
        with col2:
            try:
                for kpi_name in ['kpi_pfi_regional', 'kpi_porc_privada_regional']:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi and kpi.get('titulo') and kpi.get('valor'):
                        st.metric(
                            label=f":primary[{kpi['titulo']}]",
                            value=kpi['valor'],
                            delta=None,
                        )
                        logger.debug(f"KPI {kpi_name} renderizado: {kpi['valor']}")
                    else:
                        logger.warning(f"KPI {kpi_name} sin datos completos")
                        st.metric(label=":primary[Sin datos]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPIs regionales: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # KPIs Nacionales
        with col3:
            try:
                for kpi_name in ['kpi_pfi_nacional', 'kpi_porc_privada_nacional']:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi and kpi.get('titulo') and kpi.get('valor'):
                        st.metric(
                            label=f":primary[{kpi['titulo']}]",
                            value=kpi['valor'],
                            delta=None,
                        )
                        logger.debug(f"KPI {kpi_name} renderizado: {kpi['valor']}")
                    else:
                        logger.warning(f"KPI {kpi_name} sin datos completos")
                        st.metric(label=":primary[Sin datos]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPIs nacionales: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # Caption y nota
        st.caption("*PFI: Proyectos Federales de Innovación")
        if DFs['componentes'].get('kpi_pfi_provincial', {}).get('fuente'):
            st.caption(f"Fuente: {DFs['componentes']['kpi_pfi_provincial']['fuente']}")
        st.markdown("")
        
        # Tabla de proyectos PFI
        try:
            tabla_pfi = DFs['componentes'].get('tabla_pfi_cruce', {})
            if tabla_pfi.get('figura') is not None:
                logger.debug("Mostrando tabla PFI cruce")
                great_tables(tabla_pfi['figura'])
                if tabla_pfi.get('fuente'):
                    st.caption(f"Fuente: {tabla_pfi['fuente']}")
                st.markdown("")
            else:
                logger.info("No hay datos disponibles para tabla PFI")
                st.info("📊 No hay datos de proyectos PFI disponibles para esta provincia")
        except Exception as e:
            logger.error(f"Error mostrando tabla PFI: {e}")
            st.warning("No se pudo cargar la tabla de proyectos")
            
    except Exception as e:
        logger.error(f"Error crítico en tab de proyectos: {e}", exc_info=True)
        st.error("Error al cargar datos de proyectos. Por favor, intente recargar la página.")


def render_infraestructura_tab(DFs):
    """Renderiza el tab de infraestructura con validación completa"""
    try:
        logger.debug("Renderizando tab de infraestructura")
        st.markdown("")
        
        # KPI principal centrado
        colA, colB, colC = st.columns(3)
        with colB:
            try:
                kpi_unidades = DFs['componentes'].get('kpi_unidades_id_prov', {})
                if kpi_unidades and kpi_unidades.get('titulo') and kpi_unidades.get('valor'):
                    st.metric(
                        label=f":primary[{kpi_unidades['titulo']}]",
                        value=kpi_unidades['valor'],
                        delta=None,
                    )
                    logger.debug(f"KPI unidades I+D: {kpi_unidades['valor']}")
                else:
                    logger.warning("KPI unidades I+D sin datos")
                    st.metric(label=":primary[Unidades I+D]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPI unidades: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # Gráfico de unidades por institución
        try:
            grafico_unidades = DFs['componentes'].get('grafico_unidades_por_inst', {})
            if grafico_unidades.get('figura'):
                logger.debug("Mostrando gráfico de unidades por institución")
                st.plotly_chart(grafico_unidades['figura'], use_container_width=True)
                if grafico_unidades.get('fuente'):
                    st.caption(f"Fuente: {grafico_unidades['fuente']}")
            else:
                logger.info("Gráfico de unidades no disponible")
                st.info("📊 Gráfico de unidades por institución no disponible")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de unidades: {e}")
            st.warning("No se pudo cargar el gráfico de unidades")
        
        st.markdown("---")
        
        # KPIs de equipos en 3 columnas
        col1, col2, col3 = st.columns(3)
        
        kpis_equipos = [
            ('kpi_equipos_provincial', col1),
            ('kpi_equipos_regional', col2),
            ('kpi_equipos_nacional', col3)
        ]
        
        for kpi_name, column in kpis_equipos:
            with column:
                try:
                    kpi = DFs['componentes'].get(kpi_name, {})
                    if kpi and kpi.get('titulo') and kpi.get('valor'):
                        st.metric(
                            label=f":primary[{kpi['titulo']}]",
                            value=kpi['valor'],
                            delta=None,
                        )
                        logger.debug(f"KPI {kpi_name}: {kpi['valor']}")
                    else:
                        logger.warning(f"KPI {kpi_name} sin datos")
                        st.metric(label=":primary[Equipos I+D]", value="N/A")
                except Exception as e:
                    logger.error(f"Error mostrando KPI {kpi_name}: {e}")
                    st.metric(label=":primary[Error]", value="N/A")
        
        # Fuente de equipos
        if DFs['componentes'].get('kpi_equipos_nacional', {}).get('fuente'):
            st.caption(f"Fuente: {DFs['componentes']['kpi_equipos_nacional']['fuente']}")
        st.markdown("")
        
        # Gráfico de equipos por tipo
        try:
            grafico_equipos = DFs['componentes'].get('grafico_equipos_por_tipo', {})
            if grafico_equipos.get('figura'):
                logger.debug("Mostrando gráfico de equipos por tipo")
                st.plotly_chart(grafico_equipos['figura'], use_container_width=True)
                if grafico_equipos.get('fuente'):
                    st.caption(f"Fuente: {grafico_equipos['fuente']}")
            else:
                logger.info("Gráfico de equipos no disponible")
                st.info("📊 Gráfico de equipos por tipo no disponible")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de equipos: {e}")
            st.warning("No se pudo cargar el gráfico de equipos")
            
    except Exception as e:
        logger.error(f"Error crítico en tab de infraestructura: {e}", exc_info=True)
        st.error("Error al cargar datos de infraestructura. Por favor, intente recargar la página.")


def render_capital_humano_tab(DFs):
    """Renderiza el tab de capital humano con validación y logging"""
    try:
        logger.debug("Renderizando tab de capital humano")
        st.markdown("")
        
        # Gráfico de distribución de investigadores
        try:
            grafico_dist = DFs['componentes'].get('grafico_distribucion_investigadores', {})
            if grafico_dist.get('figura'):
                logger.debug("Mostrando gráfico de distribución de investigadores")
                st.plotly_chart(grafico_dist['figura'], use_container_width=True)
                if grafico_dist.get('fuente'):
                    st.caption(f"Fuente: {grafico_dist['fuente']}")
            else:
                logger.info("Gráfico de distribución no disponible")
                st.info("📊 Distribución de investigadores no disponible")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de distribución: {e}")
            st.warning("No se pudo cargar el gráfico de distribución")
        
        st.markdown("")
        
        # KPIs de investigadores por PEA
        col1, col2, col3 = st.columns(3, border=True)
        
        # KPI Provincial
        with col1:
            try:
                st.markdown(f"#### {st.session_state.get('provincia', 'Provincia')}")
                kpi = DFs['componentes'].get('kpi_tasa_pea_provincial', {})
                if kpi and kpi.get('valor'):
                    st.metric(
                        label=":primary[Investigadores cada 1000 habs.]",
                        value=kpi['valor'],
                        delta=None,
                    )
                    logger.debug(f"KPI PEA provincial: {kpi['valor']}")
                else:
                    logger.warning("KPI PEA provincial sin datos")
                    st.metric(label=":primary[Investigadores cada 1000 habs.]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPI PEA provincial: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # KPI Regional
        with col2:
            try:
                st.markdown(f"#### {st.session_state.get('region', 'Región')}")
                kpi = DFs['componentes'].get('kpi_tasa_pea_regional', {})
                if kpi and kpi.get('valor'):
                    st.metric(
                        label=":primary[Investigadores cada 1000 habs.]",
                        value=kpi['valor'],
                        delta=None,
                    )
                    logger.debug(f"KPI PEA regional: {kpi['valor']}")
                else:
                    logger.warning("KPI PEA regional sin datos")
                    st.metric(label=":primary[Investigadores cada 1000 habs.]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPI PEA regional: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # KPI Nacional
        with col3:
            try:
                st.markdown(f"#### {st.session_state.get('pais', 'Argentina')}")
                kpi = DFs['componentes'].get('kpi_tasa_pea_nacional', {})
                if kpi and kpi.get('valor'):
                    st.metric(
                        label=":primary[Investigadores cada 1000 habs.]",
                        value=kpi['valor'],
                        delta=None
                    )
                    logger.debug(f"KPI PEA nacional: {kpi['valor']}")
                else:
                    logger.warning("KPI PEA nacional sin datos")
                    st.metric(label=":primary[Investigadores cada 1000 habs.]", value="N/A")
            except Exception as e:
                logger.error(f"Error mostrando KPI PEA nacional: {e}")
                st.metric(label=":primary[Error]", value="N/A")
        
        # Fuente
        if DFs['componentes'].get('kpi_tasa_pea_nacional', {}).get('fuente'):
            st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_pea_nacional']['fuente']}")
        st.markdown("")
        
        # Tabla de personas por función
        try:
            tabla_personas = DFs['componentes'].get('tabla_personas_por_funcion', {})
            if tabla_personas.get('figura') is not None:
                logger.debug("Mostrando tabla de personas por función")
                great_tables(tabla_personas['figura'])
                if tabla_personas.get('fuente'):
                    st.caption(f"Fuente: {tabla_personas['fuente']}")
                st.markdown("---")
            else:
                logger.info("Tabla de personas por función no disponible")
        except Exception as e:
            logger.error(f"Error mostrando tabla de personas: {e}")
            st.info("📊 Tabla de personal no disponible")
        
        # Gráfico de evolución de investigadores
        try:
            grafico_evol = DFs['componentes'].get('grafico_evolucion_investigadores', {})
            if grafico_evol.get('figura'):
                logger.debug("Mostrando gráfico de evolución de investigadores")
                st.plotly_chart(grafico_evol['figura'])
                if grafico_evol.get('fuente'):
                    st.caption(f"Fuente: {grafico_evol['fuente']}")
            else:
                logger.info("Gráfico de evolución no disponible")
                st.info("📊 Evolución de investigadores no disponible")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de evolución: {e}")
            st.warning("No se pudo cargar el gráfico de evolución")
            
    except Exception as e:
        logger.error(f"Error crítico en tab de capital humano: {e}", exc_info=True)
        st.error("Error al cargar datos de capital humano. Por favor, intente recargar la página.")


def render_resultados_tab(DFs):
    """Renderiza el tab de resultados con manejo completo de errores"""
    try:
        logger.debug("Renderizando tab de resultados")
        st.markdown("")
        
        # Sección de Exportaciones
        graficos_exportaciones = [
            ('grafico_expo_intensidad', 'Composición de exportaciones'),
            ('grafico_expo_evolucion', 'Evolución de exportaciones'),
            ('grafico_expo_destino', 'Destino de exportaciones')
        ]
        
        for grafico_name, descripcion in graficos_exportaciones:
            try:
                grafico = DFs['componentes'].get(grafico_name, {})
                if grafico.get('figura'):
                    logger.debug(f"Mostrando {descripcion}")
                    st.plotly_chart(grafico['figura'])
                    if grafico.get('fuente'):
                        st.caption(f"Fuente: {grafico['fuente']}")
                    st.markdown("")
                else:
                    logger.info(f"{descripcion} no disponible")
            except Exception as e:
                logger.error(f"Error mostrando {grafico_name}: {e}")
                st.warning(f"No se pudo cargar {descripcion.lower()}")
        
        st.markdown("---")
        
        # Sección de Patentes - KPIs
        col1, col2, col3 = st.columns([6, 1, 3], vertical_alignment="center")
        
        try:
            # KPI Provincial
            with col1:
                kpi_prov = DFs['componentes'].get('kpi_patentes_cyt_prov', {})
                if kpi_prov and kpi_prov.get('titulo') and kpi_prov.get('valor'):
                    st.metric(
                        label=f":primary[{kpi_prov['titulo']}]",
                        value=kpi_prov['valor'],
                        delta=None,
                    )
                    logger.debug(f"KPI patentes provincial: {kpi_prov['valor']}")
                else:
                    logger.warning("KPI patentes provincial sin datos")
                    st.metric(label=":primary[Patentes provinciales]", value="N/A")
        except Exception as e:
            logger.error(f"Error en KPI patentes provincial: {e}")
        
        col1b, col2b, col3b = st.columns([2, 6, 2])
        try:
            # KPI CyT Argentina
            with col2b:
                kpi_cyt = DFs['componentes'].get('kpi_patentes_cyt_arg', {})
                if kpi_cyt and kpi_cyt.get('titulo') and kpi_cyt.get('valor'):
                    st.metric(
                        label=f":primary[{kpi_cyt['titulo']}]",
                        value=kpi_cyt['valor'],
                        delta=None
                    )
                    logger.debug(f"KPI patentes CyT: {kpi_cyt['valor']}")
                else:
                    logger.warning("KPI patentes CyT sin datos")
                    st.metric(label=":primary[Patentes CyT Argentina]", value="N/A")
        except Exception as e:
            logger.error(f"Error en KPI patentes CyT: {e}")
        
        col1c, col2c, col3c = st.columns([2, 2, 6])
        try:
            # KPI Argentina total
            with col3c:
                kpi_arg = DFs['componentes'].get('kpi_patentes_arg', {})
                if kpi_arg and kpi_arg.get('titulo') and kpi_arg.get('valor'):
                    st.metric(
                        label=f":primary[{kpi_arg['titulo']}]",
                        value=kpi_arg['valor'],
                        delta=None
                    )
                    logger.debug(f"KPI patentes Argentina: {kpi_arg['valor']}")
                else:
                    logger.warning("KPI patentes Argentina sin datos")
                    st.metric(label=":primary[Patentes Argentina]", value="N/A")
        except Exception as e:
            logger.error(f"Error en KPI patentes Argentina: {e}")
        
        # Fuente de patentes
        if DFs['componentes'].get('kpi_patentes_arg', {}).get('fuente'):
            st.caption(f"Fuente: {DFs['componentes']['kpi_patentes_arg']['fuente']}")
        st.markdown("---")
        
        # Gráfico de evolución de patentes
        try:
            grafico_patentes = DFs['componentes'].get('grafico_patentes_evolucion', {})
            if grafico_patentes.get('figura') is not None:
                logger.debug("Mostrando evolución de patentes")
                st.plotly_chart(grafico_patentes['figura'])
                if grafico_patentes.get('fuente'):
                    st.caption(f"Fuente: {grafico_patentes['fuente']}")
                st.markdown("---")
            else:
                logger.info("Gráfico de patentes no disponible")
        except Exception as e:
            logger.error(f"Error mostrando evolución de patentes: {e}")
        
        # Tabla de patentes por sector
        try:
            tabla_patentes = DFs['componentes'].get('tabla_patentes_sector', {})
            if tabla_patentes.get('figura') is not None:
                logger.debug("Mostrando tabla de patentes por sector")
                great_tables(tabla_patentes['figura'])
                if tabla_patentes.get('fuente'):
                    st.caption(f"Fuente: {tabla_patentes['fuente']}")
                st.markdown("---")
            else:
                logger.info("Tabla de patentes no disponible")
        except Exception as e:
            logger.error(f"Error mostrando tabla de patentes: {e}")
        
        # Sección de Producción Científica
        graficos_produccion = [
            ('grafico_produccion_evolucion', 'Evolución de producción científica'),
            ('grafico_produccion_tipo', 'Distribución por tipo de publicación'),
            ('grafico_publicaciones_area', 'Publicaciones por área de conocimiento')
        ]
        
        for grafico_name, descripcion in graficos_produccion:
            try:
                grafico = DFs['componentes'].get(grafico_name, {})
                if grafico.get('figura'):
                    logger.debug(f"Mostrando {descripcion}")
                    st.plotly_chart(grafico['figura'])
                    if grafico.get('fuente'):
                        st.caption(f"Fuente: {grafico['fuente']}")
                    st.markdown("---")
                else:
                    logger.info(f"{descripcion} no disponible")
            except Exception as e:
                logger.error(f"Error mostrando {grafico_name}: {e}")
                st.warning(f"No se pudo cargar {descripcion.lower()}")
        
        # Tabla de artículos Q1/Q2
        try:
            tabla_articulos = DFs['componentes'].get('tabla_articulos_q1_q2', {})
            if tabla_articulos.get('figura') is not None:
                logger.debug("Mostrando tabla de artículos Q1/Q2")
                great_tables(tabla_articulos['figura'])
                if tabla_articulos.get('fuente'):
                    st.caption(f"Fuente: {tabla_articulos['fuente']}")
            else:
                logger.info("Tabla de artículos Q1/Q2 no disponible")
        except Exception as e:
            logger.error(f"Error mostrando tabla de artículos: {e}")
            
    except Exception as e:
        logger.error(f"Error crítico en tab de resultados: {e}", exc_info=True)
        st.error("Error al cargar datos de resultados. Por favor, intente recargar la página.")


def render_ciencia_sociedad_tab(DFs):
    """Renderiza el tab de ciencia y sociedad con validación"""
    try:
        logger.debug("Renderizando tab de ciencia y sociedad")
        st.markdown("")
        
        # Gráfico de percepción de temas prioritarios
        try:
            grafico_temas = DFs['componentes'].get('grafico_percepcion_temas_prioritarios', {})
            if grafico_temas.get('figura'):
                logger.debug("Mostrando gráfico de percepción de temas prioritarios")
                st.plotly_chart(grafico_temas['figura'], use_container_width=True)
                if grafico_temas.get('fuente'):
                    st.caption(f"Fuente: {grafico_temas['fuente']}")
                st.markdown("---")
            else:
                logger.info("Gráfico de temas prioritarios no disponible")
                st.info("📊 Datos de percepción sobre temas prioritarios no disponibles")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de temas prioritarios: {e}")
            st.warning("No se pudo cargar el gráfico de temas prioritarios")
        
        # Gráfico de percepción sobre calidad de vida
        try:
            grafico_calidad = DFs['componentes'].get('grafico_percepcion_calidad_vida', {})
            if grafico_calidad.get('figura'):
                logger.debug("Mostrando gráfico de percepción de calidad de vida")
                st.plotly_chart(grafico_calidad['figura'], use_container_width=True)
                if grafico_calidad.get('fuente'):
                    st.caption(f"Fuente: {grafico_calidad['fuente']}")
                st.markdown("")
            else:
                logger.info("Gráfico de calidad de vida no disponible")
                st.info("📊 Datos de percepción sobre calidad de vida no disponibles")
        except Exception as e:
            logger.error(f"Error mostrando gráfico de calidad de vida: {e}")
            st.warning("No se pudo cargar el gráfico de calidad de vida")
        
        # Información adicional o mensaje si no hay datos
        componentes_disponibles = sum(
            1 for comp in ['grafico_percepcion_temas_prioritarios', 'grafico_percepcion_calidad_vida']
            if DFs['componentes'].get(comp, {}).get('figura')
        )
        
        if componentes_disponibles == 0:
            st.info("""
            📊 **Sección en desarrollo**
            
            Los datos de percepción ciudadana sobre ciencia y tecnología están siendo recolectados
            y estarán disponibles próximamente.
            """)
            logger.info("Tab ciencia y sociedad sin datos disponibles")
        else:
            logger.info(f"Tab ciencia y sociedad con {componentes_disponibles} componentes disponibles")
            
    except Exception as e:
        logger.error(f"Error crítico en tab de ciencia y sociedad: {e}", exc_info=True)
        st.error("Error al cargar datos de ciencia y sociedad. Por favor, intente recargar la página.")


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
