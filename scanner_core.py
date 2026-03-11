"""
scanner_core.py
Primary unwarping: UVDoc deep-learning model (UVDoc_grid.onnx)
Fallback:         classic 4-point perspective transform
Enhancement:      CLAHE grayscale  |  passthrough color
"""

import os
import cv2
import numpy as np
from PIL import Image

try:
    import onnxruntime as ort
    _ORT_AVAILABLE = True
except ImportError:
    _ORT_AVAILABLE = False

import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


_MODEL_PATH = resource_path("UVDoc_grid.onnx")
_ort_session = None


def _get_session():
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


def _unwarp_with_model(bgr: np.ndarray) -> np.ndarray:
    session = _get_session()
    if session is None:
        return None

    h_orig, w_orig = bgr.shape[:2]
    img_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(img_rgb, (496, 720))
    blob = resized.astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))[None, ...]

    result = session.run(None, {"image": blob})[0]
    grid = np.transpose(result[0], (1, 2, 0))

    grid_up = cv2.resize(grid, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
    map_x = ((grid_up[..., 0] + 1) / 2) * (w_orig - 1)
    map_y = ((grid_up[..., 1] + 1) / 2) * (h_orig - 1)

    return cv2.remap(
        bgr,
        map_x.astype(np.float32),
        map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


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
    dst = np.array(
        [[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(
        image, M, (max_w, max_h),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE,
    )


def detect_page(img: np.ndarray):
    h_orig, w_orig = img.shape[:2]
    proc_max = 800
    scale = proc_max / max(h_orig, w_orig)
    small = cv2.resize(
        img, (int(w_orig * scale), int(h_orig * scale)),
        interpolation=cv2.INTER_AREA,
    )
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
    if len(approx) == 4:
        return approx.reshape(4, 2).astype("float32") / scale
    return None


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

MAX_LOAD_SIDE = 2048   # cap input before heavy processing; enough for A4 at ~200 DPI


def unwarp_image(
    path: str,
    force_corners=None,
    rotation_angle: int = 0,
    bypass_flatten: bool = False,
) -> tuple:
    """
    Read, optionally rotate, and flatten/dewarp a document image.
    Returns (unwarped_pil: Image.Image [RGB], method: str).
    """
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Cannot read image: {path}")

    if rotation_angle == 90:
        bgr = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_angle == 180:
        bgr = cv2.rotate(bgr, cv2.ROTATE_180)
    elif rotation_angle in (270, -90):
        bgr = cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Resize down early — makes remap, perspective transform, and PIL conv much faster
    h_r, w_r = bgr.shape[:2]
    if max(h_r, w_r) > MAX_LOAD_SIDE:
        scale = MAX_LOAD_SIDE / max(h_r, w_r)
        bgr = cv2.resize(bgr, (int(w_r * scale), int(h_r * scale)),
                         interpolation=cv2.INTER_AREA)

    if bypass_flatten:
        pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        del bgr
        return pil, "bypass"

    method = "enhance_only"
    unwarped = _unwarp_with_model(bgr)

    if unwarped is not None:
        method = "onnx_cropped"
        crop_corners = force_corners if force_corners is not None else detect_page(unwarped)
        if crop_corners is not None:
            final_cv2 = _four_point_transform(unwarped, crop_corners)
        else:
            final_cv2 = unwarped
            method = "onnx_raw"
        del unwarped
    else:
        corners = force_corners if force_corners is not None else detect_page(bgr)
        if corners is not None:
            method = "perspective"
        final_cv2 = _four_point_transform(bgr, corners) if corners is not None else bgr

    h_f, w_f = final_cv2.shape[:2]
    h_o, w_o = bgr.shape[:2]
    if (h_o * w_o) > 0 and (h_f * w_f) < 0.5 * (h_o * w_o):
        final_cv2 = bgr
        method = "orig"
    elif method == "enhance_only":
        method = "orig"

    pil = Image.fromarray(cv2.cvtColor(final_cv2, cv2.COLOR_BGR2RGB))
    del bgr, final_cv2
    return pil, method


def enhance_image(unwarped_pil: Image.Image, mode: str = "color") -> Image.Image:
    """
    Apply filter to an unwarped RGB PIL image.
    Modes: 'color' (passthrough) | 'grayscale' (CLAHE contrast).
    """
    if mode == "grayscale":
        arr = np.array(unwarped_pil.convert("RGB"))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        gray = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        return Image.fromarray(gray).convert("RGB")
    # 'color': no processing
    return unwarped_pil


def process_image(
    path: str,
    mode: str = "color",
    force_corners=None,
    rotation_angle: int = 0,
    bypass_flatten: bool = False,
) -> tuple:
    """Full pipeline (backward-compat). Returns (orig_pil, processed_pil, method)."""
    pil, method = unwarp_image(path, force_corners, rotation_angle, bypass_flatten)
    processed_pil = enhance_image(pil, mode)
    return pil, processed_pil, method


def model_available() -> bool:
    return _get_session() is not None
