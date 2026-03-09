"""
scanner_core.py  (v3 – UVDoc ONNX)
Primary unwarping: UVDoc deep-learning model (UVDoc_grid.onnx)
Fallback:         classic 4-point perspective transform
Enhancement:      color-preserving CLAHE + PIL sharpness/contrast
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance

# ── Optional ONNX import (graceful if not installed) ──────────────
try:
    import onnxruntime as ort
    _ORT_AVAILABLE = True
except ImportError:
    _ORT_AVAILABLE = False

# ── Model path: same folder as this script ────────────────────────
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UVDoc_grid.onnx")
_ort_session = None   # lazy-loaded


def _get_session():
    """Load the ONNX session once and cache it."""
    global _ort_session
    if _ort_session is None:
        if not _ORT_AVAILABLE:
            return None
        if not os.path.exists(_MODEL_PATH):
            return None
        _ort_session = ort.InferenceSession(
            _MODEL_PATH,
            providers=["CPUExecutionProvider"],
        )
    return _ort_session


# ──────────────────────────────────────────────
# Primary: UVDoc neural-network unwarping
# ──────────────────────────────────────────────

def _unwarp_with_model(bgr: np.ndarray) -> np.ndarray:
    """Dewarp exactly like demo.py"""
    session = _get_session()
    if session is None:
        return None

    h_orig, w_orig = bgr.shape[:2]
    img_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(img_rgb, (496, 720))  # model expects 496x720 (WxH)
    blob = resized.astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))[None, ...]

    result = session.run(None, {'image': blob})[0]  # (1, 2, 45, 31)
    grid = np.transpose(result[0], (1, 2, 0))  # (45, 31, 2)

    # Upsample to original image size exactly as demo.py specifies
    grid_up = cv2.resize(grid, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
    map_x = ((grid_up[..., 0] + 1) / 2) * (w_orig - 1)
    map_y = ((grid_up[..., 1] + 1) / 2) * (h_orig - 1)

    # Remap to flatten on ORIGINAL high-quality image
    unwarped = cv2.remap(
        bgr,
        map_x.astype(np.float32),
        map_y.astype(np.float32),
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return unwarped


# ──────────────────────────────────────────────
# Classic contour-based page detection (demo.py adapted)
# ──────────────────────────────────────────────

def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts)
    tl, tr, br, bl = rect
    max_w = max(int(np.linalg.norm(br - bl)), int(np.linalg.norm(tr - tl)))
    max_h = max(int(np.linalg.norm(tr - br)), int(np.linalg.norm(tl - bl)))

    dst = np.array([[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (max_w, max_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def detect_page(img: np.ndarray):
    """
    Detects paper contour exactly like demo.py, but calculated on a downscaled image
    and mapped back to the high-resolution original to preserve quality.
    """
    h_orig, w_orig = img.shape[:2]
    # Downscale for calculation
    proc_max = 800
    scale = proc_max / max(h_orig, w_orig)
    small = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
        
    c = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
    
    if len(approx) == 4:
        # Map corners back to original high-res image
        pts = approx.reshape(4, 2).astype("float32")
        pts_full = pts / scale
        return pts_full
        
    return None


# ──────────────────────────────────────────────
# Enhancement  (color-preserving)
# ──────────────────────────────────────────────

def _enhance_pil(pil_img: Image.Image,
                 contrast: float = 1.3,
                 brightness: float = 1.1,
                 sharpness: float = 2.0,
                 color_enhance: float = 1.0) -> Image.Image:
    """PIL-based enhancement: contrast → brightness → sharpness → color."""
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
    pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(sharpness)
    if color_enhance != 1.0:
        pil_img = ImageEnhance.Color(pil_img).enhance(color_enhance)
    return pil_img


def _clahe_bgr(bgr: np.ndarray, clip: float = 2.0) -> np.ndarray:
    """CLAHE on LAB luminance channel — neutral color, better contrast."""
    lab             = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch= cv2.split(lab)
    clahe           = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    l_ch            = clahe.apply(l_ch)
    return cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)


# Enhancement mode dispatch
_MODE_PARAMS = {
    #                 contrast  brightness  sharpness  color
    "document":      (1.3,      1.1,        1.5,       1.0),   # matching demo.py + slight sharpness
    "super_sharp":   (1.7,      1.15,       4.0,       1.0),   # cranked up for faint text
    "magic_color":   (1.2,      1.1,        1.2,       1.5),   # focus on color, low sharp
    "grayscale":     (1.3,      1.1,        1.4,       0.0),
    "color":         (1.0,      1.0,        1.0,       1.0),   # pure original
}


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def process_image(
    path: str,
    mode: str = "color",
    force_corners=None,
) -> tuple:
    """
    Full pipeline:
      1. Read at full resolution
      2. Unwarp:
         a. UVDoc ONNX model  (if available)
         b. 4-point perspective transform  (if contour found)
         c. No warp (full image, just enhance)
      3. Enhance (color-preserving)

    Returns
    -------
    (original_pil, processed_pil, method)
      method: "onnx" | "perspective" | "enhance_only"
    """
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Cannot read image: {path}")

    original_pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

    # ── Unwarp & Crop ────────────────────────────────
    method = "enhance_only"

    # 1. Try ONNX model to flatten the page first (maps back to high-res originally)
    unwarped = _unwarp_with_model(bgr)
    
    if unwarped is not None:
        method = "onnx_cropped"
        # 2. Find exact crop boundaries on the flattened image (demo.py flow)
        if force_corners is not None:
            crop_corners = force_corners
        else:
            crop_corners = detect_page(unwarped)
            
        # 3. Crop tightly to the detected page boundaries
        if crop_corners is not None:
            final_image = _four_point_transform(unwarped, crop_corners)
        else:
            final_image = unwarped
            method = "onnx_raw"
            
    else:
        # Fallback: No ONNX model -> pure perspective warp
        if force_corners is not None:
            corners = force_corners
            method = "perspective"
        else:
            corners = detect_page(bgr)
            if corners is not None:
                method = "perspective"

        final_image = _four_point_transform(bgr, corners) if corners is not None else bgr

    # ── CLAHE for better contrast before PIL enhancement ──────────
    if mode == "bw_strict":
        # Pure Black & White (Adaptive Threshold)
        gray = cv2.cvtColor(final_image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        bw_img = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21, C=10
        )
        processed = Image.fromarray(cv2.cvtColor(bw_img, cv2.COLOR_GRAY2RGB))
    else:
        # Pre-process based on mode
        if mode in ["super_sharp", "document", "magic_color", "grayscale"]:
            # Light denoising to prevent grain before sharpening
            final_image = cv2.fastNlMeansDenoisingColored(final_image, None, 3, 3, 7, 21)
            # Mild CLAHE (clip=1.2 instead of 2.0)
            unwarped_bgr = _clahe_bgr(final_image, clip=1.2)
        else:
            unwarped_bgr = final_image  # 'color' untouched

        pil_unwarped = Image.fromarray(cv2.cvtColor(unwarped_bgr, cv2.COLOR_BGR2RGB))
        
        params = _MODE_PARAMS.get(mode, _MODE_PARAMS["document"])
        if mode == "grayscale":
            pil_unwarped = pil_unwarped.convert("L").convert("RGB")
            
        processed = _enhance_pil(pil_unwarped, *params)

    return original_pil, processed, method


def model_available() -> bool:
    """True if UVDoc_grid.onnx is present and onnxruntime is installed."""
    return _get_session() is not None


def get_page_corners(path: str):
    """Return the 4 detected corners for the image, or None."""
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    return detect_page(bgr)
