# import plotly.express as px
import streamlit as st
import plotly.express as px
from streamlit_extras.great_tables import great_tables
from streamlit_extras.metric_cards import style_metric_cards
from data_handler import get_provincias, get_informe, procesar_kpi, insertar_saltos, tabla_pivot


st.set_page_config(page_title="Portal - SICyT", page_icon=st.secrets["LOGO_CORTO"], layout="wide")
st.logo(image=st.secrets["LOGO_LARGO"], size="large")

# ---- Cargar CSS personalizado ----

custom_streamlit_css = """
    div[data-testid="stMetricValue"] > div {
        color: #354B6E;
    }
    div[data-testid="stMetricDelta"] > div {
        color: #FFFFFF;
    }
    """
# Leer el archivo CSS de icono-arg
with open("static/iconos/dist/css/icono-arg.css", "r") as css_file:
    css = css_file.read()

# Combine the icono-arg.css with the custom Streamlit CSS
    combined_css = f"""
    <style>
    {css}
    {custom_streamlit_css}
    </style>
    """

# Inyectar el CSS en la aplicación
st.markdown(combined_css, unsafe_allow_html=True)


# ---- MAINPAGE ----
def panomProvincial():
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
        st.session_state.provincia = provincia
        st.session_state.provincia_id = provinciasDF[provinciasDF['nombre_iso'] == provincia]['id'].values[0]
        st.session_state.region = provinciasDF[provinciasDF['nombre_iso'] == provincia]['region'].values[0]
        st.session_state.pais = 'Argentina'
        st.session_state.anio = '2023'

        DFs = get_informe("ficha_provincial", {
            "provincia_id": st.session_state.provincia_id,
            "provincia": st.session_state.provincia,
            "anio": st.session_state.anio
        })

        # ################################## COMPONENTES #######################################
        kpi_poblacion_prov = {'nombre': DFs["componentes"]["kpi_poblacion_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_poblacion_prov"]["resultado_sql"], DFs["componentes"]["kpi_poblacion_prov"]["config"])}
        kpi_densidad_prov = {'nombre': DFs["componentes"]["kpi_densidad_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_densidad_prov"]["resultado_sql"], DFs["componentes"]["kpi_densidad_prov"]["config"])}
        kpi_tasa_actividad_prov = {'nombre': DFs["componentes"]["kpi_tasa_actividad_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_actividad_prov"]["resultado_sql"], DFs["componentes"]["kpi_tasa_actividad_prov"]["config"])}
        kpi_tasa_actividad_nac = {'nombre': DFs["componentes"]["kpi_tasa_actividad_nac"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_actividad_nac"]["resultado_sql"], DFs["componentes"]["kpi_tasa_actividad_nac"]["config"])}
        kpi_tasa_desempleo_prov = {'nombre': DFs["componentes"]["kpi_tasa_desempleo_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_desempleo_prov"]["resultado_sql"], DFs["componentes"]["kpi_tasa_desempleo_prov"]["config"])}
        kpi_tasa_desempleo_nac = {'nombre': DFs["componentes"]["kpi_tasa_desempleo_nac"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_desempleo_nac"]["resultado_sql"], DFs["componentes"]["kpi_tasa_desempleo_nac"]["config"])}

        kpi_pfi_nacional = {'nombre': DFs["componentes"]["kpi_pfi_nacional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_pfi_nacional"]["resultado_sql"], DFs["componentes"]["kpi_pfi_nacional"]["config"])}
        kpi_pfi_regional = {'nombre': DFs["componentes"]["kpi_pfi_regional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_pfi_regional"]["resultado_sql"], DFs["componentes"]["kpi_pfi_regional"]["config"])}
        kpi_pfi_provincial = {'nombre': DFs["componentes"]["kpi_pfi_provincial"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_pfi_provincial"]["resultado_sql"], DFs["componentes"]["kpi_pfi_provincial"]["config"])}
        kpi_porc_privada_nacional = {'nombre': DFs["componentes"]["kpi_porc_privada_nacional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_porc_privada_nacional"]["resultado_sql"], DFs["componentes"]["kpi_porc_privada_nacional"]["config"])}
        kpi_porc_privada_regional = {'nombre': DFs["componentes"]["kpi_porc_privada_regional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_porc_privada_regional"]["resultado_sql"], DFs["componentes"]["kpi_porc_privada_regional"]["config"])}
        kpi_porc_privada_provincial = {'nombre': DFs["componentes"]["kpi_porc_privada_provincial"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_porc_privada_provincial"]["resultado_sql"], DFs["componentes"]["kpi_porc_privada_provincial"]["config"])}

        kpi_patentes_arg = {'nombre': DFs["componentes"]["kpi_patentes_arg"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_patentes_arg"]["resultado_sql"], DFs["componentes"]["kpi_patentes_arg"]["config"])}
        kpi_patentes_cyt_arg = {'nombre': DFs["componentes"]["kpi_patentes_cyt_arg"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_patentes_cyt_arg"]["resultado_sql"], DFs["componentes"]["kpi_patentes_cyt_arg"]["config"])}
        kpi_patentes_cyt_prov = {'nombre': DFs["componentes"]["kpi_patentes_cyt_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_patentes_cyt_prov"]["resultado_sql"], DFs["componentes"]["kpi_patentes_cyt_prov"]["config"])}

        kpi_unidades_id_prov = {'nombre': DFs["componentes"]["kpi_unidades_id_prov"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_unidades_id_prov"]["resultado_sql"], DFs["componentes"]["kpi_unidades_id_prov"]["config"])}

        kpi_equipos_nacional = {'nombre': DFs["componentes"]["kpi_equipos_nacional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_equipos_nacional"]["resultado_sql"], DFs["componentes"]["kpi_equipos_nacional"]["config"])}
        kpi_equipos_regional = {'nombre': DFs["componentes"]["kpi_equipos_regional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_equipos_regional"]["resultado_sql"], DFs["componentes"]["kpi_equipos_regional"]["config"])}
        kpi_equipos_provincial = {'nombre': DFs["componentes"]["kpi_equipos_provincial"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_equipos_provincial"]["resultado_sql"], DFs["componentes"]["kpi_equipos_provincial"]["config"])}

        kpi_tasa_pea_provincial = {'nombre': DFs["componentes"]["kpi_tasa_pea_provincial"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_pea_provincial"]["resultado_sql"], DFs["componentes"]["kpi_tasa_pea_provincial"]["config"])}
        kpi_tasa_pea_regional = {'nombre': DFs["componentes"]["kpi_tasa_pea_regional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_pea_regional"]["resultado_sql"], DFs["componentes"]["kpi_tasa_pea_regional"]["config"])}
        kpi_tasa_pea_nacional = {'nombre': DFs["componentes"]["kpi_tasa_pea_nacional"]["nombre"], 'valor': procesar_kpi(DFs["componentes"]["kpi_tasa_pea_nacional"]["resultado_sql"], DFs["componentes"]["kpi_tasa_pea_nacional"]["config"])}

        grafico_expo_top5 = DFs["componentes"]["grafico_expo_top5"]

        grafico_evolucion_regional = DFs["componentes"]["grafico_evolucion_regional"]
        grafico_inv_por_investigador = DFs["componentes"]["grafico_inv_por_investigador"]
        grafico_inv_empresaria_sector = DFs["componentes"]["grafico_inv_empresaria_sector"]

        tabla_pfi_cruce = DFs["componentes"]["tabla_pfi_cruce"]

        grafico_expo_intensidad = DFs["componentes"]["grafico_expo_intensidad"]
        grafico_expo_evolucion = DFs["componentes"]["grafico_expo_evolucion"]
        grafico_expo_destino = DFs["componentes"]["grafico_expo_destino"]

        grafico_patentes_evolucion = DFs["componentes"]["grafico_patentes_evolucion"]
        tabla_patentes_sector = DFs["componentes"]["tabla_patentes_sector"]
        grafico_produccion_evolucion = DFs["componentes"]["grafico_produccion_evolucion"]
        grafico_produccion_tipo = DFs["componentes"]["grafico_produccion_tipo"]
        tabla_articulos_q1_q2 = DFs["componentes"]["tabla_articulos_q1_q2"]
        grafico_publicaciones_area = DFs["componentes"]["grafico_publicaciones_area"]

        grafico_unidades_por_inst = DFs["componentes"]["grafico_unidades_por_inst"]
        grafico_equipos_por_tipo = DFs["componentes"]["grafico_equipos_por_tipo"]

        grafico_distribucion_investigadores = DFs["componentes"]["grafico_distribucion_investigadores"]
        tabla_personas_por_funcion = DFs["componentes"]["tabla_personas_por_funcion"]
        grafico_evolucion_investigadores = DFs["componentes"]["grafico_evolucion_investigadores"]

        grafico_percepcion_calidad_vida = DFs["componentes"]["grafico_percepcion_calidad_vida"]

        #######################################################################################

        st.markdown(f"## {provincia}")

        indicadoresTab, inversionTab, proyectosTab, infraestructuraTab, capitalHumanoTab, resultadosTab, ciencia_sociedadTab, test = st.tabs(
            ["Indicadores de contexto", "Inversión en I+D", "Proyectos", "Infraestructura", "Capital Humano", "Resultados", "Ciencia y Sociedad", "Test"]
        )

        with indicadoresTab:
            st.markdown("")
            col1, col2, col3, col4, col5 = st.columns([1, 3.75, .5, 3.75, 1])
            with col2:
                st.metric(label=f":primary[{kpi_poblacion_prov["nombre"]}]", value=kpi_poblacion_prov["valor"], delta=None)
                st.metric(label=f":primary[{kpi_tasa_actividad_prov["nombre"]}]", value=kpi_tasa_actividad_prov["valor"], delta=None)
                st.metric(label=f":primary[{kpi_tasa_desempleo_prov["nombre"]}]", value=kpi_tasa_desempleo_prov["valor"], delta=None)

            with col4:
                st.metric(label=f":primary[{kpi_densidad_prov["nombre"]}]", value=kpi_densidad_prov["valor"], delta=None)
                st.metric(label=f":primary[{kpi_tasa_actividad_nac["nombre"]}]", value=kpi_tasa_actividad_nac["valor"], delta=None)
                st.metric(label=f":primary[{kpi_tasa_desempleo_nac["nombre"]}]", value=kpi_tasa_desempleo_nac["valor"], delta=None)
            st.caption("Fuente: INDEC")
            st.markdown("")

            grafico_expo_top5['resultado_sql'].iloc[:, 0] = grafico_expo_top5['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

            top5_exportaciones_fig = px.bar(
                data_frame=grafico_expo_top5['resultado_sql'],
                x=grafico_expo_top5['config']['plot_mapping']['x'],
                y=grafico_expo_top5['config']['plot_mapping']['y'],
                labels=grafico_expo_top5['config']['plot_mapping']['labels'],
                title=grafico_expo_top5['nombre'],
                template="seaborn",
                orientation='h',
                color=grafico_expo_top5['config']['plot_mapping']['y'],
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#F2C94C", "#E26D5C", "#9B51E0", "#56CCF2", "#27AE60"]
            )
            top5_exportaciones_fig.update_layout(grafico_expo_top5['config']['layout'])
            top5_exportaciones_fig.update_layout(showlegend=False)

            st.plotly_chart(top5_exportaciones_fig, use_container_width=True)
            st.caption("Fuente: OPEX - INDEC")
            DFs['componentes']['grafico_expo_top5']['img'] = top5_exportaciones_fig.to_image(format="png", width=1200, height=600)

        with inversionTab:
            inversionID_fig = px.line(
                data_frame=grafico_evolucion_regional['resultado_sql'],
                x=grafico_evolucion_regional['config']['plot_mapping']['x'],
                y=grafico_evolucion_regional['config']['plot_mapping']['y'],
                labels=grafico_evolucion_regional['config']['plot_mapping']['labels'],
                title=grafico_evolucion_regional['nombre'],
                template="seaborn",
                color=grafico_evolucion_regional['config']['plot_mapping']['color']
            )
            inversionID_fig.update_layout(grafico_evolucion_regional['config']['layout'])
            st.plotly_chart(inversionID_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")
            st.markdown("")

            inversionInvestigador_fig = px.bar(
                data_frame=grafico_inv_por_investigador['resultado_sql'],
                y=grafico_inv_por_investigador['config']['plot_mapping']['y'],
                x=grafico_inv_por_investigador['config']['plot_mapping']['x'],
                labels=grafico_inv_por_investigador['config']['plot_mapping']['labels'],
                title=grafico_inv_por_investigador['nombre'],
                template="seaborn",
                orientation='h'
            )
            inversionInvestigador_fig.update_layout(grafico_inv_por_investigador['config']['layout'])
            st.plotly_chart(inversionInvestigador_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")
            st.markdown("")

            grafico_inv_empresaria_sector['resultado_sql'].iloc[:, 0] = grafico_inv_empresaria_sector['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

            inversionEmpresas_fig = px.bar(
                data_frame=grafico_inv_empresaria_sector['resultado_sql'],
                y=grafico_inv_empresaria_sector['config']['plot_mapping']['y'],
                x=grafico_inv_empresaria_sector['config']['plot_mapping']['x'],
                labels=grafico_inv_empresaria_sector['config']['plot_mapping']['labels'],
                title=grafico_inv_empresaria_sector['nombre'],
                template="seaborn",
                orientation='h',
                color=grafico_inv_empresaria_sector['config']['plot_mapping']['y'],
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#F2C94C", "#E26D5C", "#9B51E0", "#56CCF2", "#27AE60"]
            )

            inversionEmpresas_fig.update_layout(grafico_inv_empresaria_sector['config']['layout'])
            inversionEmpresas_fig.update_layout(showlegend=False)
            st.plotly_chart(inversionEmpresas_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")

            DFs['componentes']['grafico_evolucion_regional']['img'] = inversionID_fig.to_image(format="png", width=1200, height=600)
            DFs['componentes']['grafico_inv_por_investigador']['img'] = inversionInvestigador_fig.to_image(format="png", width=1200, height=600)
            DFs['componentes']['grafico_inv_empresaria_sector']['img'] = inversionEmpresas_fig.to_image(format="png", width=1200, height=600)

        with proyectosTab:
            st.markdown("")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f":primary[{kpi_pfi_provincial["nombre"]}]", value=kpi_pfi_provincial["valor"], delta=None)
                st.metric(label=f":primary[{kpi_porc_privada_provincial["nombre"]}]", value=kpi_porc_privada_provincial["valor"], delta=None)
            with col2:
                st.metric(label=f":primary[{kpi_pfi_regional["nombre"]}]", value=kpi_pfi_regional["valor"], delta=None)
                st.metric(label=f":primary[{kpi_porc_privada_regional["nombre"]}]", value=kpi_porc_privada_regional["valor"], delta=None)
            with col3:
                st.metric(label=f":primary[{kpi_pfi_nacional["nombre"]}]", value=kpi_pfi_nacional["valor"], delta=None)
                st.metric(label=f":primary[{kpi_porc_privada_nacional["nombre"]}]", value=kpi_porc_privada_nacional["valor"], delta=None)
            st.caption("*PFI: Proyectos Federales de Innovación")
            st.caption("Fuente: DNIYES")
            st.markdown("")

            tabla_pfi_cruce_fig, tabla_pfi_cruce_DF = tabla_pivot(tabla_pfi_cruce)
            great_tables(tabla_pfi_cruce_fig)
            st.caption("Fuente: DNIYES")

            DFs['componentes']['tabla_pfi_cruce']['df'] = tabla_pfi_cruce_DF
            st.markdown("")

        with infraestructuraTab:
            st.markdown("")
            col0, col1, col2 = st.columns([.25, 2.5, 7.25], vertical_alignment="center")
            with col1:
                st.metric(label=f":primary[{kpi_unidades_id_prov['nombre']}]", value=kpi_unidades_id_prov['valor'], delta=None)
            with col2:
                st.markdown(f"#### {grafico_unidades_por_inst['nombre']}")

            grafico_unidades_por_inst['resultado_sql'].iloc[:, 0] = grafico_unidades_por_inst['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

            unidadesIDxinstitucion_fig = px.bar(
                data_frame=grafico_unidades_por_inst['resultado_sql'],
                y=grafico_unidades_por_inst['config']['plot_mapping']['y'],
                x=grafico_unidades_por_inst['config']['plot_mapping']['x'],
                labels=grafico_unidades_por_inst['config']['plot_mapping']['labels'],
                title=None,  # grafico_unidades_por_inst['nombre'],
                template="seaborn",
                orientation='h',
                color=grafico_unidades_por_inst['config']['plot_mapping']['y'],
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#F2C94C", "#E26D5C", "#9B51E0", "#56CCF2", "#27AE60"]
            )
            unidadesIDxinstitucion_fig.update_layout(grafico_unidades_por_inst['config']['layout'])
            unidadesIDxinstitucion_fig.update_layout(margin=dict(l=0, r=20, t=0, b=20), showlegend=False)
            st.plotly_chart(unidadesIDxinstitucion_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")
            st.markdown("---")
            DFs['componentes']['grafico_unidades_por_inst']['img'] = unidadesIDxinstitucion_fig.to_image(format="png", width=1200, height=600)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f":primary[{kpi_equipos_provincial['nombre']}]", value=kpi_equipos_provincial['valor'], delta=None)
            with col2:
                st.metric(label=f":primary[{kpi_equipos_regional['nombre']}]", value=kpi_equipos_regional['valor'], delta=None)
            with col3:
                st.metric(label=f":primary[{kpi_equipos_nacional['nombre']}]", value=kpi_equipos_nacional['valor'], delta=None)
            st.caption("Fuente: DNIYES")
            st.markdown("")

            equiposIDxTipo_fig = px.bar(
                data_frame=grafico_equipos_por_tipo['resultado_sql'],
                y=grafico_equipos_por_tipo['config']['plot_mapping']['y'],
                x=grafico_equipos_por_tipo['config']['plot_mapping']['x'],
                labels=grafico_equipos_por_tipo['config']['plot_mapping']['labels'],
                title=grafico_equipos_por_tipo['nombre'],
                color=grafico_equipos_por_tipo['config']['plot_mapping']['y'],
                template="seaborn",
                orientation='h'
            )
            equiposIDxTipo_fig.update_layout(grafico_equipos_por_tipo['config']['layout'])
            equiposIDxTipo_fig.update_layout(showlegend=False)
            st.plotly_chart(equiposIDxTipo_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")
            DFs['componentes']['grafico_equipos_por_tipo']['img'] = equiposIDxTipo_fig.to_image(format="png", width=1200, height=600)

        with capitalHumanoTab:
            st.markdown("")
            investigadoresxArea_fig = px.treemap(
                title=grafico_distribucion_investigadores['nombre'],
                data_frame=grafico_distribucion_investigadores['resultado_sql'],
                path=grafico_distribucion_investigadores['config']['plot_mapping']['path'],
                values=grafico_distribucion_investigadores['config']['plot_mapping']['values'],
                labels=grafico_distribucion_investigadores['config']['plot_mapping']['labels'],
                color=grafico_distribucion_investigadores['config']['plot_mapping']['color'],
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#F2C94C", "#E26D5C", "#9B51E0", "#56CCF2", "#27AE60"],
            )
            investigadoresxArea_fig.update_traces(
                textinfo=grafico_distribucion_investigadores['config']['traces']['textinfo'],
                textposition=grafico_distribucion_investigadores['config']['traces']['textposition'],
                marker=dict(cornerradius=5))

            investigadoresxArea_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(investigadoresxArea_fig, use_container_width=True)
            st.caption("Fuente: DNIYES")
            st.markdown("")
            DFs['componentes']['grafico_distribucion_investigadores']['img'] = investigadoresxArea_fig.to_image(format="png", width=1200, height=600)

            col1, col2, col3 = st.columns(3, border=True)
            with col1:
                st.markdown(f"#### {st.session_state.provincia}")
                st.metric(label=":primary[Investigadores cada 1000 habs.]", value=kpi_tasa_pea_provincial['valor'], delta=None)
            with col2:
                st.markdown(f"#### {st.session_state.region}")
                st.metric(label=":primary[Investigadores cada 1000 habs.]", value=kpi_tasa_pea_regional['valor'], delta=None)
            with col3:
                st.markdown(f"#### {st.session_state.pais}")
                st.metric(label=":primary[Investigadores cada 1000 habs.]", value=kpi_tasa_pea_nacional['valor'], delta=None)
            st.caption("Fuente: DNIYES")
            st.markdown("")

            tabla_personas_por_funcion_fig, tabla_personas_por_funcion_DF = tabla_pivot(tabla_personas_por_funcion)
            great_tables(tabla_personas_por_funcion_fig)
            st.caption("Fuente: DNIYES")

            DFs['componentes']['tabla_personas_por_funcion']['df'] = tabla_personas_por_funcion_DF
            st.markdown("---")

            evolucionInvestigadores_fig = px.line(
                data_frame=grafico_evolucion_investigadores['resultado_sql'],
                x=grafico_evolucion_investigadores['config']['plot_mapping']['x'],
                y=grafico_evolucion_investigadores['config']['plot_mapping']['y'],
                labels=grafico_evolucion_investigadores['config']['plot_mapping']['labels'],
                title=grafico_evolucion_investigadores['nombre'],
                template="seaborn"
            )
            evolucionInvestigadores_fig.update_layout(grafico_evolucion_investigadores['config']['layout'])
            evolucionInvestigadores_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(evolucionInvestigadores_fig)
            st.caption("Fuente: DNIYES")
            DFs['componentes']['grafico_evolucion_investigadores']['img'] = evolucionInvestigadores_fig.to_image(format="png", width=1200, height=600)

        with resultadosTab:
            st.markdown("")
            exportacionesIntensidad_fig = px.pie(
                data_frame=grafico_expo_intensidad['resultado_sql'],
                names=grafico_expo_intensidad['config']['plot_mapping']['names'],
                values=grafico_expo_intensidad['config']['plot_mapping']['values'],
                labels=grafico_expo_intensidad['config']['plot_mapping']['labels'],
                title=grafico_expo_intensidad['nombre'],
                template="seaborn",
                hole=0.4
            )
            exportacionesIntensidad_fig.update_layout(grafico_expo_intensidad['config']['layout'])
            exportacionesIntensidad_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(exportacionesIntensidad_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("")
            DFs['componentes']['grafico_expo_intensidad']['img'] = exportacionesIntensidad_fig.to_image(format="png", width=1200, height=600)

            evolucionExportaciones_fig = px.line(
                data_frame=grafico_expo_evolucion['resultado_sql'],
                x=grafico_expo_evolucion['config']['plot_mapping']['x'],
                y=grafico_expo_evolucion['config']['plot_mapping']['y'],
                labels=grafico_expo_evolucion['config']['plot_mapping']['labels'],
                title=grafico_expo_evolucion['nombre'],
                color=grafico_expo_evolucion['config']['plot_mapping']['color'],
                template="seaborn"
            )
            evolucionExportaciones_fig.update_layout(grafico_expo_evolucion['config']['layout'])
            evolucionExportaciones_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(evolucionExportaciones_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("")
            DFs['componentes']['grafico_expo_evolucion']['img'] = evolucionExportaciones_fig.to_image(format="png", width=1200, height=600)

            exportacionesxPais_fig = px.treemap(
                data_frame=grafico_expo_destino['resultado_sql'],
                path=grafico_expo_destino['config']['plot_mapping']['path'],
                values=grafico_expo_destino['config']['plot_mapping']['values'],
                color=grafico_expo_destino['config']['plot_mapping']['color'],
                title=grafico_expo_destino['nombre'],
                template="seaborn",
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#F2C94C", "#E26D5C", "#D4BCEA", "#93D8EF", "#27AE60"]
            )
            exportacionesxPais_fig.update_traces(grafico_expo_destino['config']['traces'])
            exportacionesxPais_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=0)
            )
            st.plotly_chart(exportacionesxPais_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("---")
            DFs['componentes']['grafico_expo_destino']['img'] = exportacionesxPais_fig.to_image(format="png", width=1200, height=600)

            col1, col2, col3 = st.columns([6, 1, 3], vertical_alignment="center")
            with col1:
                st.metric(label=f":primary[{kpi_patentes_cyt_prov['nombre']}]", value=kpi_patentes_cyt_prov['valor'], delta=None)
            col1b, col2b, col3b = st.columns([2, 6, 2])
            with col2b:
                st.metric(label=f":primary[{kpi_patentes_cyt_arg['nombre']}]", value=kpi_patentes_cyt_arg['valor'], delta=None)
            col1c, col2c, col3c = st.columns([2, 2, 6])
            with col3c:
                st.metric(label=f":primary[{kpi_patentes_arg['nombre']}]", value=kpi_patentes_arg['valor'], delta=None)
            st.caption("Fuente: Elaboración propia en base a datos de THE LENS")
            st.markdown("---")

            evolucionPatentes_fig = px.line(
                data_frame=grafico_patentes_evolucion['resultado_sql'],
                x=grafico_patentes_evolucion['config']['plot_mapping']['x'],
                y=grafico_patentes_evolucion['config']['plot_mapping']['y'],
                labels=grafico_patentes_evolucion['config']['plot_mapping']['labels'],
                title=grafico_patentes_evolucion['nombre'],
                template="seaborn"
            )
            evolucionPatentes_fig.update_layout(grafico_patentes_evolucion['config']['layout'])
            evolucionPatentes_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            # Si el dataframe no tiene info, no mostrar
            if grafico_patentes_evolucion['resultado_sql'] is not None and not grafico_patentes_evolucion['resultado_sql'].empty:
                st.plotly_chart(evolucionPatentes_fig)
                st.caption("Fuente: Elaboración propia en base a datos de THE LENS")
                st.markdown("---")
                DFs['componentes']['grafico_patentes_evolucion']['img'] = evolucionPatentes_fig.to_image(format="png", width=1200, height=600)

            tabla_patentes_sector_fig, tabla_patentes_sector_DF = tabla_pivot(tabla_patentes_sector)
            great_tables(tabla_patentes_sector_fig)
            st.caption("Fuente: Elaboración propia en base a datos de THE LENS")

            DFs['componentes']['tabla_patentes_sector']['df'] = tabla_patentes_sector_DF
            st.markdown("---")

            produccionProvincial_fig = px.line(
                data_frame=grafico_produccion_evolucion['resultado_sql'],
                x=grafico_produccion_evolucion['config']['plot_mapping']['x'],
                y=grafico_produccion_evolucion['config']['plot_mapping']['y'],
                labels=grafico_produccion_evolucion['config']['plot_mapping']['labels'],
                title=grafico_produccion_evolucion['nombre'],
                color=grafico_produccion_evolucion['config']['plot_mapping']['color'],
                template="seaborn"
            )
            produccionProvincial_fig.update_layout(grafico_produccion_evolucion['config']['layout'])
            produccionProvincial_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(produccionProvincial_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("---")
            DFs['componentes']['grafico_produccion_evolucion']['img'] = produccionProvincial_fig.to_image(format="png", width=1200, height=600)

            distribucionPublicaciones_fig = px.treemap(
                data_frame=grafico_produccion_tipo['resultado_sql'],
                path=grafico_produccion_tipo['config']['plot_mapping']['path'],
                values=grafico_produccion_tipo['config']['plot_mapping']['values'],
                labels=grafico_produccion_tipo['config']['plot_mapping']['labels'],
                color=grafico_produccion_tipo['config']['plot_mapping']['color'],
                title=grafico_produccion_tipo['nombre'],
                template="seaborn"
            )
            distribucionPublicaciones_fig.update_traces(
                textinfo=grafico_produccion_tipo['config']['traces']['textinfo'],
                textposition=grafico_produccion_tipo['config']['traces']['textposition'],
                marker=dict(cornerradius=5)
            )
            distribucionPublicaciones_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )

            st.plotly_chart(distribucionPublicaciones_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("---")
            DFs['componentes']['grafico_produccion_tipo']['img'] = distribucionPublicaciones_fig.to_image(format="png", width=1200, height=600)

            publicacionesArea_fig = px.bar(
                data_frame=grafico_publicaciones_area['resultado_sql'],
                x=grafico_publicaciones_area['config']['plot_mapping']['x'],
                y=grafico_publicaciones_area['config']['plot_mapping']['y'],
                labels=grafico_publicaciones_area['config']['plot_mapping']['labels'],
                title=grafico_publicaciones_area['nombre'],
                color=grafico_publicaciones_area['config']['plot_mapping']['color'],
                color_discrete_sequence=["#4D7AAE", "#B9422D", "#B2713F", "#198769", "#5C3C7D", "#EBD081", "#E26D5C", "#9B51E0", "#56CCF2", "#27AE60"],
                orientation='h',
            )
            publicacionesArea_fig.update_traces(showlegend=False)
            publicacionesArea_fig.update_layout(grafico_publicaciones_area['config']['layout'])
            publicacionesArea_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=40, t=50, b=0)
            )
            st.plotly_chart(publicacionesArea_fig)
            st.caption("Fuente: DNIYES")
            st.markdown("---")
            DFs['componentes']['grafico_publicaciones_area']['img'] = publicacionesArea_fig.to_image(format="png", width=1200, height=600)
            # plotly.offline.plot()

            tabla_articulos_q1_q2_fig, tabla_articulos_q1_q2_DF = tabla_pivot(tabla_articulos_q1_q2)
            great_tables(tabla_articulos_q1_q2_fig)
            st.caption("Fuente: DNIYES")

            DFs['componentes']['tabla_articulos_q1_q2']['df'] = tabla_articulos_q1_q2_DF

        with ciencia_sociedadTab:
            st.markdown("")

            nBarras = len(provinciasDF)
            altura = 20 * nBarras + 150

            percepcionPublica_fig = px.bar(
                data_frame=grafico_percepcion_calidad_vida['resultado_sql'],
                y=grafico_percepcion_calidad_vida['config']['plot_mapping']['y'],
                x=grafico_percepcion_calidad_vida['config']['plot_mapping']['x'],
                labels=grafico_percepcion_calidad_vida['config']['plot_mapping']['labels'],
                title=None,
                template="seaborn",
                orientation='h',
                height=altura
            )
            percepcionPublica_fig.update_layout(grafico_percepcion_calidad_vida['config']['layout'])
            percepcionPublica_fig.update_layout(
                margin=dict(l=20, r=40, t=20, b=20)
            )

            st.markdown(f"### {grafico_percepcion_calidad_vida['nombre']}")
            st.plotly_chart(percepcionPublica_fig)
            st.caption("Fuente: SICYTAR")
            st.markdown("")
            DFs['componentes']['grafico_percepcion_calidad_vida']['img'] = percepcionPublica_fig.to_image(format="png", width=1200, height=600)

        with test:
            st.write(DFs)

        style_metric_cards()


try:
    st.session_state.authenticator.login(location='unrendered')
    if 'authentication_status' in st.session_state:
        if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
            st.warning("Debe estar logueado para acceder a esta información.")
            st.stop()  # App won't run anything after this line
        elif 'admin' not in st.session_state["roles"] and 'director' not in st.session_state["roles"]:
            st.error('Acceso no autorizado.')
        else:
            panomProvincial()
except AttributeError:
    st.warning("Debe estar logueado para acceder a esta información.")
