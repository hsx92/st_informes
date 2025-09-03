import os
import pandas as pd
import textwrap
import logging
from logging.handlers import RotatingFileHandler
from typing import Union
from jinja2 import Template
from great_tables import GT, style, loc, google_font

log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)

handler = RotatingFileHandler(
    "InformesApp-dh.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(handler)
logger = logging.getLogger(__name__)


def _render_str(value: str, params: dict) -> str:
    try:
        return Template(value).render(params)
    except Exception:
        return value


def render_obj(obj, params):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            rendered_key = _render_str(k, params) if isinstance(k, str) else k
            new_dict[rendered_key] = render_obj(v, params)
        return new_dict
    if isinstance(obj, list):
        return [render_obj(i, params) for i in obj]
    if isinstance(obj, str):
        return _render_str(obj, params)
    return obj


# Devuelve la cadena con saltos de línea y en case 'word caps'
def insertar_saltos(cadena: str, width: int = 35) -> str:
    if not isinstance(cadena, str):
        return cadena

    return textwrap.fill(cadena.title(), width=width).replace('\n', '<br>')


def procesar_kpi(df: pd.DataFrame, config: dict) -> str:
    if df.empty or pd.isna(df.iloc[0, 0]):
        return "N/A"
    valor = df.iloc[0, 0]
    formato = config.get('format', 'raw')
    sufijo = config.get('suffix', '')
    if formato == 'int':
        return f"{int(float(valor)):,}{sufijo}".replace(",", ".")
    if formato == 'float':
        return f"{float(valor):,.2f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{valor}{sufijo}"


def tabla_pivot(componente: dict, render_gt: bool = False) -> Union[pd.DataFrame, GT, None]:
    """
    Crea una tabla dinámica (pivot table) y la formatea con great_tables.

    Args:
        componente (dict): Un diccionario con los datos y la configuración.
                          Debe contener 'resultado_sql' (DataFrame) y 'config'.

    Returns:
        GT: Un objeto de great_tables listo para ser visualizado.
    """
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
            return gt
        except Exception as e:
            logger.info(f"Error al crear la tabla: {e}")
            return None
    else:
        return tabla
