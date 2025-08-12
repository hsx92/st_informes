# import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from great_tables import GT
from great_tables.data import sp500
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.great_tables import great_tables
from data_handler import get_provincias


st.set_page_config(page_title="Consulta", page_icon=":bar_chart:", layout="wide")
st.logo(image=st.secrets["LOGO"], size="large")

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
        st.session_state.anio = '2023'

        st.markdown(f"### {provincia}")

        indicadoresTab, inversionTab, proyectosTab, infraestructuraTab, capitalHumanoTab, resultadosTab, ciencia_sociedadTab = st.tabs(
            ["Indicadores de contexto", "Inversión en I+D", "Proyectos", "Infraestructura", "Capital Humano", "Resultados", "Ciencia y Sociedad"]
        )

        with indicadoresTab:
            col1, col2, col3, col4, col5 = st.columns([1, 3.75, .5, 3.75, 1])
            with col2:
                st.metric(label=f":primary[Población de {provincia}]", value="5000000", delta=None)
                st.metric(label=":primary[Población Provincial]", value="5000000", delta=None)
                st.metric(label=":primary[Población Provincial]", value="5000000", delta=None)

            with col4:
                st.metric(label=":primary[Densidad Poblacional Provincial]", value="5000"+" hab/km²", delta=None)
                st.metric(label=":primary[Densidad Poblacional Provincial]", value="5000"+" hab/km²", delta=None)
                st.metric(label=":primary[Densidad Poblacional Provincial]", value="5000"+" hab/km²", delta=None)

            top5_exportaciones_fig = px.bar(
                y=["Producto A", "Producto B", "Producto C", "Producto D", "Producto E"],
                x=[100, 200, 300, 400, 500],
                labels={"x": "Exportaciones (en millones de USD)", "y": "Productos"},
                title=f"Top 5 Exportaciones ({st.session_state.anio})",
                template="seaborn",
                orientation='h'
            )
            top5_exportaciones_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.markdown("---")
            st.plotly_chart(top5_exportaciones_fig, use_container_width=True)

        with inversionTab:
            inversionID_fig = px.line(
                x=["2020", "2021", "2022", "2023"],
                y=[100, 200, 300, 400],
                labels={"x": "Año", "y": "Inversión en I+D (en millones de USD)"},
                title="Evolución de la Inversión en I+D",
                template="seaborn"
            )
            inversionID_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )

            inversionInvestigador_fig = px.bar(
                y=["Provincia A", "Provincia B", "Provincia C"],
                x=[50, 100, 150],
                labels={"x": "Inversión (en millones de USD)", "y": "Provincia"},
                title=f"Inversión por investigador en la Región ({st.session_state.anio})",
                template="seaborn",
                orientation='h'
            )
            inversionInvestigador_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )

            inversionEmpresas_fig = px.bar(
                y=["Sector A", "Sector B", "Sector C"],
                x=[200, 300, 400],
                labels={"x": "Inversión (en millones de USD)", "y": "Sector"},
                title=f"Inversión privada por sector en {provincia} ({st.session_state.anio})",
                template="seaborn",
                orientation='h'
            )
            inversionEmpresas_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )

            st.plotly_chart(inversionID_fig, use_container_width=True)
            st.markdown("---")
            st.plotly_chart(inversionInvestigador_fig, use_container_width=True)
            st.markdown("---")
            st.plotly_chart(inversionEmpresas_fig, use_container_width=True)
        with proyectosTab:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=":primary[Proyectos en curso]", value=150, delta=None)
                st.metric(label=":primary[Proyectos en curso]", value=150, delta=None)
            with col2:
                st.metric(label=":primary[Proyectos finalizados]", value=75, delta=None)
                st.metric(label=":primary[Proyectos en curso]", value=150, delta=None)
            with col3:
                st.metric(label=":primary[Proyectos en colaboración]", value=30, delta=None)
                st.metric(label=":primary[Proyectos en curso]", value=150, delta=None)
            st.markdown("---")

            # Define the start and end dates for the data range
            start_date = "2010-06-07"
            end_date = "2010-06-14"

            # Filter sp500 using Pandas to dates between `start_date` and `end_date`
            sp500_mini = sp500[(sp500["date"] >= start_date) & (sp500["date"] <= end_date)]

            # Create a display table based on the `sp500_mini` table data
            table = (
                GT(sp500_mini)
                .tab_header(title=f"S&P 500", subtitle=f"{start_date} to {end_date}")
                .fmt_currency(columns=["open", "high", "low", "close"])
                .fmt_date(columns="date", date_style="wd_m_day_year")
                .fmt_number(columns="volume", compact=True)
                .cols_hide(columns="adj_close")
            )

            great_tables(table, width="stretch")

        with infraestructuraTab:
            st.markdown("")
            col1, col2 = st.columns([2, 8])
            with col1:
                st.markdown("###")
                st.markdown("###")
                st.metric(label=f":primary[Unidades de I+D]", value=120, delta=None)
            with col2:
                unidadesIDxinstitucion_fig = px.bar(
                    y=["Institución A", "Institución B", "Institución C", "Institución D"],
                    x=[10, 20, 30, 40],
                    labels={"x": "Unidades de I+D", "y": "Institución"},
                    title=f"Unidades de I+D por institución en {provincia} ({st.session_state.anio})",
                    template="seaborn",
                    orientation='h'
                )
                unidadesIDxinstitucion_fig.update_layout(
                    title_x=.2,
                    title_font=dict(size=20),
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(unidadesIDxinstitucion_fig, use_container_width=True)
            st.markdown("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f":primary[Unidades de I+D en {provincia}]", value=120, delta=None)
            with col2:
                st.metric(label=f":primary[Unidades de I+D en {provincia}]", value=120, delta=None)
            with col3:
                st.metric(label=f":primary[Unidades de I+D en {provincia}]", value=120, delta=None)
            
            equiposIDxTipo_fig = px.bar(
                y=["Equipo A", "Equipo B", "Equipo C"],
                x=[50, 100, 150],
                labels={"x": "", "y": ""},
                title=f"Equipos de I+D por tipo en {provincia} ({st.session_state.anio})",
                template="seaborn",
                orientation='h'
            )
            equiposIDxTipo_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.markdown("")
            st.plotly_chart(equiposIDxTipo_fig, use_container_width=True)
        with capitalHumanoTab:
            investigadoresxArea_fig = px.bar(
                y=["Area A", "Area B", "Area C"],
                x=[50, 100, 150],
                labels={"x": "", "y": ""},
                title=f"Investigadores por área de conocimiento (%) ({st.session_state.anio})",
                template="seaborn",
                orientation='h'
            )
            investigadoresxArea_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.markdown("")
            st.plotly_chart(investigadoresxArea_fig, use_container_width=True)
            st.markdown("")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f":primary[Cantidad de investigadores por cada 1000 hab. de la PEA en {provincia}]", value=120, delta=None)
            with col2:
                st.metric(label=f":primary[Cantidad de investigadores por cada 1000 hab. de la PEA en la región]", value=120, delta=None)
            with col3:
                st.metric(label=f":primary[Cantidad de investigadores por cada 1000 hab. de la PEA en Argentina]", value=120, delta=None)
            st.markdown("---")

            # Define the start and end dates for the data range
            start_date = "2010-06-07"
            end_date = "2010-06-14"

            # Filter sp500 using Pandas to dates between `start_date` and `end_date`
            sp500_mini = sp500[(sp500["date"] >= start_date) & (sp500["date"] <= end_date)]

            # Create a display table based on the `sp500_mini` table data
            table = (
                GT(sp500_mini)
                .tab_header(title=f"S&P 500", subtitle=f"{start_date} to {end_date}")
                .fmt_currency(columns=["open", "high", "low", "close"])
                .fmt_date(columns="date", date_style="wd_m_day_year")
                .fmt_number(columns="volume", compact=True)
                .cols_hide(columns="adj_close")
            )

            great_tables(table, width="stretch")

            st.markdown("---")

            evolucionInvestigadores_fig = px.line(
                x=["2020", "2021", "2022", "2023"],
                y=[100, 200, 300, 400],
                labels={"x": "", "y": "Cantidad de investigadores"},
                title=f"Evolución de la cantidad de investigadores (2019 - {st.session_state.anio})",
                template="seaborn"
            )
            evolucionInvestigadores_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(evolucionInvestigadores_fig)

        with resultadosTab:
            st.markdown("")
            exportacionesIntensidad_fig = px.pie(
                names=["Alta Tecnología", "Media Alta Tecnología", "Media Baja Tecnología", "Baja Tecnología"],
                values=[400, 300, 200, 100],
                labels={"values": "Exportaciones (en millones de USD)", "names": "Intensidad Tecnológica"},
                title=f"Exportaciones provinciales por intensidad tecnológica ({st.session_state.anio})",
                template="seaborn",
                hole=0.4
            )
            exportacionesIntensidad_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20),
                legend_title_text="Intensidad Tecnológica"
            )
            st.plotly_chart(exportacionesIntensidad_fig)
            st.markdown("")

            evolucionExportaciones_fig = px.line(
                x=["2020", "2021", "2022", "2023"],
                y=[100, 200, 300, 400],
                labels={"x": "", "y": "Millones de USD (FOB)"},
                title=f"Evolución de las exportaciones tecnológicas (2019 - {st.session_state.anio})",
                template="seaborn"
            )
            evolucionExportaciones_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(evolucionExportaciones_fig)

            exportaciones_pais_df = pd.DataFrame({
                "País": ["China", "Brasil", "Chile", "Uruguay"],
                "Exportaciones": [400, 300, 200, 100]
            })
            exportacionesxPais_fig = px.treemap(
                data_frame=exportaciones_pais_df,
                path=["País"],
                values="Exportaciones",
                template="seaborn"
            )
            exportacionesxPais_fig.update_layout(
                title=f"Exportaciones provinciales por país ({st.session_state.anio})",
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(exportacionesxPais_fig)
            st.markdown("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=f":primary[Cantidad de patentes de solicitantes argentinos]", value=120, delta=None)
            with col2:
                st.metric(label=f":primary[Cantidad de patentes de solicitantes argentinos]", value=120, delta=None)
            with col3:
                st.metric(label=f":primary[Cantidad de patentes de solicitantes argentinos]", value=120, delta=None)
            st.markdown("")

            evolucionPatentes_fig = px.line(
                x=["2020", "2021", "2022", "2023"],
                y=[100, 200, 300, 400],
                labels={"x": "", "y": "Cantidad de Patentes"},
                title=f"Evolución de las cantidad de patentes solicitadas por instituciones provinciales de CyT (2019 - {st.session_state.anio})",
                template="seaborn"
            )
            evolucionPatentes_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(evolucionPatentes_fig)
            st.markdown("")

            df = pd.DataFrame(
                np.random.randn(10, 5), columns=("col %d" % i for i in range(5))
            )
            st.table(df)
            st.markdown("")

            produccionProvincial_fig = px.line(
                x=["2020", "2021", "2022", "2023"],
                y=[100, 200, 300, 400],
                labels={"x": "", "y": "Producción científica"},
                title=f"Evolución de la producción científica provincial (2019 - {st.session_state.anio})",
                template="seaborn"
            )
            produccionProvincial_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(produccionProvincial_fig)
            st.markdown("")

            publicaciones_df = pd.DataFrame({
                "Tipo": ["Articulo", "Capitulo de libro", "Libro"],
                "Publicaciones": [400, 150, 50]
            })

            distribucionPublicaciones_fig = px.treemap(
                data_frame=publicaciones_df,
                path=["Tipo"],
                values="Publicaciones",
                template="seaborn"
            )
            distribucionPublicaciones_fig.update_layout(
                title=f"Distribución de publicaciones científicas por tipo ({st.session_state.anio})",
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(distribucionPublicaciones_fig)
            st.markdown("")

            df2 = pd.DataFrame(
                np.random.randn(10, 5), columns=("col %d" % i for i in range(5))
            )
            st.table(df2)
            st.markdown("")

            publicacionesArea_fig = px.bar(
                x=[100, 200, 300, 400, 500],
                y=["Área 1", "Área 2", "Área 3", "Área 4", "Área 5"],
                labels={"x": r"% de Publicaciones", "y": ""},
                title=f"Publicaciones científicas por área de conocimiento ({st.session_state.anio})",
                template="seaborn",
                orientation='h',
            )
            publicacionesArea_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(publicacionesArea_fig)
            st.markdown("")

        with ciencia_sociedadTab:
            st.markdown("")

            nBarras = len(provinciasDF)
            altura = 20 * nBarras + 150

            percepcionPublica_fig = px.bar(
                y=provinciasDF['nombre_iso'],
                x=[70, 60, 50, 40, 80, 70, 60, 50, 40, 80, 70, 60, 50, 40, 80, 70, 60, 50, 40, 80, 70, 60, 50, 40],
                labels={"x": "Porcentaje que considera que contribuye totalmente", "y": "Provincia"},
                title=f"Percepción pública de la contribución de la ciencia a la calidad de vida por Provincia ({st.session_state.anio})",
                template="seaborn",
                orientation='h',
                height=altura
            )
            percepcionPublica_fig.update_layout(
                title_font=dict(size=20),
                margin=dict(l=20, r=20, t=50, b=20),
                barcornerradius=15
            )
            percepcionPublica_fig.update_yaxes(automargin=True)
            percepcionPublica_fig.update_xaxes(
                range=[0, 100],
                tick0=0,
                dtick=10,
                ticksuffix=" %",
                title_standoff=10  # un poco de espacio entre ticks y etiqueta
            )
            st.plotly_chart(percepcionPublica_fig)
            st.markdown("")

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
