"""
pdf_exporter.py
Converts a list of image file paths into a single multi-page PDF using img2pdf.
Streams directly to disk – no full PDF in RAM.
Landscape images are automatically rotated left (CCW 90°) to portrait.
"""

import os
import tempfile
from pathlib import Path
from PIL import Image
import img2pdf


def images_to_pdf(
    paths: list,
    output_path: str,
    fit_to_a4: bool = True,
    dpi: int = 300,
    margin_mm: float = 0.0,
) -> str:
    """
    Write images referenced by *paths* to a multi-page PDF.

    Parameters
    ----------
    paths        : list of file-path strings (PNG / JPEG)
    output_path  : destination .pdf path
    fit_to_a4    : scale each page to A4 (210 × 297 mm)
    dpi, margin_mm : kept for API compatibility (unused by img2pdf path)

    Returns
    -------
    str : absolute path of the written PDF
    """
    if not paths:
        raise ValueError("No images provided.")

    output_path = str(Path(output_path).with_suffix(".pdf"))

    tmp_rotated = []   # temp files created for landscape pages
    actual_paths = []

    try:
        for p in paths:
            with Image.open(p) as img:
                w, h = img.size
            if w > h:
                # Landscape → rotate CCW 90°, save to temp
                with Image.open(p) as img:
                    rotated = img.rotate(90, expand=True)
                fd, tmp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                rotated.save(tmp_path, "PNG")
                tmp_rotated.append(tmp_path)
                actual_paths.append(tmp_path)
            else:
                actual_paths.append(str(p))

        with open(output_path, "wb") as f:
            if fit_to_a4:
                a4_layout = img2pdf.get_layout_fun(
                    (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
                )
                img2pdf.convert(actual_paths, layout_fun=a4_layout, outputstream=f)
            else:
                img2pdf.convert(actual_paths, outputstream=f)

    finally:
        for tmp in tmp_rotated:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    return output_path
