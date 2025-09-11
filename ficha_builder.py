import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import textwrap
from typing import Union
from great_tables import GT, style, loc, google_font
from sources import get_informe
from fig_builders import build_line, build_bar, build_pie, build_treemap
from logging_config import get_logger, log_execution
import time

# Inicializar logger
logger = get_logger(__name__)

pio.templates.default = 'seaborn'
BASE_FONT = dict(family="Poppins", size=16)
COLOR_DISCRETE_SEQUENCE = [
    "#0695D6",  # Azul primario oficial del gobierno argentino
    "#2E7D32",  # Verde institucional (ciencia y tecnología)
    "#D32F2F",  # Rojo de alerta/importante
    "#FA8612",  # Naranja/ámbar para destacados
    "#8030B2",  # Violeta para innovación
    "#00695C",  # Verde azulado (datos ambientales)
    "#37474F",  # Gris azulado (datos neutros)
    "#5D4037",  # Marrón (datos socioeconómicos)
    "#1565C0",  # Azul más intenso (variación del primario)
    "#AD1433",  # Rosa/magenta (datos específicos)
    "#558B2F",  # Verde oliva
    "#F9A825",  # Amarillo dorado
    "#E65100",  # Naranja profundo
    "#4527A0",  # Violeta profundo
    "#00838F"   # Cian
]

# Colores adicionales para casos específicos
COLORES_PONCHO = {
    # Colores primarios del sistema
    "primario": "#232D4F",           # Azul oficial
    "secundario": "#2E7D32",         # Verde institucional
    
    # Estados y alertas
    "exito": "#2E7D32",             # Verde
    "advertencia": "#F57C00",        # Naranja
    "error": "#D32F2F",             # Rojo
    "info": "#0695D6",              # Azul primario
    
    # Grises institucionales
    "gris_oscuro": "#37474F",       # Para textos principales
    "gris_medio": "#78909C",        # Para textos secundarios
    "gris_claro": "#ECEFF1",        # Para fondos suaves
    
    # Colores específicos para ciencia y tecnología
    "innovacion": "#6A1B9A",        # Violeta
    "datos": "#1565C0",             # Azul datos
    "tecnologia": "#00695C",        # Verde azulado
    "investigacion": "#AD1457",       # Rosa/magenta

    "resaltado": "#E1CD4A",         # Amarillo dorado para destacar
}


# --- HELPERS --- #

def has_data(comp):
    df = comp.get('resultado_sql')
    return df is not None and not df.empty


def highlight_map(series, highlight, default=COLORES_PONCHO["gris_medio"], hl=COLORES_PONCHO["primario"]):
    keys = pd.unique(series.dropna())
    return {k: (hl if k == highlight else default) for k in keys}


# Devuelve la cadena con saltos de línea
def insertar_saltos(cadena: str, width: int = 35) -> str:
    if not isinstance(cadena, str):
        return cadena

    return textwrap.fill(cadena, width=width).replace('\n', '<br>')


def procesar_kpi(df: pd.DataFrame, config: dict) -> str:
    """Procesa un KPI según su configuración."""
    try:
        if df.empty or pd.isna(df.iloc[0, 0]):
            logger.debug("KPI sin datos, retornando 'N/A'")
            return "N/A"
        
        valor = df.iloc[0, 0]
        formato = config.get('format', 'raw')
        sufijo = config.get('suffix', '')
        
        if formato == 'int':
            return f"{int(float(valor)):,}{sufijo}".replace(",", ".")
        if formato == 'float':
            return f"{float(valor):,.2f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{valor}{sufijo}"
        
    except Exception as e:
        logger.error(f"Error procesando KPI: {e}")
        return "Error"


