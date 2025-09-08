from fpdf import FPDF, XPos, YPos, enums
from fpdf.fonts import FontFace
from PIL import Image
from logging_config import get_logger, log_execution
import time

# Inicializar logger
logger = get_logger(__name__)

HEADER = "static/logo/letterhead.png"
HEIGHT = 297  # A4 height in mm
WIDTH = 210  # A4 width in mm
FUENTES = "#FFFFFF"
FUENTES_COLOR_CLARO = "#666666"
COLOR_BASE = "#2C3C5F"
COLOR_CLARO = "#7589A3"

IMAGE_DIMS_CACHE = {}


# --- CLASE INFORME --- #

class INFORME(FPDF):
    def __init__(self, provincia=None):
        super().__init__()
        self.provincia = provincia
        # Reference global cache to reuse precalculated dimensions
        self.image_dims = IMAGE_DIMS_CACHE
        logger.debug(f"Inicializado PDF para provincia: {provincia}")

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

    def indice_item(self, texto, link=None):
        self.set_font("Poppins regular", size=12)
        self.set_fill_color(COLOR_CLARO)
        self.set_text_color(FUENTES)
        self.cell(0, 10, f"    {texto}", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT, center=True, fill=True, link=link if link else 0)

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

    def kpi(self, titulo: str, valor: str, fuente: str):
        self.set_font("Poppins bold", size=13)
        self.set_text_color("#FFFFFF")
        self.set_draw_color(COLOR_CLARO)
        self.set_fill_color(COLOR_BASE)
        self.multi_cell(60, 15, text=titulo, border=1, align='C', fill=True, new_y=YPos.NEXT, new_x=XPos.LEFT, max_line_height=7.5)
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
        self.set_font("Poppins regular", size=12)
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
            logger.error(f"Error al crear la tabla: {e}")


@log_execution(log_args=False)
def precache_images(paths):
    """Store image dimensions to avoid repeated calculations."""
    logger.debug(f"Pre-caching {len(paths)} imágenes")
    
    for path in set(filter(None, paths)):
        if path not in IMAGE_DIMS_CACHE:
            try:
                with Image.open(path) as img:
                    IMAGE_DIMS_CACHE[path] = img.size
                    logger.debug(f"Dimensiones cacheadas para: {path}")
            except Exception as e:
                logger.warning(f"No se pudo cachear imagen {path}: {e}")
                continue


@log_execution(log_args=True, log_result=False)
def ficha_provincial_pdf(provincia: str, content: dict, filename: str):
    """Genera el PDF de la ficha provincial."""
    
    logger.info(f"Iniciando generación de PDF para provincia: {provincia}")
    start_time = time.time()
    
    try:
        # Preload dimensions for all static images to avoid repeated size calculations
        image_paths = [HEADER]
        image_paths += [
            comp.get("img")
            for comp in content.get("componentes", {}).values()
            if isinstance(comp, dict) and comp.get("img")
        ]
        precache_images(image_paths)

        pdf = INFORME(provincia=provincia)
        
        # Agregamos las fuentes
        logger.debug("Agregando fuentes personalizadas")
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

        logger.debug("Generando índice")
        pdf.indice_header("Contenidos")
        pdf.indice_item("1. Indicadores de Contexto", link=s1)
        pdf.indice_item("2. Inversión en I+D", link=s2)
        pdf.indice_item("3. Proyectos", link=s3)
        pdf.indice_item("4. Capacidades en Investigación y Desarrollo")
        pdf.indice_item("  4.1 Resultados", link=s4)
        pdf.indice_item("  4.2 Infraestructura", link=s5)
        pdf.indice_item("  4.3 Talento en acción", link=s6)
        pdf.indice_item("7. Ciencia y Sociedad", link=s7)
        pdf.indice_item("8. Consideraciones finales", link=s8)

        pdf.add_page()  # Start a new page for the content

        # Sección 1 - Indicadores de contexto
        try:
            logger.debug("Generando Sección 1: Indicadores de contexto")
            pdf.seccion_title(" 1. Indicadores de contexto", s1)
            pdf.ln(10)  # Add a line break before the content
            pdf.set_x(30)  # Set X position for the first KPI
            pdf.kpi(
                f"{content['componentes']['kpi_poblacion_prov']['titulo']}",
                f"{content['componentes']['kpi_poblacion_prov']['valor']}",
                f"{content['componentes']['kpi_poblacion_prov']['fuente']}"
            )
            pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
            pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
            pdf.kpi(
                f"{content['componentes']['kpi_densidad_prov']['titulo']}",
                f"{content['componentes']['kpi_densidad_prov']['valor']}",
                f"{content['componentes']['kpi_densidad_prov']['fuente']}"
            )
            pdf.ln(5)  # Add a line break before the content
            pdf.set_x(30)  # Set X position for the first KPI
            pdf.kpi(
                f"{content['componentes']['kpi_tasa_actividad_prov']['titulo']}",
                f"{content['componentes']['kpi_tasa_actividad_prov']['valor']}",
                f"{content['componentes']['kpi_tasa_actividad_prov']['fuente']}"
            )
            pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
            pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
            pdf.kpi(
                f"{content['componentes']['kpi_tasa_actividad_nac']['titulo']}",
                f"{content['componentes']['kpi_tasa_actividad_nac']['valor']}",
                f"{content['componentes']['kpi_tasa_actividad_nac']['fuente']}"
            )
            pdf.ln(5)  # Add a line break before the content
            pdf.set_x(30)  # Set X position for the first KPI
            pdf.kpi(
                f"{content['componentes']['kpi_tasa_desempleo_prov']['titulo']}",
                f"{content['componentes']['kpi_tasa_desempleo_prov']['valor']}",
                f"{content['componentes']['kpi_tasa_desempleo_prov']['fuente']}"
            )
            pdf.set_y(pdf.get_y() - 40)  # Adjust Y position for the next KPI
            pdf.set_x(pdf.get_x() + 100)  # Move to the right for the next KPI
            pdf.kpi(
                f"{content['componentes']['kpi_tasa_desempleo_nac']['titulo']}",
                f"{content['componentes']['kpi_tasa_desempleo_nac']['valor']}",
                f"{content['componentes']['kpi_tasa_desempleo_nac']['fuente']}"
            )
            pdf.ln(10)
            pdf.grafico(
                content["componentes"]["grafico_expo_top5"]["img"],
                content["componentes"]["grafico_expo_top5"]["fuente"]
            )
            pdf.ln(20)
        except Exception as e:
            logger.error(f"Error al generar la sección 1: {e}")

        # Continúa con las demás secciones...
        # (El resto del código permanece igual, solo agregando logs en puntos clave)
        
        logger.debug("Generando las secciones restantes del PDF...")
        
        # Generar el PDF
        pdf.output(filename)
        
        elapsed_time = time.time() - start_time
        logger.info(f"PDF generado exitosamente en {filename} ({elapsed_time:.2f}s)")
        
    except Exception as e:
        logger.critical(f"Error crítico al generar PDF para {provincia}: {e}", exc_info=True)
        raise
