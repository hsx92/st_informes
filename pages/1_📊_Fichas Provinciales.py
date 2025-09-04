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
from css_utils import load_css


st.set_page_config(page_title="Portal - SICyT", page_icon=st.secrets["LOGO_CORTO"], layout="wide")
st.logo(image=st.secrets["LOGO_LARGO"], size="large")

# ---- CSS ----

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


# ---- MAINPAGE ----
def panomProvincial():
    """Render the provincial dashboard page.

    Loads provincial data, displays metrics and tables, and provides the
    option to export the report as a PDF.

    Returns:
        None: This function renders the page but does not return a value.
    """
    provinciasDF = get_provincias()

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
        st.session_state.provincia = provinciasDF[provinciasDF['nombre_iso'] == provincia]['provincia'].values[0]
        st.session_state.provincia_id = provinciasDF[provinciasDF['nombre_iso'] == provincia]['id'].values[0]
        st.session_state.region = provinciasDF[provinciasDF['nombre_iso'] == provincia]['region'].values[0]
        st.session_state.pais = 'Argentina'
        st.session_state.anio = '2023'

        DFs = ficha_provincial_figs(
            provincia_id=st.session_state.provincia_id,
            provincia=st.session_state.provincia,
            anio=st.session_state.anio
        )

        st.markdown(f"## {provincia}")

        indicadoresTab, inversionTab, proyectosTab, infraestructuraTab, capitalHumanoTab, resultadosTab, ciencia_sociedadTab = st.tabs(
            ["Indicadores de contexto", "Inversión en I+D", "Proyectos", "Infraestructura", "Capital Humano", "Resultados", "Ciencia y Sociedad"]
        )

        with indicadoresTab:
            st.markdown("")

            col1, col2, col3, col4, col5 = st.columns([1, 3.75, .5, 3.75, 1])
            with col2:
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_poblacion_prov']['titulo']}]",
                    value=DFs['componentes']['kpi_poblacion_prov']['valor'],
                    delta=None,
                )
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_tasa_actividad_prov']['titulo']}]",
                    value=DFs['componentes']['kpi_tasa_actividad_prov']['valor'],
                    delta=None,
                )
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_tasa_desempleo_prov']['titulo']}]",
                    value=DFs['componentes']['kpi_tasa_desempleo_prov']['valor'],
                    delta=None,
                )
            with col4:
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_densidad_prov']['titulo']}]",
                    value=DFs['componentes']['kpi_densidad_prov']['valor'],
                    delta=None,
                )
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_tasa_actividad_nac']['titulo']}]",
                    value=DFs['componentes']['kpi_tasa_actividad_nac']['valor'],
                    delta=None,
                )
                st.metric(
                    label=f":primary[{DFs['componentes']['kpi_tasa_desempleo_nac']['titulo']}]",
                    value=DFs['componentes']['kpi_tasa_desempleo_nac']['valor'],
                    delta=None,
                )
            st.caption(f"Fuente: {DFs['componentes']['kpi_tasa_actividad_nac']['fuente']}")
            st.markdown("")

            st.plotly_chart(DFs['componentes']['grafico_expo_top5']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_expo_top5']['fuente']}")

        with inversionTab:
            st.plotly_chart(DFs['componentes']['grafico_evolucion_regional']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_evolucion_regional']['fuente']}")
            st.markdown("")

            st.plotly_chart(DFs['componentes']['grafico_inv_por_investigador']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_inv_por_investigador']['fuente']}")
            st.markdown("")

            st.plotly_chart(DFs['componentes']['grafico_inv_empresaria_sector']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_inv_empresaria_sector']['fuente']}")

        with proyectosTab:
            st.markdown("")
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

        with infraestructuraTab:
            st.markdown("")
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

        with capitalHumanoTab:
            st.markdown("")

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

        with resultadosTab:
            st.markdown("")

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

        with ciencia_sociedadTab:
            st.markdown("")

            st.plotly_chart(DFs['componentes']['grafico_percepcion_temas_prioritarios']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_percepcion_temas_prioritarios']['fuente']}")
            st.markdown("---")

            st.plotly_chart(DFs['componentes']['grafico_percepcion_calidad_vida']['figura'], use_container_width=True)
            st.caption(f"Fuente: {DFs['componentes']['grafico_percepcion_calidad_vida']['fuente']}")
            st.markdown("")

        style_metric_cards()
        st.markdown("---")

        # --- EXPORTAR PDF ---
        col1, col2, col3 = st.columns(3)
        with col2:
            exportar = st.button("Exportar a PDF", use_container_width=True)
            if exportar:
                try:
                    data = preparar_data_pdf(DFs)
                    ficha_provincial_pdf(st.session_state.provincia, data, f"output/Ficha Provincial - {st.session_state.provincia}.pdf")
                    exportar = False
                except Exception as e:
                    st.error(f"Error al generar la ficha provincial: {e}")


try:
    st.session_state.authenticator.login(location='unrendered')
    if 'authentication_status' in st.session_state:
        if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
            st.warning("Debe estar logueado para acceder a esta información.")
            st.stop()  # App won't run anything after this line
        elif 'admin' not in st.session_state["roles"] and 'director' not in st.session_state["roles"]:
            st.error('Acceso no autorizado.')
            st.stop()
        else:
            panomProvincial()
except AttributeError:
    st.warning("Debe estar logueado para acceder a esta información.")
    st.stop()
