import plotly.express as px
import plotly.graph_objects as go
from data_handler import get_informe
from utils import procesar_kpi, insertar_saltos, tabla_pivot


def preparar_data_pdf(data: dict):
    for nombre, componente in data["componentes"].items():
        if nombre.startswith("kpi"):
            continue
        elif nombre.startswith("tabla"):
            data["componentes"][nombre]["df"] = tabla_pivot(componente)
        elif nombre.startswith("grafico"):
            width, height = (1080, None)
            if nombre == "grafico_percepcion_calidad_vida":
                width, height = (None, 700)
            if nombre == "grafico_percepcion_temas_prioritarios":
                width, height = (1080, 600)
                data["componentes"][nombre]["img"] = componente.get("figura").to_image(
                    format="png", width=width, height=height, scale=1, validate=True
                )
                continue
            if componente.get("figura") is not None:
                # Convertir la figura a imagen
                data["componentes"][nombre]["img"] = componente.get("figura").to_image(
                    format="png", width=width, height=height, scale=2, validate=True
                )

    # Delete 'figura' and 'resultado_sql' from every 'componente'
    for nombre, componente in data["componentes"].items():
        componente.pop("figura", None)
        componente.pop("resultado_sql", None)

    print('Generación del diccionario de la ficha provincial completada.')
    return data


