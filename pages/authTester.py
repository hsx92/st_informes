import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards


def example():
    # Define the custom CSS for Streamlit metric component
    custom_streamlit_css = """
    div[data-testid="stMetricValue"] > div {
        color: #354B6E;
    }
    div[data-testid="stMetricDelta"] > div {
        color: #FFFFFF;
    }
    """

    # Read the icono-arg.css file
    with open("static/iconos/dist/css/icono-arg.css", "r") as css_file:
        icono_arg_css = css_file.read()

    # Combine the icono-arg.css with the custom Streamlit CSS
    combined_css = f"""
    <style>
    {icono_arg_css}
    {custom_streamlit_css}
    </style>
    """

    # Inject the combined CSS into the Streamlit app
    st.markdown(combined_css, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric(label=":primary[Densidad Poblacional]", value="5000"+" hab/km²", delta=None)
    col2.metric(label="Loss", value=5000, delta=None)
    col3.metric(label="No Change", value=5000, delta=None)

    style_metric_cards()


example()
