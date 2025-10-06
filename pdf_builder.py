from fpdf import FPDF, XPos, YPos, enums
from fpdf.fonts import FontFace
from PIL import Image
from logging_config import get_logger, log_execution
from pdf_dynamic_layout import PDFLayoutManager
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
        self.image_dims = IMAGE_DIMS_CACHE
        self.layout_manager = PDFLayoutManager(self)
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

    def grafico(self, grafico: str, fuente: str, x: float = None,
                w: float = 190, title: str = "", auto_layout: bool = True):
        if not grafico:
            return
            
        # Calcular altura real del gráfico
        img_height = self.layout_manager.calculate_image_height(grafico, w)
        
        # Altura total necesaria (título + imagen + fuente)
        total_height = (10 if title else 0) + img_height
        
        # Verificar si necesitamos nueva página
        if auto_layout:
            self.layout_manager.add_page_if_needed(total_height)
        
        # Renderizar título si existe
        if title:
            self.set_font("Poppins regular", size=14)
            self.set_text_color("#0000008A")
            self.multi_cell(
                0, 10, title, border=0, align="C",
                new_y=YPos.NEXT, new_x=XPos.LMARGIN, max_line_height=8
            )
            self.ln(2)
        
        # Renderizar imagen y agregar bordes de 1px
        x_pos = x if x is not None else (self.w - w) / 2
        self.rect(x=x_pos-1, y=self.get_y()-1, w=w+1, h=img_height+1.5, style='D')
        self.image(grafico, x=x_pos, w=w, dims=self.image_dims.get(grafico))

        # Renderizar fuente
        self.set_font("Poppins regular", size=6)
        self.set_text_color(FUENTES_COLOR_CLARO)
        self.set_x(w - 20)
        self.cell(
            0, 5, f"Fuente: {fuente}", align='L', border=0,
            new_y=YPos.NEXT, new_x=XPos.LMARGIN
        )
        
        # Espaciado inteligente después del gráfico
        self.layout_manager.smart_spacing(5)

    def kpi(self, titulo: str, valor: str, fuente: str):
        self.set_font("Poppins bold", size=12)
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

    def tabla(self, df, type: str = "", title: str = "", subtitle: str = "", fuente: str = "", width: float = 190, cols_width: list = None, auto_layout: bool = True):
        if df.empty:
            return
            
        # Preparar datos
        df = df.fillna('')
        df = df.map(lambda x: int(x) if isinstance(x, float) else x)
        
        # Calcular altura necesaria
        table_height = self.layout_manager.calculate_table_height(df)
        title_height = 14 if title else 0
        total_height = title_height + table_height
        
        # Verificar espacio disponible
        if auto_layout:
            self.layout_manager.add_page_if_needed(total_height)
        
        # Renderizar título
        if title:
            self.set_x(10)
            self.set_font("Poppins regular", size=12)
            self.set_text_color("#0000008A")
            self.multi_cell(
                0, 5, title, border=0, align="C",
                new_y=YPos.NEXT, new_x=XPos.LMARGIN, max_line_height=5
            )
            self.ln(2.5)
        if subtitle:
            self.set_x(10)
            self.set_font("Poppins regular", size=9)
            self.set_text_color("#0000008A")
            self.multi_cell(
                0, 5, subtitle, border=0, align="C",
                new_y=YPos.NEXT, new_x=XPos.LMARGIN, max_line_height=5
            )
            self.ln(2.5)
        
        # Configurar tabla
        self.set_font("Poppins regular", size=9)
        self.set_text_color("#101010")
        self.set_draw_color(COLOR_BASE)
        self.set_fill_color(FUENTES)
        self.set_x(15)
        
        # Calcular anchos de columna según especificación (en porcentaje o iguales)
        if cols_width and len(cols_width) == len(df.columns):
            col_widths = [(width - 15) * (w / 100) for w in cols_width]
        else:
            col_widths = [(width - 15) / len(df.columns)] * len(df.columns)
        
        headings_style = FontFace(
            emphasis="BOLD", color=(FUENTES),
            fill_color=(COLOR_BASE), size_pt=9
        )

        try:
            if type == "TABLA_AGRUPADA":
                self._render_table_chunk(df, col_widths, headings_style, width, format_last=True)
            else:
                with self.table(
                    borders_layout=enums.TableBordersLayout.NO_HORIZONTAL_LINES,
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
        
        # Renderizar fuente
        if fuente:
            self.ln(2)
            self.set_font("Poppins regular", size=6)
            self.set_text_color(FUENTES_COLOR_CLARO)
            self.set_x(WIDTH - 30)
            self.cell(
                0, 5, f"Fuente: {fuente}", align='L', border=0,
                new_y=YPos.NEXT, new_x=XPos.LMARGIN
            )
    
    def _render_table_chunk(
            self, df_chunk, col_widths, headings_style,
            width, include_header=True, format_last=False):
        """Renderiza un fragmento de tabla."""
        with self.table(
            borders_layout=enums.TableBordersLayout.MINIMAL,
            text_align=enums.Align.C,
            cell_fill_color=(243, 240, 233),
            cell_fill_mode=enums.TableCellFillMode.ROWS,
            line_height=self.font_size * 1.2,
            col_widths=col_widths,
            first_row_as_headings=include_header,
            width=width,
            padding=2
        ) as table:
            if include_header:
                header_row = table.row()
                for idx, col_name in enumerate(df_chunk.columns):
                    # Agregar borde derecho solo a la última columna del header
                    if idx == len(df_chunk.columns) - 1:
                        header_row.cell(str(col_name), style=headings_style, border=enums.CellBordersLayout.RIGHT)
                    else:
                        header_row.cell(str(col_name), style=headings_style)
            
            total_rows = len(df_chunk)
            for row_idx, (index, data_row) in enumerate(df_chunk.iterrows()):
                is_last_row = (row_idx == total_rows - 1) and format_last
                row = table.row()
                
                for col_idx, item in enumerate(data_row):
                    cell_value = str(item)
                    is_last_col = col_idx == len(data_row) - 1
                    
                    # Determinar el estilo del borde según la posición
                    if is_last_row:
                        # Última fila con format_last=True: solo bordes externos
                        if col_idx == 0:
                            # Primera celda de última fila: borde izquierdo y abajo
                            border = enums.CellBordersLayout.LEFT | enums.CellBordersLayout.BOTTOM | enums.CellBordersLayout.TOP
                        elif is_last_col:
                            # Última celda de última fila: borde derecho y abajo
                            border = enums.CellBordersLayout.RIGHT | enums.CellBordersLayout.BOTTOM | enums.CellBordersLayout.TOP
                        else:
                            # Celdas del medio en última fila: solo borde abajo y arriba
                            border = enums.CellBordersLayout.BOTTOM | enums.CellBordersLayout.TOP

                        # Aplicar estilo bold a la última fila
                        row.cell(
                            cell_value,
                            border=border,
                            style=FontFace(emphasis="BOLD", size_pt=9)
                        )
                    else:
                        # Filas normales
                        row.cell(
                            cell_value,
                            border=(
                                enums.CellBordersLayout.LEFT |
                                enums.CellBordersLayout.RIGHT |
                                enums.CellBordersLayout.TOP
                            ) if cell_value else (
                                enums.CellBordersLayout.LEFT |
                                enums.CellBordersLayout.RIGHT
                            )
                        )

    def kpi_grid(self, kpis: list, cols: int = 2, auto_layout: bool = True):
        """
        Renderiza una cuadrícula de KPIs usando la función kpi() existente.
        """
        if not kpis:
            return
        
        # Dimensiones
        kpi_width = 55
        kpi_total_height = 40  # Alto total de un KPI
        h_spacing = 15 if cols == 2 else 10  # Espacio horizontal entre KPIs
        v_spacing = 2.5
        
        # Calcular filas
        rows = (len(kpis) + cols - 1) // cols
        
        # Verificar ancho disponible
        grid_width = cols * kpi_width + (cols - 1) * h_spacing
        max_width = self.w - self.l_margin - self.r_margin
        
        if grid_width > max_width:
            # Reducir columnas si es necesario
            cols = min(cols, 3)  # Máximo 3 columnas para seguridad
            while cols > 1 and (cols * kpi_width + (cols - 1) * h_spacing) > max_width:
                cols -= 1
            rows = (len(kpis) + cols - 1) // cols
            grid_width = cols * kpi_width + (cols - 1) * h_spacing
        
        # Calcular altura total necesaria
        grid_height = rows * kpi_total_height + (rows - 1) * v_spacing
        
        # Verificar espacio vertical
        if auto_layout and hasattr(self, 'layout_manager'):
            self.layout_manager.add_page_if_needed(grid_height + 10)
        elif self.get_y() + grid_height > self.h - self.b_margin:
            self.add_page()
        
        # Posición inicial centrada
        start_x = (self.w - grid_width) / 2
        start_y = self.get_y()
        
        # Guardar posiciones de inicio de cada fila
        row_positions = []
        
        for row in range(rows):
            row_y = start_y + row * (kpi_total_height + v_spacing)
            row_positions.append(row_y)
        
        # Renderizar KPIs
        current_row = 0
        for i, kpi in enumerate(kpis):
            row = i // cols
            col = i % cols
            
            # Si cambiamos de fila, resetear posición
            if row != current_row:
                current_row = row
            
            # Calcular posición X para este KPI
            x_pos = start_x + col * (kpi_width + h_spacing) - (2.5 if cols > 2 else 0)
            y_pos = row_positions[row]
            
            # Posicionar cursor
            self.set_xy(x_pos, y_pos)
            
            # Renderizar KPI - pero necesitamos modificar temporalmente su comportamiento
            # Guardar configuración actual
            old_x = self.x
            old_y = self.y
            
            # Llamar a kpi con parámetros
            self.kpi(
                titulo=kpi.get('titulo', ''),
                valor=kpi.get('valor', 'N/A'),
                fuente=kpi.get('fuente', '')
            )
            
            # Si no es el último de la fila, resetear posición
            if col < cols - 1 and i < len(kpis) - 1:
                self.set_xy(old_x, old_y)
        
        # Posicionar cursor después del grid
        final_y = start_y + grid_height + v_spacing
        self.set_y(final_y)
        
        logger.debug(f"Grid de KPIs completado: {len(kpis)} elementos en {rows}x{cols}")


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
    """Genera el PDF de la ficha provincial con layout dinámico."""
    
    logger.info(f"Iniciando generación de PDF para provincia: {provincia}")
    start_time = time.time()
    
    try:
        # Precargar dimensiones de imágenes
        image_paths = [HEADER]
        image_paths += [
            comp.get("img")
            for comp in content.get("componentes", {}).values()
            if isinstance(comp, dict) and comp.get("img")
        ]
        precache_images(image_paths)

        # Crear PDF con layout manager
        pdf = INFORME(provincia=provincia)
        
        # Configurar fuentes
        logger.debug("Agregando fuentes personalizadas")
        pdf.add_font("Poppins regular", "", "static/fonts/Poppins/Poppins-Regular.ttf")
        pdf.add_font("Poppins regular", "B", "static/fonts/Poppins/Poppins-Bold.ttf")
        pdf.add_font("Poppins bold", "", "static/fonts/Poppins/Poppins-Bold.ttf")
        pdf.add_font("Poppins italic", "", "static/fonts/Poppins/Poppins-Italic.ttf")
        
        pdf.set_top_margin(10)
        pdf.set_auto_page_break(auto=True, margin=15)

        # --- PORTADA ---
        pdf.add_page()
        pdf.image(HEADER, x=0, y=0, w=WIDTH, dims=IMAGE_DIMS_CACHE.get(HEADER))
        pdf.set_y(60)
        pdf.informe_title(fuente="Dirección Nacional de Informes y Estudios")
        
        # --- ÍNDICE ---
        links = _generar_indice(pdf)
        
        # --- SECCIONES ---
        pdf.add_page()
        
        # Diccionario de funciones de sección para modularidad
        secciones = {
            'contexto': _generar_seccion_contexto,
            'inversion': _generar_seccion_inversion,
            'proyectos': _generar_seccion_proyectos,
            'capacidades': _generar_seccion_capacidades,
            'resultados': _generar_seccion_resultados,
            'infraestructura': _generar_seccion_infraestructura,
            'talento': _generar_seccion_talento,
            'sociedad': _generar_seccion_sociedad,
            # 'consideraciones': _generar_consideraciones_finales
        }
        
        # Generar cada sección
        i = 1
        for nombre_seccion, func_seccion in secciones.items():
            try:
                logger.debug(f"Generando sección: {nombre_seccion}")
                func_seccion(pdf, content['componentes'], links[f's{i}'])
                i += 1
            except Exception as e:
                logger.error(f"Error en sección {nombre_seccion}: {e}")
                # Continuar con las demás secciones
        
        # Generar el PDF
        pdf.output(filename)
        
        elapsed_time = time.time() - start_time
        logger.info(f"PDF generado exitosamente en {filename} ({elapsed_time:.2f}s)")
        
    except Exception as e:
        logger.critical(f"Error crítico al generar PDF para {provincia}: {e}", exc_info=True)
        raise


def _generar_indice(pdf):
    """Genera el índice con links navegables."""
    # Links para navegación
    links = {}
    secciones = [
        "1. Indicadores de Contexto",
        "2. Inversión en I+D",
        "3. Proyectos",
        "4. Capacidades en Investigación y Desarrollo",
        "  4.1 Resultados",
        "  4.2 Infraestructura",
        "  4.3 Talento en acción",
        "5. Ciencia y Sociedad",
        "6. Consideraciones finales"
    ]
    
    for i, seccion in enumerate(secciones, 1):
        links[f's{i}'] = pdf.add_link()
    
    pdf.indice_header("Contenidos")
    for seccion, link in zip(secciones, links.values()):
        pdf.indice_item(seccion, link=link)
    
    return links


def _generar_seccion_contexto(pdf, componentes, link=None):
    """Genera la sección de indicadores de contexto."""
    pdf.seccion_title(" 1. Indicadores de contexto", link)
    pdf.layout_manager.smart_spacing(10)

    # KPIs en grid
    kpis = [
        componentes['kpi_poblacion_prov'],
        componentes['kpi_densidad_prov'],
        componentes['kpi_tasa_actividad_prov'],
        componentes['kpi_tasa_actividad_nac'],
        componentes['kpi_tasa_desempleo_prov'],
        componentes['kpi_tasa_desempleo_nac']
    ]
    
    pdf.kpi_grid(kpis, cols=2)
    pdf.layout_manager.smart_spacing(5)

    # Gráfico de exportaciones
    if componentes['grafico_expo_top5'].get('img'):
        pdf.grafico(
            componentes["grafico_expo_top5"]["img"],
            componentes["grafico_expo_top5"]["fuente"],
            auto_layout=True
        )
    pdf.add_page()


def _generar_seccion_inversion(pdf, componentes, link=None):
    """Genera la sección de inversión en I+D."""
    pdf.seccion_title(" 2. Inversión en I+D", link)
    pdf.layout_manager.smart_spacing(5)
    
    # KPIs de APN
    kpis_apn = [
        componentes.get('kpi_apn_devengado_prov'),
        componentes.get('kpi_apn_devengado_region'),
        componentes.get('kpi_apn_devengado_nac')
    ]
    kpis_apn = [k for k in kpis_apn if k]  # Filtrar None
    
    if kpis_apn:
        pdf.kpi_grid(kpis_apn, cols=3)
    
    # Tabla de jurisdicción
    if componentes.get('tabla_apn_jurisdiccion_entidad_programa_prov', {}).get('tiene_datos', False):
        pdf.tabla(
            componentes['tabla_apn_jurisdiccion_entidad_programa_prov']['df'],
            type=componentes['tabla_apn_jurisdiccion_entidad_programa_prov'].get('tipo_componente', ''),
            title=componentes['tabla_apn_jurisdiccion_entidad_programa_prov'].get('titulo', ''),
            subtitle=componentes['tabla_apn_jurisdiccion_entidad_programa_prov'].get('subtitulo', ''),
            fuente=componentes['tabla_apn_jurisdiccion_entidad_programa_prov'].get('fuente', ''),
            cols_width=[22, 23, 30, 13, 12],
            auto_layout=True
        )

    # Más gráficos de inversión
    graficos_inversion = [
        'grafico_evolucion_presupuesto_apn',
        'grafico_evolucion_regional',
        'grafico_inv_por_investigador'
    ]
    
    for grafico_key in graficos_inversion:
        if componentes.get(grafico_key, {}).get('img'):
            pdf.grafico(
                componentes[grafico_key]["img"],
                componentes[grafico_key]["fuente"],
                auto_layout=True
            )
            pdf.layout_manager.smart_spacing(10)
    pdf.set_y(pdf.get_y() - 7.5)
    if componentes.get('grafico_inv_empresaria_sector', {}).get('tiene_datos', False):
        pdf.grafico(
            componentes['grafico_inv_empresaria_sector']['img'],
            componentes['grafico_inv_empresaria_sector']['fuente'],
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(3)


def _generar_seccion_proyectos(pdf, componentes, link=None):
    """Genera la sección de proyectos."""
    pdf.seccion_title(" 3. Proyectos", link)
    pdf.layout_manager.smart_spacing(5)

    # KPIs de proyectos
    kpis_proyectos = [
        componentes['kpi_pfi_nacional'],
        componentes['kpi_pfi_regional'],
        componentes['kpi_pfi_provincial'],
        componentes['kpi_porc_privada_nacional'],
        componentes['kpi_porc_privada_regional'],
        componentes['kpi_porc_privada_provincial']
    ]
    pdf.kpi_grid(kpis_proyectos, cols=3)
    pdf.layout_manager.smart_spacing(5)

    if componentes.get('tabla_pfi_cruce', {}).get('tiene_datos', False):
        pdf.tabla(
            componentes['tabla_pfi_cruce']['df'],
            title=componentes['tabla_pfi_cruce'].get('titulo', ''),
            subtitle=componentes['tabla_pfi_cruce'].get('subtitulo', ''),
            fuente=componentes['tabla_pfi_cruce'].get('fuente', ''),
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(10)


def _generar_seccion_capacidades(pdf, componentes, link=None):
    """Genera la subsección de resultados dentro de Capacidades en I+D."""
    pdf.seccion_title(" 4. Capacidades en Investigación y Desarrollo", link)
    pdf.layout_manager.smart_spacing(5)


def _generar_seccion_resultados(pdf, componentes, link=None):
    """Genera la subsección de resultados dentro de Capacidades en I+D."""
    pdf.seccion_title(" 4.1 Resultados", link)
    pdf.layout_manager.smart_spacing(5)

    # Gráficos de resultados
    graficos_resultados = [
        'grafico_expo_intensidad',
        'grafico_expo_evolucion',
        'grafico_expo_destino',
    ]
    
    for grafico_key in graficos_resultados:
        if componentes.get(grafico_key, {}).get('img'):
            pdf.grafico(
                componentes[grafico_key]["img"],
                componentes[grafico_key]["fuente"],
                auto_layout=True
            )
    pdf.layout_manager.smart_spacing(10)
    # KPIs de resultados
    kpis_resultados = [
        componentes['kpi_patentes_arg'],
        componentes['kpi_patentes_cyt_arg'],
        componentes['kpi_patentes_cyt_prov']
    ]
    pdf.kpi_grid(kpis_resultados, cols=3)
    pdf.layout_manager.smart_spacing(10)

    if componentes.get('grafico_patentes_evolucion', {}).get('tiene_datos', False):
        pdf.grafico(
            componentes['grafico_patentes_evolucion']['img'],
            componentes['grafico_patentes_evolucion']['fuente'],
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(10)

    if componentes.get('tabla_patentes_sector', {}).get('tiene_datos', False):
        pdf.tabla(
            componentes['tabla_patentes_sector']['df'],
            title=componentes['tabla_patentes_sector'].get('titulo', ''),
            subtitle=componentes['tabla_patentes_sector'].get('subtitulo', ''),
            fuente=componentes['tabla_patentes_sector'].get('fuente', ''),
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(10)

    graficos_resultados_2 = [
        'grafico_produccion_evolucion',
        'grafico_produccion_tipo',
        'grafico_publicaciones_area'
    ]
    for grafico_key in graficos_resultados_2:
        if componentes.get(grafico_key, {}).get('img'):
            pdf.grafico(
                componentes[grafico_key]["img"],
                componentes[grafico_key]["fuente"],
                auto_layout=True
            )
    pdf.layout_manager.smart_spacing(5)

    if componentes.get('tabla_articulos_q1_q2', {}).get('tiene_datos', False):
        pdf.tabla(
            componentes['tabla_articulos_q1_q2']['df'],
            title=componentes['tabla_articulos_q1_q2'].get('titulo', ''),
            subtitle=componentes['tabla_articulos_q1_q2'].get('subtitulo', ''),
            fuente=componentes['tabla_articulos_q1_q2'].get('fuente', ''),
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(10)


def _generar_seccion_infraestructura(pdf, componentes, link=None):
    """Genera la subsección de infraestructura dentro de Capacidades en I+D."""
    pdf.seccion_title(" 4.2 Infraestructura", link)
    pdf.layout_manager.smart_spacing(5)

    # KPI único centrado
    pdf.set_x((pdf.w - 60) / 2)
    pdf.kpi(
        titulo=componentes['kpi_unidades_id_prov'].get('titulo', ''),
        valor=componentes['kpi_unidades_id_prov'].get('valor', 'N/A'),
        fuente=componentes['kpi_unidades_id_prov'].get('fuente', '')
    )
    pdf.layout_manager.smart_spacing(5)
    pdf.grafico(
        componentes['grafico_unidades_por_inst']['img'],
        componentes['grafico_unidades_por_inst']['fuente'],
        auto_layout=True
    )
    # KPIS de infraestructura
    kpis_infraestructura = [
        componentes['kpi_equipos_nacional'],
        componentes['kpi_equipos_regional'],
        componentes['kpi_equipos_provincial']
    ]
    pdf.kpi_grid(kpis_infraestructura, cols=3)
    pdf.layout_manager.smart_spacing(5)

    if componentes.get('grafico_equipos_por_tipo', {}).get('tiene_datos', False):
        pdf.grafico(
            componentes['grafico_equipos_por_tipo']['img'],
            componentes['grafico_equipos_por_tipo']['fuente'],
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(10)


def _generar_seccion_talento(pdf, componentes, link=None):
    """Genera la subsección de talento dentro de Capacidades en I+D."""
    pdf.seccion_title(" 4.3 Talento en acción", link)
    pdf.layout_manager.smart_spacing(5)

    pdf.grafico(
        componentes['grafico_distribucion_investigadores']['img'],
        componentes['grafico_distribucion_investigadores']['fuente'],
        auto_layout=True
    )
    pdf.layout_manager.smart_spacing(5)

    # KPIS de talento
    kpis_talento = [
        componentes['kpi_tasa_pea_provincial'],
        componentes['kpi_tasa_pea_regional'],
        componentes['kpi_tasa_pea_nacional']
    ]
    pdf.kpi_grid(kpis_talento, cols=3)
    pdf.layout_manager.smart_spacing(10)

    if componentes.get('tabla_personas_por_funcion', {}).get('tiene_datos', False):
        pdf.tabla(
            componentes['tabla_personas_por_funcion']['df'],
            title=componentes['tabla_personas_por_funcion'].get('titulo', ''),
            subtitle=componentes['tabla_personas_por_funcion'].get('subtitulo', ''),
            fuente=componentes['tabla_personas_por_funcion'].get('fuente', ''),
            auto_layout=True
        )
    pdf.layout_manager.smart_spacing(5)

    pdf.grafico(
        componentes['grafico_evolucion_investigadores']['img'],
        componentes['grafico_evolucion_investigadores']['fuente'],
        auto_layout=True
    )
    pdf.add_page()


def _generar_seccion_sociedad(pdf, componentes, link=None):
    """Genera la sección de ciencia y sociedad."""
    pdf.seccion_title(" 5. Ciencia y Sociedad", link)
    pdf.layout_manager.smart_spacing(5)

    graficos_sociedad = [
        'grafico_percepcion_temas_prioritarios',
        'grafico_percepcion_calidad_vida'
    ]
    for grafico_key in graficos_sociedad:
        if componentes.get(grafico_key, {}).get('img'):
            pdf.grafico(
                componentes[grafico_key]["img"],
                componentes[grafico_key]["fuente"],
                auto_layout=True
            )
