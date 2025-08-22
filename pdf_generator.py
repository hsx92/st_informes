from data_handler import procesar_kpi
from fpdf import FPDF, XPos, YPos, enums
from fpdf.fonts import FontFace
from PIL import Image


HEADER = "static/logo/letterhead.png"
HEIGHT = 297  # A4 height in mm
WIDTH = 210  # A4 width in mm
FUENTES = "#FFFFFF"
FUENTES_COLOR_CLARO = "#666666"
COLOR_BASE = "#2C3C5F"
COLOR_CLARO = "#7589A3"

IMAGE_DIMS_CACHE = {}


def precache_images(paths):
    """Store image dimensions to avoid repeated calculations."""
    for path in set(filter(None, paths)):
        if path not in IMAGE_DIMS_CACHE:
            try:
                with Image.open(path) as img:
                    IMAGE_DIMS_CACHE[path] = img.size
            except Exception:
                continue


class PDF(FPDF):
    def __init__(self, provincia=None):
        super().__init__()
        self.provincia = provincia
        # Reference global cache to reuse precalculated dimensions
        self.image_dims = IMAGE_DIMS_CACHE

    def footer(self):
        # Set position of the footer
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(FUENTES_COLOR_CLARO)
        # Page number
        self.cell(0, 10, f'Pág. {self.page_no()}', align='C')

    def indice_header(self, texto):
        self.set_font("Poppins bold", size=16)
        self.set_fill_color(COLOR_BASE)
        self.set_text_color(FUENTES)
        self.cell(0, 20, f"  {texto}", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT, center=True, fill=True)

    def indice_item(self, texto, link):
        self.set_font("Poppins regular", size=12)
        self.set_fill_color(COLOR_CLARO)
        self.set_text_color(FUENTES)
        self.cell(0, 10, f"    {texto}", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT, center=True, fill=True, link=link)

    def informe_title(self, fuente):
        self.set_font("Poppins bold", size=22)
        self.cell(0, 10, f"Ficha Provincial - {self.provincia}", 0, align="C", new_x=XPos.CENTER, new_y=YPos.NEXT, center=True)
        self.set_font("Poppins regular", size=9)
        self.set_text_color(FUENTES_COLOR_CLARO)
        self.cell(0, 5, f"{fuente}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT, center=True)
        self.set_text_color("#000000")  # Reset text color for subsequent content
        self.ln(10)  # Add a line break after the title

    def seccion_title(self, seccion_title, link):
        self.set_font('Poppins bold', '', 14)
        self.set_text_color('#FFFFFF')
        self.set_fill_color(COLOR_BASE)
        chapter_title = f'  {seccion_title}'
        self.cell(0, 10, chapter_title, fill=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.set_link(link)

    def grafico(self, grafico: str, fuente: str, x: float = enums.Align.C, w: float = 190, title: str = ""):
        if grafico == "":
            self.ln(-10)
            return
        if title != "":
            self.set_font("Poppins regular", size=14)
            self.set_text_color("#0000008A")
            self.multi_cell(0, 10, title, border=0, align="C", new_y=YPos.NEXT, new_x=XPos.LMARGIN, max_line_height=8)
            self.ln(2)
        # Use cached dimensions and keep loaded image in cache to avoid recomputation
        self.image(grafico, x=x, w=w, dims=self.image_dims.get(grafico))
        self.set_font("Poppins regular", size=6)
        self.set_text_color(FUENTES_COLOR_CLARO)
        self.set_x(w - 20)
        self.cell(0, 5, f"Fuente: {fuente}", align='L', border=0, new_y=YPos.NEXT, new_x=XPos.LMARGIN)

    def kpi(self, nombre: str, valor: str, fuente: str):
        self.set_font("Poppins bold", size=13)
        self.set_text_color("#FFFFFF")
        self.set_draw_color(COLOR_CLARO)
        self.set_fill_color(COLOR_BASE)
        self.multi_cell(60, 15, text=nombre, border=1, align='C', fill=True, new_y=YPos.NEXT, new_x=XPos.LEFT, max_line_height=7.5)
        self.set_font("Poppins regular", size=16)
        self.set_text_color(COLOR_BASE)
        self.cell(60, 20, f"{valor}", align='C', border=1, new_y=YPos.NEXT, new_x=XPos.LEFT)
        self.set_font("Poppins regular", size=6)
        self.set_text_color(FUENTES_COLOR_CLARO)
        self.cell(60, 5, f"Fuente: {fuente}", align='C', border=0, new_y=YPos.NEXT, new_x=XPos.RIGHT)

    def tabla(self, df, title: str = "", width: float = 190):
        if df.empty:
            self.ln(-10)
            return
        # Reemplazar 'NaN' por ''
        df = df.fillna('')
        # Reemplazar floats con ints
        df = df.map(lambda x: int(x) if isinstance(x, float) else x)
        if title != "":
            self.set_x(10)
            self.set_font("Poppins regular", size=14)
            self.set_text_color("#0000008A")
            self.multi_cell(0, 10, title, border=0, align="C", new_y=YPos.NEXT, new_x=XPos.LMARGIN, max_line_height=5)
            self.ln(4)
        self.set_font("Poppins regular", size=10)
        self.set_text_color("#101010")
        self.set_draw_color(COLOR_BASE)
        self.set_fill_color((227, 222, 206))
        self.set_x(15)

        # Construir secuencia de rows (iterable) incluyendo headers
        # Ancho de cada columna (distribución equitativa)
        col_widths = [(width - 15) / len(df.columns)] * len(df.columns)

        headings_style = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=(44, 60, 95))

        try:
            with self.table(
                borders_layout=enums.TableBordersLayout.MINIMAL,
                text_align=enums.Align.C,
                cell_fill_color=(243, 240, 233),
                cell_fill_mode=enums.TableCellFillMode.ROWS,
                line_height=self.font_size * 2.5,
                col_widths=col_widths,
                first_row_as_headings=True,
                width=width,
            ) as table:
                # 1. Añadir la fila de encabezados
                header_row = table.row()
                for col_name in df.columns:
                    header_row.cell(str(col_name), style=headings_style)

                # 2. Añadir las filas de datos
                for index, data_row in df.iterrows():
                    row = table.row()
                    for item in data_row:
                        row.cell(str(item))
        except Exception as e:
            print(f"Error al crear la tabla: {e}")


def ficha_provincial_pdf(provincia: str, content: dict, filename):
    # Preload dimensions for all static images to avoid repeated size calculations
    image_paths = [HEADER]
    image_paths += [
        comp.get("img")
        for comp in content.get("componentes", {}).values()
        if isinstance(comp, dict) and comp.get("img")
    ]
    precache_images(image_paths)

    pdf = PDF(provincia=provincia)
    # Agregamos las fuentes
    pdf.add_font("Poppins regular", "", "static/fonts/Poppins/Poppins-Regular.ttf")
    pdf.add_font("Poppins regular", "B", "static/fonts/Poppins/Poppins-Bold.ttf")
    pdf.add_font("Poppins bold", "", "static/fonts/Poppins/Poppins-Bold.ttf")
    pdf.add_font("Poppins italic", "", "static/fonts/Poppins/Poppins-Italic.ttf")

    pdf.set_top_margin(20)

    pdf.add_page()
    pdf.image(HEADER, x=0, y=0, w=WIDTH, dims=IMAGE_DIMS_CACHE.get(HEADER))
    pdf.set_y(60)
    pdf.informe_title(fuente="Dirección Nacional de Informes y Estudios")

    # 8 Links
    s1 = pdf.add_link()
    s2 = pdf.add_link()
    s3 = pdf.add_link()
    s4 = pdf.add_link()
    s5 = pdf.add_link()
    s6 = pdf.add_link()
    s7 = pdf.add_link()
    s8 = pdf.add_link()

    pdf.indice_header("Contenidos")
    pdf.indice_item("1. Indicadores de Contexto", link=s1)
    pdf.indice_item("2. Inversión en I+D", link=s2)
    pdf.indice_item("3. Proyectos", link=s3)
    pdf.indice_item("4. Infraestructura", link=s4)
    pdf.indice_item("5. Capital Humano", link=s5)
    pdf.indice_item("6. Resultados", link=s6)
    pdf.indice_item("7. Ciencia y Sociedad", link=s7)
    pdf.indice_item("8. Consideraciones finales", link=s8)

    pdf.add_page()  # Start a new page for the content

    # Sección 1
    try:
        pdf.seccion_title("Indicadores de contexto", s1)
        pdf.ln(10)  # Add a line break before the content
        pdf.set_x(30)  # Set X position for the first KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_poblacion_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_poblacion_prov"]["resultado_sql"], content["componentes"]["kpi_poblacion_prov"]["config"])}",
            f"{content["componentes"]["kpi_poblacion_prov"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_densidad_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_densidad_prov"]["resultado_sql"], content["componentes"]["kpi_densidad_prov"]["config"])}",
            f"{content["componentes"]["kpi_densidad_prov"]["fuente"]}"
        )
        pdf.ln(5)  # Add a line break before the content
        pdf.set_x(30)  # Set X position for the first KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_actividad_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_actividad_prov"]["resultado_sql"], content["componentes"]["kpi_tasa_actividad_prov"]["config"])}",
            f"{content["componentes"]["kpi_tasa_actividad_prov"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_actividad_nac"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_actividad_nac"]["resultado_sql"], content["componentes"]["kpi_tasa_actividad_nac"]["config"])}",
            f"{content["componentes"]["kpi_tasa_actividad_nac"]["fuente"]}"
        )
        pdf.ln(5)  # Add a line break before the content
        pdf.set_x(30)  # Set X position for the first KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_desempleo_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_desempleo_prov"]["resultado_sql"], content["componentes"]["kpi_tasa_desempleo_prov"]["config"])}",
            f"{content["componentes"]["kpi_tasa_desempleo_prov"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_desempleo_nac"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_desempleo_nac"]["resultado_sql"], content["componentes"]["kpi_tasa_desempleo_nac"]["config"])}",
            f"{content["componentes"]["kpi_tasa_desempleo_nac"]["fuente"]}"
        )
        pdf.ln(10)
        pdf.grafico(
            content["componentes"]["grafico_expo_top5"]["img"],
            content["componentes"]["grafico_expo_top5"]["fuente"]
        )
        pdf.ln(20)
    except Exception as e:
        print(f"Error al generar la sección 1: {e}")
        print(e)

    # Seccion 2
    try:
        pdf.seccion_title("Inversión en I+D", s2)
        pdf.ln(5)
        pdf.grafico(
            content["componentes"]["grafico_evolucion_regional"]["img"],
            content["componentes"]["grafico_evolucion_regional"]["fuente"]
        )
        pdf.ln(10)
        pdf.grafico(
            content["componentes"]["grafico_inv_por_investigador"]["img"],
            content["componentes"]["grafico_inv_por_investigador"]["fuente"]
        )
        pdf.ln(10)
        pdf.grafico(
            content["componentes"]["grafico_inv_empresaria_sector"]["img"],
            content["componentes"]["grafico_inv_empresaria_sector"]["fuente"]
        )
        pdf.ln(5)
    except Exception as e:
        print(f"Error al generar la sección 2: {e}")
        print(e)

    # Seccion 3
    try:
        pdf.seccion_title("Proyectos", s3)
        pdf.ln(12.5)  # Add a line break before the content
        pdf.kpi(
            f"{content["componentes"]["kpi_pfi_provincial"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_pfi_provincial"]["resultado_sql"], content["componentes"]["kpi_pfi_provincial"]["config"])}",
            f"{content["componentes"]["kpi_pfi_provincial"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 65)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_pfi_regional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_pfi_regional"]["resultado_sql"], content["componentes"]["kpi_pfi_regional"]["config"])}",
            f"{content["componentes"]["kpi_pfi_regional"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 130)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_pfi_nacional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_pfi_nacional"]["resultado_sql"], content["componentes"]["kpi_pfi_nacional"]["config"])}",
            f"{content["componentes"]["kpi_pfi_nacional"]["fuente"]}"
        )
        pdf.ln(7.5)  # Add a line break before the content
        pdf.kpi(
            f"{content["componentes"]["kpi_porc_privada_provincial"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_porc_privada_provincial"]["resultado_sql"], content["componentes"]["kpi_porc_privada_provincial"]["config"])}",
            f"{content["componentes"]["kpi_porc_privada_provincial"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 65)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_porc_privada_regional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_porc_privada_regional"]["resultado_sql"], content["componentes"]["kpi_porc_privada_regional"]["config"])}",
            f"{content["componentes"]["kpi_porc_privada_regional"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 130)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_porc_privada_nacional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_porc_privada_nacional"]["resultado_sql"], content["componentes"]["kpi_porc_privada_nacional"]["config"])}",
            f"{content["componentes"]["kpi_porc_privada_nacional"]["fuente"]}"
        )
        pdf.add_page()

        tabla_pfi_cruce_df = content['componentes']['tabla_pfi_cruce']['df']
        pdf.tabla(tabla_pfi_cruce_df, content["componentes"]["tabla_pfi_cruce"]["nombre"], width=190)
        pdf.ln(10)  # Add a line break before the next section
    except Exception as e:
        print(f"Error al generar la sección 3: {e}")
        print(e)

    # Seccion 4
    try:
        pdf.seccion_title("Infraestructura", s4)
        pdf.ln(5)  # Add a line break before the content
        pdf.set_x(80)
        pdf.kpi(
            f"{content["componentes"]["kpi_unidades_id_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_unidades_id_prov"]["resultado_sql"], content["componentes"]["kpi_unidades_id_prov"]["config"])}",
            f"{content["componentes"]["kpi_unidades_id_prov"]["fuente"]}"
        )
        pdf.ln(5)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_unidades_por_inst"]["img"],
            content["componentes"]["grafico_unidades_por_inst"]["fuente"],
            title=content["componentes"]["grafico_unidades_por_inst"]["nombre"]
        )
        pdf.ln(10)  # Add a line break before the content
        pdf.kpi(
            f"{content["componentes"]["kpi_equipos_provincial"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_equipos_provincial"]["resultado_sql"], content["componentes"]["kpi_equipos_provincial"]["config"])}",
            f"{content["componentes"]["kpi_equipos_provincial"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 65)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_equipos_regional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_equipos_regional"]["resultado_sql"], content["componentes"]["kpi_equipos_regional"]["config"])}",
            f"{content["componentes"]["kpi_equipos_regional"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 130)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_equipos_nacional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_equipos_nacional"]["resultado_sql"], content["componentes"]["kpi_equipos_nacional"]["config"])}",
            f"{content["componentes"]["kpi_equipos_nacional"]["fuente"]}"
        )
        pdf.ln(5)

        pdf.grafico(
            content["componentes"]["grafico_equipos_por_tipo"]["img"],
            content["componentes"]["grafico_equipos_por_tipo"]["fuente"],
        )
        pdf.ln(7.5)
    except Exception as e:
        print(f"Error al generar la sección 4: {e}")
        print(e)

    # Seccion 5
    try:
        pdf.seccion_title("Capital Humano", s5)
        pdf.ln(7.5)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_distribucion_investigadores"]["img"],
            content["componentes"]["grafico_distribucion_investigadores"]["fuente"],
        )
        pdf.ln(15)  # Add a line break before the content

        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_pea_provincial"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_pea_provincial"]["resultado_sql"], content["componentes"]["kpi_tasa_pea_provincial"]["config"])}",
            f"{content["componentes"]["kpi_tasa_pea_provincial"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 65)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_pea_regional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_pea_regional"]["resultado_sql"], content["componentes"]["kpi_tasa_pea_regional"]["config"])}",
            f"{content["componentes"]["kpi_tasa_pea_regional"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 130)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_tasa_pea_nacional"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_tasa_pea_nacional"]["resultado_sql"], content["componentes"]["kpi_tasa_pea_nacional"]["config"])}",
            f"{content["componentes"]["kpi_tasa_pea_nacional"]["fuente"]}"
        )
        pdf.ln(15)

        tabla_personas_por_funcion_df = content["componentes"]["tabla_personas_por_funcion"]["df"]
        pdf.tabla(tabla_personas_por_funcion_df, content["componentes"]["tabla_personas_por_funcion"]["nombre"], width=190)
        pdf.ln(20)

        pdf.grafico(
            content["componentes"]["grafico_evolucion_investigadores"]["img"],
            content["componentes"]["grafico_evolucion_investigadores"]["fuente"],
        )
    except Exception as e:
        print(f"Error al generar la sección 5: {e}")
        print(e)

    # Salto de página
    # pdf.add_page()
    pdf.ln(20)  # Add a line break before the next section

    # Seccion 6
    try:
        pdf.seccion_title("Resultados", s6)
        pdf.ln(10)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_expo_intensidad"]["img"],
            content["componentes"]["grafico_expo_intensidad"]["fuente"],
        )
        pdf.ln(20)  # Add a line break before the content
        pdf.grafico(
            content["componentes"]["grafico_expo_evolucion"]["img"],
            content["componentes"]["grafico_expo_evolucion"]["fuente"],
        )
        pdf.ln(10)  # Add a line break before the content
        pdf.grafico(
            content["componentes"]["grafico_expo_destino"]["img"],
            content["componentes"]["grafico_expo_destino"]["fuente"],
        )
        pdf.ln(15)  # Add a line break before the content

        pdf.set_x(30)  # Set X position for the first KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_patentes_cyt_prov"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_patentes_cyt_prov"]["resultado_sql"], content["componentes"]["kpi_patentes_cyt_prov"]["config"])}",
            f"{content["componentes"]["kpi_patentes_cyt_prov"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() - 50)  # Adjust Y position for the next KPI
        pdf.set_x(pdf.get_x() + 110)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_patentes_cyt_arg"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_patentes_cyt_arg"]["resultado_sql"], content["componentes"]["kpi_patentes_cyt_arg"]["config"])}",
            f"{content["componentes"]["kpi_patentes_cyt_arg"]["fuente"]}"
        )
        pdf.set_y(pdf.get_y() + 15)  # Adjust Y position for the next KPI
        pdf.set_x(75)  # Move to the right for the next KPI
        pdf.kpi(
            f"{content["componentes"]["kpi_patentes_arg"]["nombre"]}",
            f"{procesar_kpi(content["componentes"]["kpi_patentes_arg"]["resultado_sql"], content["componentes"]["kpi_patentes_arg"]["config"])}",
            f"{content["componentes"]["kpi_patentes_arg"]["fuente"]}"
        )
        pdf.ln(10)

        pdf.grafico(
            content["componentes"]["grafico_patentes_evolucion"]["img"],
            content["componentes"]["grafico_patentes_evolucion"]["fuente"],
        )
        pdf.ln(10)  # Add a line break before the content

        tabla_patentes_sector_df = content["componentes"]["tabla_patentes_sector"]["df"]
        pdf.tabla(tabla_patentes_sector_df, content["componentes"]["tabla_patentes_sector"]["nombre"], width=190)
        pdf.ln(10)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_produccion_evolucion"]["img"],
            content["componentes"]["grafico_produccion_evolucion"]["fuente"],
        )
        pdf.ln(20)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_produccion_tipo"]["img"],
            content["componentes"]["grafico_produccion_tipo"]["fuente"],
        )
        pdf.ln(10)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_publicaciones_area"]["img"],
            content["componentes"]["grafico_publicaciones_area"]["fuente"],
        )
        pdf.ln(10)  # Add a line break before the content

        pdf.tabla(
            content["componentes"]["tabla_articulos_q1_q2"]["df"],
            content["componentes"]["tabla_articulos_q1_q2"]["nombre"],
            width=190
        )
    except Exception as e:
        print(f"Error al generar la sección 6: {e}")
        print(e)

    pdf.add_page()

    # Seccion 7
    try:
        pdf.seccion_title("Ciencia y Sociedad", s7)
        pdf.ln(12.5)  # Add a line break before the content

        pdf.grafico(
            content["componentes"]["grafico_percepcion_calidad_vida"]["img"],
            content["componentes"]["grafico_percepcion_calidad_vida"]["fuente"],
            title=content["componentes"]["grafico_percepcion_calidad_vida"]["nombre"],
            w=195
        )
    except Exception as e:
        print(f"Error al generar la sección 7: {e}")
        print(e)

    pdf.add_page()

    pdf.seccion_title("Consideraciones finales", s8)
    pdf.ln(5)  # Add a line break before the content

    pdf.set_font("Poppins regular", size=12)
    pdf.set_text_color("#000000")  # Reset text color for content
    pdf.multi_cell(0, 10, "Holi")

    # Generar el PDF
    pdf.output(filename)
