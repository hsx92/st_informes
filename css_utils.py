import streamlit as st


@st.cache_data
def load_css(path: str) -> str:
    """Load a CSS file and return its contents.

    The result is cached by Streamlit to avoid rereading the file on each run.

    Args:
        path: Path to the CSS file.

    Returns:
        The contents of the CSS file as a string.
    """
    try:
        with open(path, "r", encoding="utf-8") as css_file:
            return css_file.read()
    except FileNotFoundError:
        st.warning(f"No se encontró el archivo {path}. Se aplicará solo el CSS personalizado.")
        return ""


def get_metric_css(theme: str = "dark") -> str:
    """Generate CSS for metric cards based on the current theme.
    
    Args:
        theme: Color theme ('dark' or 'light')
        
    Returns:
        CSS string for metric styling
    """
    if theme == "dark":
        # Para tema oscuro: texto claro sobre fondo oscuro
        return """
        div[data-testid="stMetricValue"] > div {
            color: #354B6E !important;  /* Texto claro para mejor contraste */
            font-weight: 600;
        }
        div[data-testid="stMetricDelta"] > div {
            color: #7DD3C0 !important;  /* Verde claro para deltas positivos */
        }
        div[data-testid="stMetricLabel"] > div {
            color: #B4C6DB !important;  /* Gris azulado claro para labels */
            font-weight: 500;
        }
        """
    else:
        # Para tema claro: mantener colores originales
        return """
        div[data-testid="stMetricValue"] > div {
            color: #354B6E !important;
            font-weight: 600;
        }
        div[data-testid="stMetricDelta"] > div {
            color: #198769 !important;
        }
        div[data-testid="stMetricLabel"] > div {
            color: #54698B !important;
            font-weight: 500;
        }
        """


def get_colors() -> dict[str, str]:
    """Return a dictionary of official colors used in the application."""
    return {
        # Colores primarios del sistema
        "primario": "#232D4F",           # Azul oficial
        "secundario": "#354B6E",         # Azul secundario
        
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

        "resaltado": "#F7D80E",         # Amarillo dorado para destacar
    }