# Renderiza una tabla dinámica y la formatea con great_tables para su visualización en Streamlit
@log_execution(log_result=False)
def tabla_pivot(componente: dict, render_gt: bool = False) -> Union[pd.DataFrame, GT, None]:
    """
    Crea una tabla dinámica (pivot table) y la formatea con great_tables.

    Args:
        componente (dict): Un diccionario con los datos y la configuración.
                          Debe contener 'resultado_sql' (DataFrame) y 'config'.
        render_gt: Si renderizar como great_tables o devolver DataFrame

    Returns:
        GT: Un objeto de great_tables listo para ser visualizado.
    """
    try:
        logger.debug(f"Generando tabla pivot para componente: {componente.get('titulo', 'sin título')}")
        
        # 1. Extraer el DataFrame de los datos
        df = componente['resultado_sql']

        # 2. Crear la tabla dinámica usando la configuración del componente
        pivot_config = componente['config']['pivot']
        if 'index' in pivot_config:
            tabla = (
                df
                .pivot_table(
                    index=pivot_config['index'],
                    columns=pivot_config['columns'],
                    values=pivot_config['values'],
                    aggfunc=pivot_config['aggfunc']
                )
                .reset_index()
            )
            # Borrar el contenido del column_header de la columna índice
            tabla.columns = tabla.columns.where(tabla.columns != pivot_config['index'], '')
            col_str = tabla.columns.tolist()
            col_str = col_str[1:] if col_str else []
        else:
            tabla = df.pivot_table(
                columns=pivot_config['columns'],
                values=pivot_config['values'],
                aggfunc=pivot_config['aggfunc']
            )
            col_str = tabla.columns.tolist()

        # 3. Construcción del objeto GT con el formato deseado
        if render_gt:
            try:
                gt = (
                    GT(tabla)
                    .tab_header(title=componente['titulo'])
                    .tab_stubhead(label='')
                    .opt_table_font(
                        font=google_font(name="Poppins"),
                    )
                    # 1. Formato para el cuerpo de la primera columna (el índice)
                    .tab_style(
                        style.css("padding-top: 25px; padding-bottom: 25px;"),  # El primer valor es el padding vertical (top/bottom)
                        locations=loc.body()
                    )
                    .tab_style(style=[
                        style.css("padding-top: 15px; padding-bottom: 15px;"),
                        style.text(font=google_font(name="Poppins"), align="center")
                    ],  # El primer valor es el padding vertical (top/bottom)
                        locations=[loc.header(), loc.column_header()]
                    )
                    # 2. Formato para el encabezado de la primera columna
                    .tab_style([
                        style.fill(color="#4D7AAE"),
                        style.text(font=google_font(name="Poppins"), weight="bold", color="white", align="center"),
                    ],
                        locations=loc.body(columns='')
                    )
                    # 3. Formato para el encabezado de las otras columnas
                    .tab_style(
                        style.text(font=google_font(name="Poppins"), weight="bold", color="white", align="center"),
                        locations=loc.column_labels()
                    )
                    .tab_style(
                        style=style.text(font=google_font(name="Poppins"), align="center", color="gray", weight="lighter"),
                        locations=loc.body(columns=col_str)
                    )
                    .data_color(
                        na_color="white",
                        palette=[
                            "#FDF8E7", "#FBF5E0", "#F9F2DA", "#F7EFD4", "#F5EDCE", "#F3EAC8",
                            "#F1E7C2", "#EFE4BC", "#EFE1B6", "#ECE4B1", "#EAE2AC", "#E8DFAB",
                            "#E6DC9F", "#E4D999", "#E2D693", "#E0D38D", "#DED087", "#DCCDA1"
                        ],
                        domain=[df[pivot_config['values']].min(), df[pivot_config['values']].max()],
                    )
                    .fmt_integer(
                        columns=col_str,
                        use_seps=True,
                        sep_mark="."
                    )
                    .tab_options(
                        heading_background_color="#54698B",
                        column_labels_background_color="#54698B",  # Nuevo: Color de fondo para encabezados
                        table_border_top_color="#54698B",
                        table_border_bottom_color="#54698B",
                        row_striping_include_stub=True,
                    )
                )
                logger.debug("Tabla GT generada exitosamente")
                return gt
            except Exception as e:
                logger.error(f"Error al generar GT table: {e}")
                return None
        else:
            return tabla
            
    except Exception as e:
        logger.error(f"Error en tabla_pivot: {e}")
        return None


# --- TO IMG ---

