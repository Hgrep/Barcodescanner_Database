import os
import tempfile
from barcode import Code128
from barcode.writer import ImageWriter

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# CR80 card size (credit card)
CR80_WIDTH_MM = 85.6
CR80_HEIGHT_MM = 53.98

PAGE_WIDTH, PAGE_HEIGHT = A4


class LibraryCardPrinter:
    """
    Generates Code 128 library cards as a double-sided A4 PDF.
    """

    def __init__(self, output_path):
        self.output_path = output_path

        # Convert to points
        self.card_w = CR80_WIDTH_MM * mm
        self.card_h = CR80_HEIGHT_MM * mm

        # Layout: 2 columns x 5 rows = 10 cards per page
        self.cols = 2
        self.rows = 5

        self.margin_x = 10 * mm
        self.margin_y = 10 * mm
        self.h_gap = 5 * mm
        self.v_gap = 5 * mm

        self._register_fonts()

    # ---------------- BARCODE ----------------

    def _generate_barcode_image(self, text):
        """
        Generate a Code 128 barcode image for the given text.
        Returns a PIL image path.
        """
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        code = Code128(
            text,
            writer=ImageWriter(),
        )

        code.save(
            path.replace(".png", ""),
            {
                "module_height": 10.0,
                "module_width": 0.25,
                "quiet_zone": 2,
                "font_size": 10,
                "text_distance": 2,
                "write_text": False,
            }
        )

        return path

    # ---------------- LAYOUT ----------------

    def _card_positions(self):
        """
        Yield (x, y) positions for each card slot on a page.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                x = self.margin_x + col * (self.card_w + self.h_gap)
                y = PAGE_HEIGHT - self.margin_y - (row + 1) * self.card_h - row * self.v_gap
                yield x, y

    # ---------------- DRAWING ----------------

    def _draw_front(self, c, name, barcode_path, x, y):
        """
        Front side: Name + barcode
        """
        c.rect(x, y, self.card_w, self.card_h)

        # Name
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(
            x + self.card_w / 2,
            y + self.card_h - 10 * mm,
            name
        )

        # Barcode
        img = ImageReader(barcode_path)
        img_w = self.card_w - 20 * mm
        img_h = 20 * mm

        c.drawImage(
            img,
            x + 10 * mm,
            y + (self.card_h / 2) - (img_h / 2),
            width=img_w,
            height=img_h,
            preserveAspectRatio=True,
            mask="auto"
        )

    def _draw_back(self, c, name, x, y):
        """
        Back side: centered school logo branding.
        """
        c.rect(x, y, self.card_w, self.card_h)

        center_x = x + self.card_w / 2
        center_y = y + self.card_h / 2

        # Font sizes
        title_size = 18
        sub_size = title_size / 3

        # Vertical spacing
        line_gap = 3 * mm
        text_gap = 2 * mm

        # --- Top text ---
        c.setFont(self.font_main, title_size)
        c.setFillColorRGB(0, 0, 0)

        c.drawCentredString(
            center_x,
            center_y + sub_size + line_gap,
        )

        # --- Divider line ---
        line_width = self.card_w * 0.7
        c.setLineWidth(0.5)
        c.line(
            center_x - line_width / 2,
            center_y,
            center_x + line_width / 2,
            center_y
        )

        # --- Address text ---
        c.setFont(self.font_sub, sub_size)
        c.setFillColorRGB(1, 0, 0)

        c.drawCentredString(
            center_x,
            center_y - text_gap - sub_size,
        )

    # ---------------- PUBLIC API ----------------

    def generate_pdf(self, account_names):
        """
        Generate a double-sided A4 PDF for the given account names.
        """
        c = canvas.Canvas(self.output_path, pagesize=A4)

        barcodes = [
            (name, self._generate_barcode_image(name))
            for name in account_names
        ]

        # -------- FRONT PAGES --------
        index = 0
        while index < len(barcodes):
            for (x, y), item in zip(self._card_positions(), barcodes[index:]):
                name, barcode_path = item
                self._draw_front(c, name, barcode_path, x, y)
            c.showPage()
            index += self.cols * self.rows

        # -------- BACK PAGES --------
        index = 0
        while index < len(account_names):
            grid = self._card_positions_grid()

            page_names = account_names[index:index + self.cols * self.rows]
            name_idx = 0

            for row in grid:
                mirrored_row = list(reversed(row))  # mirror columns only
                for (x, y) in mirrored_row:
                    if name_idx >= len(page_names):
                        break
                    name = page_names[name_idx]
                    self._draw_back(c, name, x, y)
                    name_idx += 1

            c.showPage()
            index += self.cols * self.rows

        c.save()
    
    def _card_positions_grid(self):
        """
        Return positions as a 2D list: rows -> columns.
        """
        grid = []
        for row in range(self.rows):
            row_positions = []
            for col in range(self.cols):
                x = self.margin_x + col * (self.card_w + self.h_gap)
                y = (
                    PAGE_HEIGHT
                    - self.margin_y
                    - (row + 1) * self.card_h
                    - row * self.v_gap
                )
                row_positions.append((x, y))
            grid.append(row_positions)
        return grid
    
    def _register_fonts(self):
        """
        Register Franklin Gothic if available, otherwise fall back.
        """
        self.font_main = "Helvetica-Bold"
        self.font_sub = "Helvetica-Bold"

        font_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "assets",
            "fonts",
            "FranklinGothicDemiCond.ttf"
        )

        font_path = os.path.abspath(font_path)

        if os.path.exists(font_path):
            pdfmetrics.registerFont(
                TTFont("FranklinGothicDemiCond", font_path)
            )
            self.font_main = "FranklinGothicDemiCond"
            self.font_sub = "FranklinGothicDemiCond"