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
    markers_text: bool = False,
    template: str = "plotly_white",
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
    hovertemplate: Optional[str] = None,
    hide_legend: Optional[bool] = False,
    margin: Optional[dict] = None,
    final_marker_text: bool = False,
):
    df = comp["resultado_sql"]
    pm = comp["config"]["plot_mapping"]
    fig = px.line(
        data_frame=df,
        x=pm["x"],
        y=pm["y"],
        labels=pm.get("labels"),
        color=pm.get("color"),
        text=pm["y"] if markers_text else None,
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
    if hide_legend:
        fig.update_layout(showlegend=False)
    if final_marker_text:
        apply_config(fig, comp)
        # Agregar texto al final de cada línea
        for trace in fig.data:
            scatter_fig = px.scatter(
                x=[trace.x[-1]],
                y=[trace.y[-1]],
                size=[0],
                text=[f"{trace.name}<br>{trace.y[-1]:,.0f} M"],
            )
            scatter_trace = scatter_fig.data[0]
            scatter_trace.update(
                textposition="top center",
                textfont=dict(size=18),
                showlegend=False,
                cliponaxis=False,
                marker=dict(color=trace.line.color, size=15),
                hovertemplate=f"<b>{trace.name}</b><br>{trace.x[-1]}<br>{pm['labels'][pm['y']]}: {trace.y[-1]:,.0f}<extra></extra>",
            )
            fig.add_trace(scatter_trace)
        return fig
    return apply_config(fig, comp)


def build_pie(
    comp: Mapping[str, Any],
    *,
    template: str = "plotly_white",
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
    template: str = "plotly_white",
    orientation: str = "h",
    height: Optional[int] = None,
    dynamic_height: bool = False,
    color_discrete_sequence: Optional[list[str]] = None,
    color_discrete_map: Optional[dict[str, str]] = None,
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
    template: str = "plotly_white",
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
