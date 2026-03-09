# scan_to_pdf_debug.py
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
from pathlib import Path

# ---------- PDF export ----------
def image_to_pdf(pil_image, output_path="output.pdf", dpi=300, margin_mm=5.0):
    PTS_PER_MM = 72.0 / 25.4
    c = canvas.Canvas(str(Path(output_path).with_suffix(".pdf")))
    img = pil_image
    if img.mode != "RGB":
        img = img.convert("RGB")
    img_w_px, img_h_px = img.size
    img_w_pts = img_w_px * 72.0 / dpi
    img_h_pts = img_h_px * 72.0 / dpi

    page_w, page_h = A4
    c.setPageSize((page_w, page_h))

    margin = margin_mm * PTS_PER_MM
    avail_w = page_w - 2 * margin
    avail_h = page_h - 2 * margin

    scale = min(avail_w / img_w_pts, avail_h / img_h_pts, 1.0)
    draw_w = img_w_pts * scale
    draw_h = img_h_pts * scale

    x = margin + (avail_w - draw_w)/2
    y = margin + (avail_h - draw_h)/2

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    c.drawImage(ImageReader(img_byte_arr), x, y, draw_w, draw_h)
    c.showPage()
    c.save()
    return str(Path(output_path).absolute())

# ---------- Load ONNX model ----------
session = ort.InferenceSession("UVDoc_grid.onnx", providers=['CPUExecutionProvider'])

def unwarp_with_model(img):
    h_orig, w_orig = img.shape[:2]

    # Preprocess
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(img_rgb, (496, 720))  # model expects 496x720 (WxH)
    blob = resized.astype(np.float32)/255.0
    blob = np.transpose(blob, (2,0,1))[None,...]

    # Run inference
    result = session.run(None, {'image': blob})[0]  # (1,2,45,31)
    grid = np.transpose(result[0], (1,2,0))  # (45,31,2)

    # Upsample to original image size
    grid_up = cv2.resize(grid, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
    map_x = ((grid_up[...,0]+1)/2)*(w_orig-1)
    map_y = ((grid_up[...,1]+1)/2)*(h_orig-1)

    # Remap to flatten
    unwarped = cv2.remap(img,
                         map_x.astype(np.float32),
                         map_y.astype(np.float32),
                         interpolation=cv2.INTER_CUBIC,
                         borderMode=cv2.BORDER_REPLICATE)
    return unwarped

# ---------- Enhancement ----------
def enhance_image(pil_img):
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.3)
    pil_img = ImageEnhance.Brightness(pil_img).enhance(1.1)
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.2)
    return pil_img

# ---------- Detect real contour ----------
def detect_paper_contour(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    edged = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(c, 0.02*cv2.arcLength(c,True), True)
    if len(approx) == 4:
        return approx
    return None

def draw_contour(img, contour, color=(0,0,255), thickness=3):
    img_out = img.copy()
    if contour is not None:
        cv2.polylines(img_out, [contour], isClosed=True, color=color, thickness=thickness)
    return img_out

# ---------- Main ----------
if __name__ == "__main__":
    img_path = "test.jpg"
    img = cv2.imread(img_path)

    # Flatten with model
    unwarped = unwarp_with_model(img)

    # Detect contour on flattened image
    contour = detect_paper_contour(unwarped)
    unwarped_with_contour = draw_contour(unwarped, contour)

    # Save debug image
    cv2.imwrite("debug_unwarped_contour.jpg", unwarped_with_contour)
    cv2.imwrite("unwarped_document.jpg", unwarped)

    # Enhance and save PDF
    pil_img = Image.fromarray(cv2.cvtColor(unwarped, cv2.COLOR_BGR2RGB))
    pil_img = enhance_image(pil_img)
    pdf_path = image_to_pdf(pil_img, "scan_test.pdf")

    print("Saved unwarped image: unwarped_document.jpg")
    print("Saved debug contour: debug_unwarped_contour.jpg")
    print("Saved PDF: scan_test.pdf")