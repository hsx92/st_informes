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
        st.warning("No se encontró el archivo icono-arg.css. Se aplicará solo el CSS personalizado.")
        return ""
