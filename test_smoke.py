"""
test_smoke.py
Headless smoke test for scanner_core and pdf_exporter.
Run from project root: python test_smoke.py
"""

import sys
import os
import traceback
import numpy as np
from pathlib import Path

PASS = "  [PASS]"
FAIL = "  [FAIL]"

results = []

# ─────────────────────────────────────────────
# Create a synthetic document image for testing
# ─────────────────────────────────────────────
def make_test_image(path: str):
    """Create a white A4-like image with black text lines (no external file needed)."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (800, 1100), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Simulate document background
    draw.rectangle([40, 40, 760, 1060], fill=(255, 255, 255))
    # Draw fake text lines
    for y in range(100, 900, 35):
        draw.rectangle([80, y, 720, y+18], fill=(30, 30, 30))
    img.save(path, "JPEG")

# ─────────────────────────────────────────────
# Test 1: scanner_core imports
# ─────────────────────────────────────────────
try:
    from scanner_core import process_image, detect_page
    results.append((PASS, "Import scanner_core"))
except Exception as e:
    results.append((FAIL, f"Import scanner_core: {e}"))
    print("\n".join(f"{r[0]} {r[1]}" for r in results))
    sys.exit(1)

# ─────────────────────────────────────────────
# Test 2: pdf_exporter imports
# ─────────────────────────────────────────────
try:
    from pdf_exporter import images_to_pdf
    results.append((PASS, "Import pdf_exporter"))
except Exception as e:
    results.append((FAIL, f"Import pdf_exporter: {e}"))

# ─────────────────────────────────────────────
# Test 3: Create synthetic test image
# ─────────────────────────────────────────────
import tempfile
_tmp_dir = tempfile.gettempdir()
TEST_IMG = str(Path(_tmp_dir) / "test_doc.jpg")
try:
    make_test_image(TEST_IMG)
    assert Path(TEST_IMG).exists()
    results.append((PASS, "Create synthetic test image"))
except Exception as e:
    results.append((FAIL, f"Create test image: {e}"))
    TEST_IMG = None

# ─────────────────────────────────────────────
# Test 4: process_image – all modes
# ─────────────────────────────────────────────
if TEST_IMG:
    pil_images_for_pdf = []
    for mode in ["auto", "grayscale", "color"]:
        try:
            orig, proc = process_image(TEST_IMG, mode=mode)
            assert orig is not None and proc is not None
            results.append((PASS, f"process_image mode='{mode}'"))
            if mode == "auto":
                pil_images_for_pdf.append(proc)
        except Exception as e:
            results.append((FAIL, f"process_image mode='{mode}': {e}"))
            traceback.print_exc()

    # ─────────────────────────────────────────
    # Test 5: PDF export
    # ─────────────────────────────────────────
    if pil_images_for_pdf:
        OUT_PDF = str(Path(tempfile.gettempdir()) / "test_output.pdf")
        try:
            # Add 3 pages
            pil_images_for_pdf *= 3
            pdf_path = images_to_pdf(pil_images_for_pdf, OUT_PDF, fit_to_a4=True)
            size = Path(pdf_path).stat().st_size
            assert size > 1000, f"PDF too small: {size} bytes"
            results.append((PASS, f"Export PDF ({size:,} bytes) → {pdf_path}"))
        except Exception as e:
            results.append((FAIL, f"Export PDF: {e}"))
            traceback.print_exc()

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print()
print("=" * 48)
print("  SMOKE TEST RESULTS")
print("=" * 48)
for status, msg in results:
    print(f"{status}  {msg}")
print("=" * 48)

failed = [r for r in results if r[0] == FAIL]
if failed:
    print(f"\n❌  {len(failed)} test(s) FAILED.")
    sys.exit(1)
else:
    print(f"\n✅  All {len(results)} tests PASSED.")
    sys.exit(0)
