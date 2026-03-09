"""
pdf_exporter.py
Converts a list of PIL Images into a single multi-page PDF using ReportLab.
Each image is placed on its own page with DPI-correct sizing.
"""

from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io


def images_to_pdf(
    pil_images: list,
    output_path: str,
    fit_to_a4: bool = True,
    dpi: int = 300,
    margin_mm: float = 0.0,
) -> str:
    """
    Write *pil_images* (list of PIL Image objects) to a multi-page PDF.

    Parameters
    ----------
    pil_images   : list of PIL.Image.Image (RGB or L)
    output_path  : destination .pdf path
    fit_to_a4    : if True, pages use A4 paper size; else natural image size
    dpi          : nominal DPI used when fitting images
    margin_mm    : page margin in mm (applied on all sides)

    Returns
    -------
    str : absolute path of the written PDF
    """
    if not pil_images:
        raise ValueError("No images provided.")

    output_path = str(Path(output_path).with_suffix(".pdf"))

    # points-per-mm
    PTS_PER_MM = 72.0 / 25.4

    c = canvas.Canvas(output_path)

    for idx, img in enumerate(pil_images):
        if img.mode not in ("RGB", "L", "RGBA"):
            img = img.convert("RGB")
        if img.mode == "RGBA":
            # ReportLab doesn't support RGBA directly → flatten on white
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg

        img_w_px, img_h_px = img.size
        img_w_pts = img_w_px * 72.0 / dpi
        img_h_pts = img_h_px * 72.0 / dpi

        if fit_to_a4:
            page_w, page_h = A4           # 595.28 x 841.89 pts
        else:
            page_w, page_h = img_w_pts, img_h_pts

        c.setPageSize((page_w, page_h))

        margin = margin_mm * PTS_PER_MM
        avail_w = page_w - 2 * margin
        avail_h = page_h - 2 * margin

        # Scale image to fit available area while preserving aspect ratio
        scale = min(avail_w / img_w_pts, avail_h / img_h_pts, 1.0)
        draw_w = img_w_pts * scale
        draw_h = img_h_pts * scale

        # Center on page
        x = margin + (avail_w - draw_w) / 2
        y = margin + (avail_h - draw_h) / 2

        # Push image bytes to ReportLab
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG", optimize=False)
        img_byte_arr.seek(0)

        c.drawImage(ImageReader(img_byte_arr), x, y, draw_w, draw_h)
        c.showPage()

    c.save()
    return output_path