@log_execution(log_args=False)
def preparar_data_pdf(data: dict):
    """Prepara los datos para generación de PDF."""
    logger.info("Iniciando preparación de datos para PDF")
    start_time = time.time()
    
    try:
        for nombre, componente in data["componentes"].items():
            if nombre.startswith("kpi"):
                continue
            elif nombre.startswith("tabla"):
                logger.debug(f"Procesando tabla: {nombre}")
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
                    logger.debug(f"Convirtiendo gráfico a imagen: {nombre}")
                    # Convertir la figura a imagen
                    data["componentes"][nombre]["img"] = componente.get("figura").to_image(
                        format="png", width=width, height=height, scale=2, validate=True
                    )

        # Delete 'figura' and 'resultado_sql' from every 'componente'
        for nombre, componente in data["componentes"].items():
            componente.pop("figura", None)
            componente.pop("resultado_sql", None)

        elapsed_time = time.time() - start_time
        logger.info(f'Generación del diccionario de la ficha provincial completada en {elapsed_time:.2f}s')
        return data
        
    except Exception as e:
        logger.error(f"Error en preparar_data_pdf: {e}")
        raise


# --- FICHA PROVINCIAL --- #

@log_execution(log_args=True, log_result=False)
def ficha_provincial_figs(provincia_id: int, provincia: str, anio: int) -> dict:
    """Genera las figuras para la ficha provincial."""
    
    logger.info(f"Generando figuras para provincia: {provincia} (ID: {provincia_id}, Año: {anio})")
    start_time = time.time()
    
    try:
        # Obtener datos del informe
        DFs = get_informe("ficha_provincial", {
            "provincia_id": provincia_id,
            "provincia": provincia,
            "anio": anio
        })
        
        logger.debug(f"Datos obtenidos, procesando {len(DFs.get('componentes', {}))} componentes")

        # COMPONENTES #

        # KPI
        kpi_count = 0
        for key, k in DFs["componentes"].items():
            if k["tipo_componente"] == "KPI":
                k["valor"] = procesar_kpi(k["resultado_sql"], k["config"])
                kpi_count += 1
        
        logger.debug(f"Procesados {kpi_count} KPIs")

        # FIGURAS
        logger.debug("Generando figuras...")
        
        # Proceso de generación de figuras (código existente)
        try:
            DFs["componentes"]["grafico_expo_top5"]['resultado_sql'].iloc[:, 1] = DFs["componentes"]["grafico_expo_top5"]['resultado_sql'].iloc[:, 1].apply(insertar_saltos)
        except IndexError as e:
            logger.warning(f"Error al insertar saltos en 'grafico_expo_top5': {e}")

        top5_exportaciones_fig = build_bar(
            comp=DFs["componentes"]["grafico_expo_top5"],
            orientation='h',
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            showlegend=False
        )

        # ---

        inversionID_fig = build_line(
            comp=DFs["componentes"]["grafico_evolucion_regional"],
            markers=True,)

        # ---

        inversionInvestigador_fig = build_bar(
            comp=DFs["componentes"]["grafico_inv_por_investigador"],
            orientation='h',
            color_discrete_map=highlight_map(DFs["componentes"]["grafico_inv_por_investigador"]['resultado_sql']['unidad_territorial'], provincia),
            showlegend=False
        )

        # ---

        DFs["componentes"]["grafico_inv_empresaria_sector"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_inv_empresaria_sector"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

        inversionEmpresas_fig = build_bar(
            comp=DFs["componentes"]["grafico_inv_empresaria_sector"],
            orientation='h',
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            showlegend=False
        )

        # ---

        if has_data(DFs["componentes"]["tabla_pfi_cruce"]):
            tabla_pfi_cruce_fig = tabla_pivot(DFs["componentes"]["tabla_pfi_cruce"], render_gt=True)
        else:
            tabla_pfi_cruce_fig = None

        # ---

        unidadesIDxinstitucion_fig = build_bar(
            comp=DFs["componentes"]["grafico_unidades_por_inst"],
            orientation='h',
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            showlegend=False,
            dynamic_height=True
        )

        # ---

        equiposIDxTipo_fig = build_bar(
            comp=DFs["componentes"]["grafico_equipos_por_tipo"],
            orientation='h',
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            showlegend=False
        )

        # ---

        investigadoresxArea_fig = build_treemap(
            comp=DFs["componentes"]["grafico_distribucion_investigadores"],
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        # ---

        if has_data(DFs["componentes"]["tabla_personas_por_funcion"]):
            tabla_personas_por_funcion_fig = tabla_pivot(DFs["componentes"]["tabla_personas_por_funcion"], render_gt=True)
        else:
            tabla_personas_por_funcion_fig = None

        # ---

        evolucionInvestigadores_fig = build_line(
            comp=DFs["componentes"]["grafico_evolucion_investigadores"],
            margin=dict(l=20, r=20, t=90, b=20)
        )

        # ---

        exportacionesIntensidad_fig = build_pie(
            comp=DFs["componentes"]["grafico_expo_intensidad"],
            margin=dict(l=20, r=20, t=90, b=20)
        )

        # ---

        evolucionExportaciones_fig = build_line(
            comp=DFs["componentes"]["grafico_expo_evolucion"],
            margin=dict(l=20, r=20, t=90, b=20)
        )

        # ---

        DFs["componentes"]["grafico_expo_destino"]['resultado_sql'] = DFs["componentes"]["grafico_expo_destino"]['resultado_sql'].head(15)

        exportacionesxPais_fig = build_treemap(
            comp=DFs["componentes"]["grafico_expo_destino"],
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            margin=dict(l=20, r=20, t=50, b=0)
        )

        # ---

        if has_data(DFs["componentes"]["grafico_patentes_evolucion"]):

            evolucionPatentes_fig = build_line(
                comp=DFs["componentes"]["grafico_patentes_evolucion"],
                margin=dict(l=20, r=20, t=90, b=20)
            )
        else:
            evolucionPatentes_fig = None

        # ---

        if has_data(DFs["componentes"]["tabla_patentes_sector"]):
            tabla_patentes_sector_fig = tabla_pivot(DFs["componentes"]["tabla_patentes_sector"], render_gt=True)
        else:
            tabla_patentes_sector_fig = None

        # ---

        produccionProvincial_fig = build_line(
            comp=DFs["componentes"]["grafico_produccion_evolucion"],
            margin=dict(l=20, r=20, t=90, b=20)
        )

        # ---

        distribucionPublicaciones_fig = build_treemap(
            comp=DFs["componentes"]["grafico_produccion_tipo"],
            margin=dict(l=20, r=20, t=50, b=20),
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE
        )

        # --- HDP

        DFs["componentes"]["grafico_publicaciones_area"]['resultado_sql'].iloc[:, 0] = DFs["componentes"]["grafico_publicaciones_area"]['resultado_sql'].iloc[:, 0].apply(insertar_saltos)

        publicacionesArea_fig = build_bar(
            comp=DFs["componentes"]["grafico_publicaciones_area"],
            orientation='h',
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE,
            showlegend=False,
        )

        # ---

        if has_data(DFs["componentes"]["tabla_articulos_q1_q2"]):
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
            marker=dict(color=COLORES_PONCHO["gris_medio"], size=10),
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
            marker=dict(color=COLORES_PONCHO["resaltado"], size=12, symbol='circle'),
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
                line=dict(color=COLORES_PONCHO["gris_medio"], width=1, dash='solid')
            ))

        # Añadimos las líneas de la mediana
        for i, row in medianas.iterrows():
            all_shapes.append(dict(
                type='line', x0=i - 0.5, x1=i + 0.5, y0=row['valor'], y1=row['valor'],
                line=dict(color=COLORES_PONCHO["resaltado"], width=3, dash='dash')
            ))

        percepcionTemasPrioritarios_fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='lines',
            line=dict(color=COLORES_PONCHO["resaltado"], width=3, dash='dash'),
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

        # ---

        percepcionPublica_fig = build_bar(
            comp=DFs["componentes"]["grafico_percepcion_calidad_vida"],
            color_discrete_map=highlight_map(DFs["componentes"]["grafico_percepcion_calidad_vida"]['resultado_sql']['unidad_territorial'], provincia),
            dynamic_height=True,
            showlegend=False,
            margin=dict(l=20, r=40, t=150, b=20)
        )

        # --- FIN FIGURAS --- #
        
        logger.debug("Asignando figuras a componentes...")

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

        elapsed_time = time.time() - start_time
        logger.info(f"Figuras generadas exitosamente para {provincia} en {elapsed_time:.2f}s")
        
        return DFs
        
    except Exception as e:
        logger.critical(f"Error inesperado al generar las figuras de la ficha provincial para {provincia}: {e}", exc_info=True)
        return {}
