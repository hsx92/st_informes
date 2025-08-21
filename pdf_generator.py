from fpdf import FPDF, XPos, YPos, enums


HEADER = "static/logo/letterhead.png"
HEIGHT = 297  # A4 height in mm
WIDTH = 210  # A4 width in mm
FUENTES = "#FFFFFF"
FUENTES_COLOR_CLARO = "#666666"
COLOR_BASE = "#2C3C5F"
COLOR_CLARO = "#7589A3"


class PDF(FPDF):
    def __init__(self, provincia=None):
        super().__init__()
        self.provincia = provincia

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


def ficha_provincial_pdf(provincia: str, content: dict, filename):
    pdf = PDF(provincia=provincia)
    # Agregamos las fuentes
    pdf.add_font("Poppins regular", "", "static/fonts/Poppins/Poppins-Regular.ttf")
    pdf.add_font("Poppins bold", "", "static/fonts/Poppins/Poppins-Bold.ttf")
    pdf.add_font("Poppins italic", "", "static/fonts/Poppins/Poppins-Italic.ttf")

    pdf.set_top_margin(20)

    pdf.add_page()
    pdf.image(HEADER, x=0, y=0, w=WIDTH)
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
    pdf.seccion_title("Indicadores de contexto", s1)
    pdf.ln(5)  # Add a line break before the content
    pdf.set_x(30)  # Set X position for the first KPI
    pdf.kpi("Población Provincial", "5.000.000", "INDEC")
    pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
    pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
    pdf.kpi("Población Nacional", "45.000.000", "INDEC")
    pdf.ln(2)  # Add a line break before the content
    pdf.set_x(30)  # Set X position for the first KPI
    pdf.kpi("Población Provincial", "5.000.000", "INDEC")
    pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
    pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
    pdf.kpi("Población Nacional", "45.000.000", "INDEC")
    pdf.ln(2)  # Add a line break before the content
    pdf.set_x(30)  # Set X position for the first KPI
    pdf.kpi("Población Provincial", "5.000.000", "INDEC")
    pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
    pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
    pdf.kpi("Población Nacional aaaaaaaa", "45.000.000", "INDEC")
    pdf.ln(10)
    pdf.image('output/top5_exportaciones.png', x=enums.Align.C, w=190)
    pdf.cell(0, 5, "Fuente: INDEC", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(20)

    pdf.seccion_title("Inversión en I+D", s2)
    pdf.ln(5)
    pdf.image('output/inversionID.png', x=enums.Align.C, w=190)
    pdf.cell(0, 5, "Fuente: POSIX", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.image('output/inversionInvestigador.png', x=enums.Align.C, w=190)
    pdf.cell(0, 5, "Fuente: POSIX", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.image('output/inversionEmpresas.png', x=enums.Align.C, w=190)
    pdf.cell(0, 5, "Fuente: POSIX", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.seccion_title("Proyectos", s3)
    pdf.ln(5)  # Add a line break before the content

    pdf.seccion_title("Infraestructura", s4)
    pdf.ln(5)  # Add a line break before the content

    pdf.seccion_title("Capital Humano", s5)
    pdf.ln(5)  # Add a line break before the content

    pdf.seccion_title("Resultados", s6)
    pdf.ln(5)  # Add a line break before the content

    pdf.seccion_title("Ciencia y Sociedad", s7)
    pdf.ln(5)  # Add a line break before the content

    pdf.seccion_title("Consideraciones finales", s8)
    pdf.ln(5)  # Add a line break before the content

    pdf.set_font("Poppins regular", size=12)
    pdf.set_text_color("#000000")  # Reset text color for content
    pdf.multi_cell(0, 10, str(content))
    pdf.output(filename)


if __name__ == "__main__":
    provincia = "Buenos Aires"
    content = {"contenido": "Este es el contenido de la ficha provincial."}
    filename = "output/ficha_provincial.pdf"
    ficha_provincial_pdf(provincia, content, filename)
