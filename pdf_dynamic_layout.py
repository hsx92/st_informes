"""
Gestor de layout dinámico para PDFs de informes provinciales.
Maneja espaciado, saltos de página y posicionamiento adaptativo.
"""

from fpdf import FPDF
import pandas as pd
from PIL import Image
from logging_config import get_logger

logger = get_logger(__name__)


class PDFLayoutManager:
    """Gestiona el layout dinámico del PDF."""
    
    def __init__(self, pdf: FPDF):
        self.pdf = pdf
        self.page_height = 297  # A4
        self.page_width = 210   # A4
        self.margin_top = 10
        self.margin_bottom = 15
        self.margin_left = 10
        self.margin_right = 10
        self.usable_height = self.page_height - self.margin_top - self.margin_bottom
        self.footer_height = 10
        
    def get_remaining_space(self) -> float:
        """Calcula el espacio restante en la página actual."""
        current_y = self.pdf.get_y()
        return self.page_height - current_y - self.footer_height - self.margin_bottom
    
    def needs_new_page(self, required_height: float) -> bool:
        """Determina si se necesita una nueva página."""
        return self.get_remaining_space() < required_height

    def add_page_if_needed(self, required_height: float, force_new: bool = False) -> bool:
        """Añade una nueva página si es necesario."""
        if self.needs_new_page(required_height) or force_new:
            self.pdf.add_page()
            logger.debug(f"Nueva página añadida. Espacio requerido: {required_height}mm")
            return True
        return False
    
    def calculate_image_height(self, image_path: str, target_width: float) -> float:
        """Calcula la altura de una imagen dado un ancho objetivo."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = height / width
                return target_width * aspect_ratio
        except Exception as e:
            logger.warning(f"No se pudo calcular altura de imagen {image_path}: {e}")
            return 100  # Altura por defecto
    
    def calculate_table_height(self, df: pd.DataFrame, row_height: float = 9) -> float:
        """Estima la altura de una tabla basándose en el número de filas."""
        if df is None or df.empty:
            return 0
        
        # Altura base (headers, bordes, etc.)
        base_height = 12
        
        # Altura de las filas
        num_rows = len(df)
        content_height = num_rows * row_height
        
        return base_height + content_height
    
    def calculate_kpi_block_height(self, num_kpis: int, columns: int = 2) -> float:
        """Calcula la altura necesaria para un bloque de KPIs."""
        rows = (num_kpis + columns - 1) // columns
        kpi_height = 40  # Altura de cada KPI
        spacing = 5
        return rows * kpi_height + (rows - 1) * spacing
    
    def smart_spacing(self, default_space: float = 10) -> None:
        """Añade espaciado inteligente basado en el contenido siguiente."""
        remaining = self.get_remaining_space()
        
        # Si queda poco espacio, mejor pasar a la siguiente página
        if remaining < default_space * 2:
            self.pdf.add_page()
        else:
            self.pdf.ln(min(default_space, remaining * 0.1))
