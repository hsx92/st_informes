import plotly.express as px
from typing import Any, Mapping, Optional


# --- HELPERS --- #

def height_for_bars(n: int, per_bar: int = 22, base: int = 260,
                    min_h: int = 420, max_h: int = 3000) -> int:
    """Altura sugerida según cantidad de categorías (barras) para gráficos horizontales."""
    return max(min(base + n * per_bar, max_h), min_h)


def apply_config(fig, comp: Mapping[str, Any]):
    # Layout
    layout = comp.get("config", {}).get("layout")
    if layout:
        fig.update_layout(layout)
    # Traces (opcional)
    traces_cfg = comp.get("config", {}).get("traces")
    if traces_cfg:
        fig.update_traces(traces_cfg)
    return fig


# --- BUILDERS --- #

def build_line(
    comp: Mapping[str, Any],
    *,
    markers: bool = True,
    template: str = "seaborn",
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
    hovertemplate: Optional[str] = None,
    margin: Optional[dict] = None,
):
    df = comp["resultado_sql"]
    pm = comp["config"]["plot_mapping"]
    fig = px.line(
        data_frame=df,
        x=pm["x"],
        y=pm["y"],
        labels=pm.get("labels"),
        color=pm.get("color"),
        title=comp["titulo"],
        subtitle=comp.get("subtitulo"),
        markers=markers,
        template=template,
        color_discrete_sequence=color_discrete_sequence,
        color_discrete_map=color_discrete_map,
    )
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    if margin:
        fig.update_layout(margin=margin)
    return apply_config(fig, comp)


def build_pie(
    comp: Mapping[str, Any],
    *,
    template: str = "seaborn",
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
    hole: Optional[float] = None,
    showlegend: Optional[bool] = None,
    hovertemplate: Optional[str] = None,
    margin: Optional[dict] = None,
):
    df = comp["resultado_sql"]
    pm = comp["config"]["plot_mapping"]
    hole = hole if hole is not None else pm.get("hole", 0)
    fig = px.pie(
        data_frame=df,
        names=pm["names"],
        values=pm["values"],
        labels=pm.get("labels"),
        title=comp["titulo"],
        subtitle=comp.get("subtitulo"),
        hole=hole,
        template=template,
        color=pm.get("color"),  # opcional si mapeás colores por categoría
        color_discrete_sequence=color_discrete_sequence,
        color_discrete_map=color_discrete_map,
    )
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    if margin:
        fig.update_layout(margin=margin)
    return apply_config(fig, comp)


def build_bar(
    comp: Mapping[str, Any],
    *,
    template: str = "seaborn",
    orientation: str = "h",
    height: Optional[int] = None,
    dynamic_height: bool = False,
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
    hovertemplate: Optional[str] = None,
    showlegend: Optional[bool] = None,
    margin: Optional[dict] = None,
):
    df = comp["resultado_sql"]
    pm = comp["config"]["plot_mapping"]
    fig = px.bar(
        data_frame=df,
        x=pm["x"],
        y=pm["y"],
        labels=pm.get("labels"),
        title=comp["titulo"],
        subtitle=comp.get("subtitulo"),
        color=pm.get("color"),
        template=template,
        orientation=orientation,
        color_discrete_sequence=color_discrete_sequence,
        color_discrete_map=color_discrete_map,
    )
    if height is None and dynamic_height:
        n_cats = df[pm["y"]].nunique(dropna=True)
        height = height_for_bars(n_cats)
        fig.update_layout(height=height)
    if height is not None:
        fig.update_layout(height=height)
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    if orientation == 'h':
        if df[pm["x"]].dtype == "int64" or df[pm["x"]].dtype == "float64":
            max_x = df[pm["x"]].max()
            if max_x < 10:
                fig.update_xaxes(dtick=1)
    elif orientation == 'v':
        if df[pm["y"]].dtype == "int64" or df[pm["y"]].dtype == "float64":
            max_y = df[pm["y"]].max()
            if max_y < 10:
                fig.update_yaxes(dtick=1)
    if margin:
        fig.update_layout(margin=margin)

    return apply_config(fig, comp)


def build_treemap(
    comp: Mapping[str, Any],
    *,
    template: str = "seaborn",
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
    corner_radius: int = 5,
    hovertemplate: Optional[str] = None,
    margin: Optional[dict] = None,
):
    df = comp["resultado_sql"]
    pm = comp["config"]["plot_mapping"]
    fig = px.treemap(
        data_frame=df,
        path=pm["path"],
        values=pm["values"],
        labels=pm.get("labels"),
        color=pm.get("color"),
        title=comp["titulo"],
        subtitle=comp.get("subtitulo"),
        template=template,
        color_discrete_sequence=color_discrete_sequence,
        color_discrete_map=color_discrete_map,
    )
    if corner_radius > 0:
        fig.update_traces(marker=dict(cornerradius=corner_radius))
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    if margin:
        fig.update_layout(margin=margin)
    return apply_config(fig, comp)