def ficha_provincial_figs(provincia_id: int, provincia: str, anio: int) -> dict:

    """Genera las figuras para la ficha provincial."""

    default_color = "#5A7290"
    # light_color = "#EAEAEA"
    highLight_color_1 = "#232D4F"
    highLight_color_2 = "#E1CD4A"
    color_discrete_sequence = ["#4D7AAE", "#9D584C", "#EBDBCF", "#198769", "#5C3C7D", "#F2C94C", "#C65B0E", "#9B51E0", "#56CCF2", "#F493DD", "#A93226", "#6A829A", "#AF7700", "#C0C0C0", "#16A085"]

    DFs = get_informe("ficha_provincial", {
        "provincia_id": provincia_id,
        "provincia": provincia,
        "anio": anio
    })

    # COMPONENTES #

    # KPI

    for key, k in DFs["componentes"].items():
        if k["tipo_componente"] == "KPI":
            k["valor"] = procesar_kpi(k["resultado_sql"], k["config"])

    # FIGURAS

    DFs["componentes"]["grafico_expo_top5"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_expo_top5"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

    top5_exportaciones_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_expo_top5"]['resultado_sql'],
        x=DFs["componentes"]["grafico_expo_top5"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_expo_top5"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_expo_top5"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_expo_top5"]['titulo'],
        subtitle=DFs["componentes"]["grafico_expo_top5"]['subtitulo'],
        template="seaborn",
        orientation='h',
        color=DFs["componentes"]["grafico_expo_top5"]['config']['plot_mapping']['y'],
        color_discrete_sequence=color_discrete_sequence
    )
    top5_exportaciones_fig.update_layout(DFs["componentes"]["grafico_expo_top5"]['config']['layout'])
    top5_exportaciones_fig.update_layout(showlegend=False)

    # ---

    inversionID_fig = px.line(
        data_frame=DFs["componentes"]["grafico_evolucion_regional"]['resultado_sql'],
        x=DFs["componentes"]["grafico_evolucion_regional"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_evolucion_regional"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_evolucion_regional"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_evolucion_regional"]['titulo'],
        subtitle=DFs["componentes"]["grafico_evolucion_regional"]['subtitulo'],
        markers=True,
        template="seaborn",
        color=DFs["componentes"]["grafico_evolucion_regional"]['config']['plot_mapping']['color']
    )
    inversionID_fig.update_layout(DFs["componentes"]["grafico_evolucion_regional"]['config']['layout'])

    # ---

    highLight_color = {f"{provincia}": highLight_color_1}
    color_discrete_map = {
        c: highLight_color.get(c, default_color) for c in DFs["componentes"]["grafico_inv_por_investigador"]['resultado_sql']['unidad_territorial']
    }

    inversionInvestigador_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_inv_por_investigador"]['resultado_sql'],
        y=DFs["componentes"]["grafico_inv_por_investigador"]['config']['plot_mapping']['y'],
        x=DFs["componentes"]["grafico_inv_por_investigador"]['config']['plot_mapping']['x'],
        labels=DFs["componentes"]["grafico_inv_por_investigador"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_inv_por_investigador"]['titulo'],
        subtitle=DFs["componentes"]["grafico_inv_por_investigador"]['subtitulo'],
        color=DFs["componentes"]["grafico_inv_por_investigador"]['config']['plot_mapping']['color'],
        template="seaborn",
        orientation='h',
        color_discrete_map=color_discrete_map
    )
    inversionInvestigador_fig.update_layout(DFs["componentes"]["grafico_inv_por_investigador"]['config']['layout'])
    inversionInvestigador_fig.update_traces(showlegend=False)

    # ---

    DFs["componentes"]["grafico_inv_empresaria_sector"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_inv_empresaria_sector"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

    inversionEmpresas_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_inv_empresaria_sector"]['resultado_sql'],
        y=DFs["componentes"]["grafico_inv_empresaria_sector"]['config']['plot_mapping']['y'],
        x=DFs["componentes"]["grafico_inv_empresaria_sector"]['config']['plot_mapping']['x'],
        labels=DFs["componentes"]["grafico_inv_empresaria_sector"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_inv_empresaria_sector"]['titulo'],
        subtitle=DFs["componentes"]["grafico_inv_empresaria_sector"]['subtitulo'],
        template="seaborn",
        orientation='h',
        color=DFs["componentes"]["grafico_inv_empresaria_sector"]['config']['plot_mapping']['y'],
        color_discrete_sequence=color_discrete_sequence
    )

    inversionEmpresas_fig.update_layout(DFs["componentes"]["grafico_inv_empresaria_sector"]['config']['layout'])
    inversionEmpresas_fig.update_layout(showlegend=False)

    # ---

    if DFs["componentes"]["tabla_pfi_cruce"]['resultado_sql'] is not None and not DFs["componentes"]["tabla_pfi_cruce"]['resultado_sql'].empty:
        tabla_pfi_cruce_fig = tabla_pivot(DFs["componentes"]["tabla_pfi_cruce"], render_gt=True)
    else:
        tabla_pfi_cruce_fig = None

    # ---

    DFs["componentes"]["grafico_unidades_por_inst"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_unidades_por_inst"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

    unidadesIDxinstitucion_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_unidades_por_inst"]['resultado_sql'],
        y=DFs["componentes"]["grafico_unidades_por_inst"]['config']['plot_mapping']['y'],
        x=DFs["componentes"]["grafico_unidades_por_inst"]['config']['plot_mapping']['x'],
        labels=DFs["componentes"]["grafico_unidades_por_inst"]['config']['plot_mapping']['labels'],
        title=" ",
        template="seaborn",
        orientation='h',
        color=DFs["componentes"]["grafico_unidades_por_inst"]['config']['plot_mapping']['y'],
        color_discrete_sequence=color_discrete_sequence
    )
    unidadesIDxinstitucion_fig.update_layout(DFs["componentes"]["grafico_unidades_por_inst"]['config']['layout'])
    unidadesIDxinstitucion_fig.update_layout(margin=dict(l=0, r=20, t=0, b=20), showlegend=False)

    # ---

    equiposIDxTipo_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_equipos_por_tipo"]['resultado_sql'],
        y=DFs["componentes"]["grafico_equipos_por_tipo"]['config']['plot_mapping']['y'],
        x=DFs["componentes"]["grafico_equipos_por_tipo"]['config']['plot_mapping']['x'],
        labels=DFs["componentes"]["grafico_equipos_por_tipo"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_equipos_por_tipo"]['titulo'],
        subtitle=DFs["componentes"]["grafico_equipos_por_tipo"]['subtitulo'],
        color=DFs["componentes"]["grafico_equipos_por_tipo"]['config']['plot_mapping']['y'],
        template="seaborn",
        orientation='h'
    )
    equiposIDxTipo_fig.update_layout(DFs["componentes"]["grafico_equipos_por_tipo"]['config']['layout'])
    equiposIDxTipo_fig.update_layout(showlegend=False)

    # ---

    investigadoresxArea_fig = px.treemap(
        title=DFs["componentes"]["grafico_distribucion_investigadores"]['titulo'],
        subtitle=DFs["componentes"]["grafico_distribucion_investigadores"]['subtitulo'],
        data_frame=DFs["componentes"]["grafico_distribucion_investigadores"]['resultado_sql'],
        path=DFs["componentes"]["grafico_distribucion_investigadores"]['config']['plot_mapping']['path'],
        values=DFs["componentes"]["grafico_distribucion_investigadores"]['config']['plot_mapping']['values'],
        labels=DFs["componentes"]["grafico_distribucion_investigadores"]['config']['plot_mapping']['labels'],
        color=DFs["componentes"]["grafico_distribucion_investigadores"]['config']['plot_mapping']['color'],
        color_discrete_sequence=color_discrete_sequence,
    )
    investigadoresxArea_fig.update_traces(DFs["componentes"]["grafico_distribucion_investigadores"]['config']['traces'])
    investigadoresxArea_fig.update_traces(marker=dict(cornerradius=5))

    investigadoresxArea_fig.update_layout(DFs["componentes"]["grafico_distribucion_investigadores"]['config']['layout'])
    investigadoresxArea_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    # ---

    if DFs["componentes"]["tabla_personas_por_funcion"]['resultado_sql'] is not None and not DFs["componentes"]["tabla_personas_por_funcion"]['resultado_sql'].empty:
        tabla_personas_por_funcion_fig = tabla_pivot(DFs["componentes"]["tabla_personas_por_funcion"], render_gt=True)
    else:
        tabla_personas_por_funcion_fig = None

    # ---

    evolucionInvestigadores_fig = px.line(
        data_frame=DFs["componentes"]["grafico_evolucion_investigadores"]['resultado_sql'],
        x=DFs["componentes"]["grafico_evolucion_investigadores"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_evolucion_investigadores"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_evolucion_investigadores"]['config']['plot_mapping']['labels'],
        color=DFs["componentes"]["grafico_evolucion_investigadores"]['config']['plot_mapping']['color'],
        title=DFs["componentes"]["grafico_evolucion_investigadores"]['titulo'],
        subtitle=DFs["componentes"]["grafico_evolucion_investigadores"]['subtitulo'],
        markers=True,
        template="seaborn"
    )
    evolucionInvestigadores_fig.update_layout(DFs["componentes"]["grafico_evolucion_investigadores"]['config']['layout'])
    evolucionInvestigadores_fig.update_layout(margin=dict(l=20, r=20, t=90, b=20))

    # ---

    exportacionesIntensidad_fig = px.pie(
        data_frame=DFs["componentes"]["grafico_expo_intensidad"]['resultado_sql'],
        names=DFs["componentes"]["grafico_expo_intensidad"]['config']['plot_mapping']['names'],
        values=DFs["componentes"]["grafico_expo_intensidad"]['config']['plot_mapping']['values'],
        labels=DFs["componentes"]["grafico_expo_intensidad"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_expo_intensidad"]['titulo'],
        subtitle=DFs["componentes"]["grafico_expo_intensidad"]['subtitulo'],
        hole=DFs["componentes"]["grafico_expo_intensidad"]['config']['plot_mapping']['hole'],
        template="seaborn",
    )
    exportacionesIntensidad_fig.update_layout(DFs["componentes"]["grafico_expo_intensidad"]['config']['layout'])
    exportacionesIntensidad_fig.update_traces(DFs["componentes"]["grafico_expo_intensidad"]['config']['traces'])
    exportacionesIntensidad_fig.update_layout(margin=dict(l=20, r=20, t=90, b=20))

    # ---

    evolucionExportaciones_fig = px.line(
        data_frame=DFs["componentes"]["grafico_expo_evolucion"]['resultado_sql'],
        x=DFs["componentes"]["grafico_expo_evolucion"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_expo_evolucion"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_expo_evolucion"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_expo_evolucion"]['titulo'],
        subtitle=DFs["componentes"]["grafico_expo_evolucion"]['subtitulo'],
        color=DFs["componentes"]["grafico_expo_evolucion"]['config']['plot_mapping']['color'],
        markers=True,
        template="seaborn"
    )
    evolucionExportaciones_fig.update_layout(DFs["componentes"]["grafico_expo_evolucion"]['config']['layout'])
    evolucionExportaciones_fig.update_layout(margin=dict(l=20, r=20, t=90, b=20))

    # ---

    # DFs["componentes"]["grafico_expo_destino"]['resultado_sql']['porcentaje'] = DFs["componentes"]["grafico_expo_destino"]['resultado_sql']['porcentaje'].apply(lambda x: f'{x:.2f} %')
    exportacionesxPais_fig = px.treemap(
        data_frame=DFs["componentes"]["grafico_expo_destino"]['resultado_sql'].head(15),
        path=DFs["componentes"]["grafico_expo_destino"]['config']['plot_mapping']['path'],
        values=DFs["componentes"]["grafico_expo_destino"]['config']['plot_mapping']['values'],
        color=DFs["componentes"]["grafico_expo_destino"]['config']['plot_mapping']['color'],
        title=DFs["componentes"]["grafico_expo_destino"]['titulo'],
        subtitle=DFs["componentes"]["grafico_expo_destino"]['subtitulo'],
        template="seaborn",
        color_discrete_sequence=color_discrete_sequence
    )
    exportacionesxPais_fig.update_traces(DFs["componentes"]["grafico_expo_destino"]['config']['traces'])
    exportacionesxPais_fig.update_layout(DFs["componentes"]["grafico_expo_destino"]['config']['layout'])
    exportacionesxPais_fig.update_layout(margin=dict(l=20, r=20, t=50, b=0))

    # ---

    if DFs["componentes"]["grafico_patentes_evolucion"]['resultado_sql'] is not None and not DFs["componentes"]["grafico_patentes_evolucion"]['resultado_sql'].empty:
        evolucionPatentes_fig = px.line(
            data_frame=DFs["componentes"]["grafico_patentes_evolucion"]['resultado_sql'],
            x=DFs["componentes"]["grafico_patentes_evolucion"]['config']['plot_mapping']['x'],
            y=DFs["componentes"]["grafico_patentes_evolucion"]['config']['plot_mapping']['y'],
            labels=DFs["componentes"]["grafico_patentes_evolucion"]['config']['plot_mapping']['labels'],
            title=DFs["componentes"]["grafico_patentes_evolucion"]['titulo'],
            subtitle=DFs["componentes"]["grafico_patentes_evolucion"]['subtitulo'],
            markers=True,
            template="seaborn"
        )
        evolucionPatentes_fig.update_layout(DFs["componentes"]["grafico_patentes_evolucion"]['config']['layout'])
        evolucionPatentes_fig.update_layout(margin=dict(l=20, r=20, t=90, b=20))
    else:
        evolucionPatentes_fig = None

    # ---

    if DFs["componentes"]["tabla_patentes_sector"]['resultado_sql'] is not None and not DFs["componentes"]["tabla_patentes_sector"]['resultado_sql'].empty:
        tabla_patentes_sector_fig = tabla_pivot(DFs["componentes"]["tabla_patentes_sector"], render_gt=True)
    else:
        tabla_patentes_sector_fig = None

    # ---

    produccionProvincial_fig = px.line(
        data_frame=DFs["componentes"]["grafico_produccion_evolucion"]['resultado_sql'],
        x=DFs["componentes"]["grafico_produccion_evolucion"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_produccion_evolucion"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_produccion_evolucion"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_produccion_evolucion"]['titulo'],
        subtitle=DFs["componentes"]["grafico_produccion_evolucion"]['subtitulo'],
        color=DFs["componentes"]["grafico_produccion_evolucion"]['config']['plot_mapping']['color'],
        markers=True,
        template="seaborn"
    )
    produccionProvincial_fig.update_layout(DFs["componentes"]["grafico_produccion_evolucion"]['config']['layout'])
    produccionProvincial_fig.update_layout(margin=dict(l=20, r=20, t=90, b=20))

    # ---

    distribucionPublicaciones_fig = px.treemap(
        data_frame=DFs["componentes"]["grafico_produccion_tipo"]['resultado_sql'],
        path=DFs["componentes"]["grafico_produccion_tipo"]['config']['plot_mapping']['path'],
        values=DFs["componentes"]["grafico_produccion_tipo"]['config']['plot_mapping']['values'],
        labels=DFs["componentes"]["grafico_produccion_tipo"]['config']['plot_mapping']['labels'],
        color=DFs["componentes"]["grafico_produccion_tipo"]['config']['plot_mapping']['color'],
        title=DFs["componentes"]["grafico_produccion_tipo"]['titulo'],
        subtitle=DFs["componentes"]["grafico_produccion_tipo"]['subtitulo'],
        template="seaborn"
    )
    distribucionPublicaciones_fig.update_traces(DFs["componentes"]["grafico_produccion_tipo"]['config']['traces'])
    distribucionPublicaciones_fig.update_traces(
        marker=dict(cornerradius=5),
    )
    distribucionPublicaciones_fig.update_layout(DFs["componentes"]["grafico_produccion_tipo"]['config']['layout'])
    distribucionPublicaciones_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    # ---

    DFs["componentes"]["grafico_publicaciones_area"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_publicaciones_area"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

    publicacionesArea_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_publicaciones_area"]['resultado_sql'],
        x=DFs["componentes"]["grafico_publicaciones_area"]['config']['plot_mapping']['x'],
        y=DFs["componentes"]["grafico_publicaciones_area"]['config']['plot_mapping']['y'],
        labels=DFs["componentes"]["grafico_publicaciones_area"]['config']['plot_mapping']['labels'],
        title=DFs["componentes"]["grafico_publicaciones_area"]['titulo'],
        subtitle=DFs["componentes"]["grafico_publicaciones_area"]['subtitulo'],
        color=DFs["componentes"]["grafico_publicaciones_area"]['config']['plot_mapping']['color'],
        color_discrete_sequence=color_discrete_sequence,
        orientation='h',
    )
    publicacionesArea_fig.update_traces(showlegend=False)
    publicacionesArea_fig.update_layout(DFs["componentes"]["grafico_publicaciones_area"]['config']['layout'])

    # ---

    if DFs["componentes"]["tabla_articulos_q1_q2"]["resultado_sql"] is not None and not DFs["componentes"]["tabla_articulos_q1_q2"]["resultado_sql"].empty:
        tabla_articulos_q1_q2_fig = tabla_pivot(DFs["componentes"]["tabla_articulos_q1_q2"], render_gt=True)
    else:
        tabla_articulos_q1_q2_fig = None

    # ---

    nBarras = 24
    altura = 20 * nBarras + 300

    DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['resultado_sql'].iloc[:, 1] = DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['resultado_sql'].iloc[:, 1].apply(insertar_saltos, width=20)
    percepcion_df = DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['resultado_sql'].copy()
    percepcion_df['valor'] = percepcion_df['valor'].round(2)
    percepcion_df = percepcion_df.sort_values(by='variable')

    medianas = percepcion_df.groupby('variable')['valor'].median().reset_index()
    medianas = medianas.sort_values(by='variable').reset_index(drop=True)

    highlight_percepcion_df = percepcion_df[percepcion_df['unidad_territorial'] == provincia]
    other_provinces_df = percepcion_df[percepcion_df['unidad_territorial'] != provincia]

    # Empezamos con una figura vacía
    percepcionTemasPrioritarios_fig = go.Figure()

    # Añadimos la traza para el resto de las provincias
    percepcionTemasPrioritarios_fig.add_trace(go.Scatter(
        x=other_provinces_df['variable'],
        y=other_provinces_df['valor'],
        mode='markers',
        marker=dict(color=default_color, size=10),
        name='Otras Provincias',
        showlegend=False,
        hovertext=other_provinces_df['unidad_territorial'],
        hovertemplate='<b>%{hovertext}</b><br>%{y}' + DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['config']['layout']['yaxis']['ticksuffix'] + '<extra></extra>'
    ))

    # Añadimos la traza para la provincia resaltada
    percepcionTemasPrioritarios_fig.add_trace(go.Scatter(
        x=highlight_percepcion_df['variable'],
        y=highlight_percepcion_df['valor'],
        mode='markers',
        marker=dict(color=highLight_color_2, size=12, symbol='circle'),
        name=provincia,
        hovertext=highlight_percepcion_df['unidad_territorial'],
        hovertemplate='<b>%{hovertext}</b><br>%{y}' + DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['config']['layout']['yaxis']['ticksuffix'] + '<extra></extra>'
    ))

    all_shapes = []
    num_categories = len(medianas)
    y_max = percepcion_df['valor'].max() * 1.1

    # Añadimos los separadores verticales
    for i in range(num_categories + 1):
        all_shapes.append(dict(
            type='line',
            x0=-0.5 if i < 1 else i - 0.5,
            x1=-0.5 if i < 1 else i - 0.5,
            y0=0,
            y1=y_max,
            line=dict(color=default_color, width=1, dash='solid')
        ))

    # Añadimos las líneas de la mediana
    for i, row in medianas.iterrows():
        all_shapes.append(dict(
            type='line', x0=i - 0.5, x1=i + 0.5, y0=row['valor'], y1=row['valor'],
            line=dict(color=highLight_color_2, width=3, dash='dash')
        ))

    percepcionTemasPrioritarios_fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color=highLight_color_2, width=3, dash='dash'),
        name='Mediana'
    ))

    main_title = DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['titulo']
    subtitle = DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['subtitulo']

    full_title = f"{main_title}<br><span style='font-size: 16px; font-weight: normal;'>{subtitle}</span>"

    percepcionTemasPrioritarios_fig.update_layout(
        title=full_title,
        height=altura,
        margin=dict(l=20, r=40, t=175, b=150),
        legend_title_text="",
        shapes=all_shapes
    )
    percepcionTemasPrioritarios_fig.update_layout(
        DFs["componentes"]["grafico_percepcion_temas_prioritarios"]['config']['layout']
    )

    # Save test chart image
    # percepcionTemasPrioritarios_fig.write_image("output/test_percepcion_temas_prioritarios.png", width=1500, scale=2)

    # ---

    highLight_color = {f"{provincia}": highLight_color_1}
    color_discrete_map = {
        c: highLight_color.get(c, default_color) for c in DFs["componentes"]["grafico_percepcion_calidad_vida"]['resultado_sql']['unidad_territorial']
    }

    percepcionPublica_fig = px.bar(
        data_frame=DFs["componentes"]["grafico_percepcion_calidad_vida"]['resultado_sql'],
        y=DFs["componentes"]["grafico_percepcion_calidad_vida"]['config']['plot_mapping']['y'],
        x=DFs["componentes"]["grafico_percepcion_calidad_vida"]['config']['plot_mapping']['x'],
        labels=DFs["componentes"]["grafico_percepcion_calidad_vida"]['config']['plot_mapping']['labels'],
        color=DFs["componentes"]["grafico_percepcion_calidad_vida"]['config']['plot_mapping']['color'],
        title=DFs["componentes"]["grafico_percepcion_calidad_vida"]['titulo'],
        subtitle=DFs["componentes"]["grafico_percepcion_calidad_vida"]['subtitulo'],
        template="seaborn",
        orientation='h',
        color_discrete_map=color_discrete_map,
        height=altura
    )
    percepcionPublica_fig.update_layout(DFs["componentes"]["grafico_percepcion_calidad_vida"]['config']['layout'])
    percepcionPublica_fig.update_layout(margin=dict(l=20, r=40, t=150, b=20))
    percepcionPublica_fig.update_traces(showlegend=False)

    # --- FIN FIGURAS --- #

    DFs["componentes"]["grafico_expo_top5"]["figura"] = top5_exportaciones_fig
    DFs["componentes"]["grafico_evolucion_regional"]["figura"] = inversionID_fig
    DFs["componentes"]["grafico_inv_por_investigador"]["figura"] = inversionInvestigador_fig
    DFs["componentes"]["grafico_inv_empresaria_sector"]["figura"] = inversionEmpresas_fig
    DFs["componentes"]["tabla_pfi_cruce"]["figura"] = tabla_pfi_cruce_fig
    DFs["componentes"]["grafico_unidades_por_inst"]["figura"] = unidadesIDxinstitucion_fig
    DFs["componentes"]["grafico_equipos_por_tipo"]["figura"] = equiposIDxTipo_fig
    DFs["componentes"]["grafico_distribucion_investigadores"]["figura"] = investigadoresxArea_fig
    DFs["componentes"]["tabla_personas_por_funcion"]["figura"] = tabla_personas_por_funcion_fig
    DFs["componentes"]["grafico_evolucion_investigadores"]["figura"] = evolucionInvestigadores_fig
    DFs["componentes"]["grafico_expo_intensidad"]["figura"] = exportacionesIntensidad_fig
    DFs["componentes"]["grafico_expo_evolucion"]["figura"] = evolucionExportaciones_fig
    DFs["componentes"]["grafico_expo_destino"]["figura"] = exportacionesxPais_fig
    DFs["componentes"]["grafico_patentes_evolucion"]["figura"] = evolucionPatentes_fig
    DFs["componentes"]["tabla_patentes_sector"]["figura"] = tabla_patentes_sector_fig
    DFs["componentes"]["grafico_produccion_evolucion"]["figura"] = produccionProvincial_fig
    DFs["componentes"]["grafico_produccion_tipo"]["figura"] = distribucionPublicaciones_fig
    DFs["componentes"]["grafico_publicaciones_area"]["figura"] = publicacionesArea_fig
    DFs["componentes"]["tabla_articulos_q1_q2"]["figura"] = tabla_articulos_q1_q2_fig
    DFs["componentes"]["grafico_percepcion_temas_prioritarios"]["figura"] = percepcionTemasPrioritarios_fig
    DFs["componentes"]["grafico_percepcion_calidad_vida"]["figura"] = percepcionPublica_fig

    return DFs
