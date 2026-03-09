"""
main_app.py
Document Scanner – Windows Desktop App
Tkinter-based GUI: import images, preview processing, manage pages, export PDF.
"""

import os
import sys
import threading
import tempfile
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import numpy as np
import tkinter.simpledialog as simpledialog

# Try to enable drag-and-drop
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

from scanner_core import unwarp_image, enhance_image, model_available
from pdf_exporter import images_to_pdf
from drive_service import DriveService
import queue

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ───────────────────────────────────────────
# Constants / Theme (Warm Cat Theme)
# ───────────────────────────────────────────

BG_DARK     = "#fffbed"   # Light cream (overall)
BG_PANEL    = "#ffffff"   # White (preview area / sidebar)
BG_CARD     = "#fff9f1"   # Very light peach (galleries)
ACCENT      = "#ffa57d"   # Warm peach (buttons)
ACCENT_HOVER = "#ff9a61"  # Brighter peach for hover
ACCENT2     = "#ffa57d"   # Selection
TEXT_MAIN   = "#6E5A4D"   # Mocha (titles/labels)
TEXT_DIM    = "#A67C5A"   # Soft mocha (hints)
TEXT_WHITE  = "#ffffff"   # White (on accent buttons)

THUMB_W, THUMB_H = 110, 145
PREVIEW_MAX = 480

# ───────────────────────────────────────────
# Translations (VI / EN)
# ───────────────────────────────────────────
TRANSLATIONS = {
    "VI": {
        # Toolbar buttons
        "add_images":    "Thêm ảnh",
        "import_drive":  "Nhập Drive",
        "clear_all":     "Xóa tất cả",
        "export_pdf":    "Xuất PDF",
        "logout":        "Đăng xuất",
        # Mode
        "mode_label":    "Chế độ:",
        "mode_document": "Tài liệu",
        "mode_super":    "Siêu nét",
        "mode_magic":    "Sinh động",
        "mode_bw":       "Đen trắng",
        "mode_gray":     "Xám",
        "mode_color":    "Tự nhiên",
        "fit_a4":        "Khổ A4",
        # Sidebar / Preview
        "page_list":     "Danh sách trang",
        "original":      "Ảnh gốc",
        "processed":     "Sau xử lý",
        "no_image":      "Chưa có ảnh",
        # Status / page count
        "ready":         "Sẵn sàng",
        "pages":         "{n} trang",
        "page_n":        "Trang {n}",
        "delete":        " Xóa",
        # Detection badges
        "method_onnx":   "🧠 AI",
        "method_persp":  "✅ Khung",
        "method_orig":   "⚠️ Ảnh gốc",
        # Dialogs
        "select_btn":    "Chọn",
        "cancel_btn":    "Hủy",
        # Confirmations
        "clear_confirm_title": "Xóa tất cả",
        "clear_confirm_msg":   "Xóa toàn bộ danh sách trang?",
        # Processing
        "processing_n":      "Đang xử lý {n} ảnh…",
        "processing_img":    "Đang xử lý ({i}/{n}): {name}…",
        "loaded_n":          "Đã tải {n} trang",
        "updating_filter":   "Đang cập nhật bộ lọc ({mode})…",
        "updating_i":        "Đang cập nhật ({i}/{n}): {name}…",
        "filter_updated":    "Đã cập nhật chế độ xử lý",
        "cleared_all":       "Đã xóa tất cả",
        # PDF
        "no_pages_title":    "Chưa có ảnh",
        "no_pages_msg":      "Hãy thêm ít nhất một ảnh trước khi xuất PDF.",
        "pdf_save_title":    "Lưu PDF",
        "pdf_file":          "tai_lieu_scan.pdf",
        "pdf_exporting":     "Đang xuất PDF…",
        "pdf_exported":      "Đã xuất: {name}",
        "pdf_success_title": "Xuất thành công",
        "pdf_success_msg":   "PDF đã lưu tại:\n{path}\n\nMở file ngay?",
        "err_pdf":           "Lỗi xuất PDF",
        "err_pdf_msg":       "Không thể xuất PDF:\n{err}",
        "err_pdf_status":    "Lỗi xuất PDF",
        # Image loading errors
        "err_process":       "Lỗi xử lý ảnh",
        "err_process_msg":   "Không thể xử lý:\n{file}\n\n{err}",
        # Drive
        "drive_import_title": "Nhập từ Drive",
        "drive_prompt":       "Nhập tên thư mục trên Google Drive:",
        "drive_searching":    "Đang tìm thư mục trên Drive: {name}…",
        "drive_not_found":    "Không tìm thấy thư mục '{name}' trên Drive",
        "drive_multi_title":  "Nhiều thư mục trùng tên",
        "drive_multi_msg":    "Chọn đúng thư mục bạn muốn tải:",
        "drive_no_images":    "Thư mục không có ảnh nào.",
        "drive_downloading":  "Đang tải từ Drive ({i}/{n}): {name}…",
        "drive_cached":       "Sử dụng bản tạm ({i}/{n}): {name}…",
        "drive_processing":   "Đang xử lý Drive ({i}/{n})…",
        "drive_failed":       "Kết nối Drive thất bại:\n{err}",
        "err_drive":          "Lỗi Drive",
        # Logout
        "logout_success_title": "Đăng xuất",
        "logout_success_msg":   "Đã đăng xuất khỏi Google Drive.\nLần nhập tiếp theo sẽ yêu cầu đăng nhập lại.",
        "logout_no_login_title": "Thông báo",
        "logout_no_login":      "Chưa đăng nhập Google Drive.",
        "logout_err_title":     "Lỗi",
        "logout_err":           "Không thể đăng xuất:\n{err}",
        # Add images dialog
        "add_title":   "Chọn ảnh tài liệu",
        "add_types":   "Ảnh",
        "all_files":   "Tất cả",
    },
    "EN": {
        # Toolbar buttons
        "add_images":    "Add Images",
        "import_drive":  "Import Drive",
        "clear_all":     "Clear All",
        "export_pdf":    "Export PDF",
        "logout":        "Log Out",
        # Mode
        "mode_label":    "Mode:",
        "mode_document": "Document",
        "mode_super":    "Ultra Sharp",
        "mode_magic":    "Vivid",
        "mode_bw":       "B&W",
        "mode_gray":     "Grayscale",
        "mode_color":    "Natural",
        "fit_a4":        "A4 Size",
        # Sidebar / Preview
        "page_list":     "Page List",
        "original":      "Original",
        "processed":     "Processed",
        "no_image":      "No image",
        # Status / page count
        "ready":         "Ready",
        "pages":         "{n} pages",
        "page_n":        "Page {n}",
        "delete":        " Delete",
        # Detection badges
        "method_onnx":   "🧠 AI",
        "method_persp":  "✅ Frame",
        "method_orig":   "⚠️ Original",
        # Dialogs
        "select_btn":    "Select",
        "cancel_btn":    "Cancel",
        # Confirmations
        "clear_confirm_title": "Clear All",
        "clear_confirm_msg":   "Delete all pages from the list?",
        # Processing
        "processing_n":      "Processing {n} images…",
        "processing_img":    "Processing ({i}/{n}): {name}…",
        "loaded_n":          "{n} pages loaded",
        "updating_filter":   "Updating filter ({mode})…",
        "updating_i":        "Updating ({i}/{n}): {name}…",
        "filter_updated":    "Filter mode updated",
        "cleared_all":       "Cleared all",
        # PDF
        "no_pages_title":    "No images",
        "no_pages_msg":      "Please add at least one image before exporting PDF.",
        "pdf_save_title":    "Save PDF",
        "pdf_file":          "scanned_document.pdf",
        "pdf_exporting":     "Exporting PDF…",
        "pdf_exported":      "Exported: {name}",
        "pdf_success_title": "Export successful",
        "pdf_success_msg":   "PDF saved at:\n{path}\n\nOpen now?",
        "err_pdf":           "PDF export error",
        "err_pdf_msg":       "Cannot export PDF:\n{err}",
        "err_pdf_status":    "PDF export error",
        # Image loading errors
        "err_process":       "Image processing error",
        "err_process_msg":   "Cannot process:\n{file}\n\n{err}",
        # Drive
        "drive_import_title": "Import from Drive",
        "drive_prompt":       "Enter Google Drive folder name:",
        "drive_searching":    "Searching Drive folder: {name}…",
        "drive_not_found":    "Folder '{name}' not found on Drive",
        "drive_multi_title":  "Multiple folders found",
        "drive_multi_msg":    "Select the correct folder:",
        "drive_no_images":    "No images found in folder.",
        "drive_downloading":  "Downloading from Drive ({i}/{n}): {name}…",
        "drive_cached":       "Using cached ({i}/{n}): {name}…",
        "drive_processing":   "Processing Drive image ({i}/{n})…",
        "drive_failed":       "Drive connection failed:\n{err}",
        "err_drive":          "Drive error",
        # Logout
        "logout_success_title": "Logged out",
        "logout_success_msg":   "Logged out of Google Drive.\nNext import will require login again.",
        "logout_no_login_title": "Info",
        "logout_no_login":      "Not logged in to Google Drive.",
        "logout_err_title":     "Error",
        "logout_err":           "Cannot log out:\n{err}",
        # Add images dialog
        "add_title":   "Select document images",
        "add_types":   "Images",
        "all_files":   "All files",
    },
}

# ───────────────────────────────────────────
# Custom Radio Button Dialog
# ───────────────────────────────────────────
class RadioSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt, options, ok_text="Chọn", cancel_text="Hủy"):
        self.prompt = prompt
        self.options = options
        self.result = None
        self._ok_text = ok_text
        self._cancel_text = cancel_text
        super().__init__(parent, title)

    def body(self, master):
        master.configure(bg=BG_PANEL)
        tk.Label(master, text=self.prompt, justify="left", wraplength=450, 
                 bg=BG_PANEL, fg=TEXT_MAIN, font=("Segoe UI", 10, "bold")).pack(padx=10, pady=10)
        
        self.var = tk.IntVar(value=0)
        frame = tk.Frame(master, bg=BG_PANEL)
        frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        for i, opt in enumerate(self.options):
            rb = tk.Radiobutton(frame, text=opt, variable=self.var, value=i, 
                                anchor="w", bg=BG_PANEL, fg=TEXT_MAIN,
                                activebackground=BG_PANEL, activeforeground=ACCENT,
                                selectcolor=BG_PANEL, font=("Segoe UI", 9))
            rb.pack(fill="x", pady=2)
        return frame

    def apply(self):
        self.result = self.var.get()

    def buttonbox(self):
        # Professional buttons
        box = tk.Frame(self)
        tk.Button(box, text=self._ok_text, width=10, command=self.ok, default="active",
                  bg=ACCENT, fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5, pady=5)
        tk.Button(box, text=self._cancel_text, width=10, command=self.cancel,
                  bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9)).pack(side="left", padx=5, pady=5)
        box.pack()



# ───────────────────────────────────────────
# App class
# ───────────────────────────────────────────

class DocumentScannerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CDScan")
        self.root.state("zoomed")  # start maximized
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        # Set window icon
        try:
            icon_path = resource_path(os.path.join("static", "cat_icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not set window icon: {e}")

        self._pages: list[dict] = []          # {"path", "orig_pil", "proc_pil", "thumb_photo", "label_widget"}
        self._selected_idx: int = -1
        self._mode_var    = tk.StringVar(value="color")
        self._status_var  = tk.StringVar(value="Sẵn sàng")  # updated by _apply_lang
        self._fit_a4_var  = tk.BooleanVar(value=True)
        self._processing  = False
        self._cat_x = 2
        self._cat_dir = 1
        self._animating = False
        self._overlay_active = False
        self._overlay_angle = 0

        # Create hidden temp directory in system temp folder
        self._temp_dir = tempfile.mkdtemp(prefix="CDScan_")

        self._lang = "VI"  # default language

        self._setup_styles()
        self._load_icons()
        self._build_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        # Clean up hidden temp directory
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
        self.root.destroy()

    def _t(self, key):
        """Return translated string for current language."""
        return TRANSLATIONS[self._lang].get(key, TRANSLATIONS["VI"].get(key, key))

    # ── Icons ──────────────────────────────

    def _load_icons(self):
        """Load and resize PNG icons from static directory."""
        self._icons = {}
        static_dir = Path(resource_path("static"))
        
        icon_mappings = {
            "logo":      "cat_code.png",
            "add":       "cat_symbol.png",
            "pdf":       "cat_pdf.png",
            "clear":     "cat_x.png",
            "del":       "cat_x.png",
            "drive":     "drive.png",
            "progress":  "cat_fly.png",
            "round":     "cat_round.png",
            "logout":    "cat_exit.png",
            "flag_vi":   "vi.png",
            "flag_en":   "en.png",
        }
        
        for key, filename in icon_mappings.items():
            path = static_dir / filename
            if path.exists():
                try:
                    img = Image.open(path)
                    if key in ("flag_vi", "flag_en"):
                        size = 28
                    elif key == "logo":
                        size = 36
                    elif key == "del":
                        size = 18
                    size = 28 if key != "logo" else 36
                    if key == "del": size = 18
                    if key in ("flag_vi", "flag_en"): size = 28
                    img.thumbnail((size, size), Image.LANCZOS)
                    self._icons[key] = ImageTk.PhotoImage(img)
                    
                    if key == "progress":
                        # Also create a flipped version for flying back
                        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
                        self._icons["progress_flipped"] = ImageTk.PhotoImage(flipped)
                    
                    if key == "round":
                        # Large rotating cat in the center
                        img = img.copy().convert("RGBA")
                        img.thumbnail((512, 512), Image.LANCZOS)
                        self._icons["round_pil"] = img
                except Exception:
                    self._icons[key] = None
            else:
                self._icons[key] = None

    # ── Styles ──────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame",        background=BG_DARK)
        style.configure("Panel.TFrame",  background=BG_PANEL)
        style.configure("Card.TFrame",   background=BG_CARD)
        style.configure("TLabel",        background=BG_DARK,  foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("Title.TLabel",  background=BG_DARK,  foreground=TEXT_MAIN, font=("Segoe UI", 13, "bold"))
        style.configure("Dim.TLabel",    background=BG_PANEL, foreground=TEXT_DIM,   font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=BG_DARK,  foreground=TEXT_DIM,    font=("Segoe UI", 9, "italic"))

        # Radio / Check
        style.configure("TRadiobutton", background=BG_PANEL,
                        foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=BG_PANEL,
                        foreground=TEXT_MAIN, font=("Segoe UI", 10))
        
        # Scrollbar
        style.configure("Vertical.TScrollbar", background=BG_CARD,
                        troughcolor=BG_PANEL, borderwidth=0, arrowsize=12)
        style.configure("TProgressbar", background=ACCENT, troughcolor=BG_PANEL)

    def _create_cat_button(self, parent, text, icon_key, command):
        """Helper to create a cat-style button with icon and hover."""
        btn = tk.Button(
            parent, text=f" {text}", image=self._icons.get(icon_key),
            compound="left", command=command,
            bg=ACCENT, fg=TEXT_WHITE, font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, padx=10, pady=5, cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=ACCENT))
        return btn

    # ── Build UI ────────────────────────────

    def _build_ui(self):
        # ─ Top toolbar (White background)
        toolbar = tk.Frame(self.root, bg=BG_PANEL, pady=8, padx=12)
        toolbar.pack(fill="x", side="top")

        # Logo + Title
        logo_lbl = tk.Label(toolbar, image=self._icons.get("logo"), bg=BG_PANEL)
        logo_lbl.pack(side="left", padx=(0, 8))
        
        ttk.Label(toolbar, text="CDScan", style="Title.TLabel", background=BG_PANEL).pack(side="left", padx=(0, 20))

        # Buttons with custom icons
        self._btn_add = self._create_cat_button(toolbar, self._t("add_images"), "add", self._add_images)
        self._btn_add.pack(side="left", padx=5)
        self._btn_drive = self._create_cat_button(toolbar, self._t("import_drive"), "drive", self._import_from_drive)
        self._btn_drive.pack(side="left", padx=5)
        self._btn_clear = self._create_cat_button(toolbar, self._t("clear_all"), "clear", self._clear_all)
        self._btn_clear.pack(side="left", padx=5)
        self._btn_pdf = self._create_cat_button(toolbar, self._t("export_pdf"), "pdf", self._export_pdf)
        self._btn_pdf.pack(side="left", padx=5)

        # Language toggle button – toolbar right side
        self._btn_lang = tk.Button(
            toolbar, image=self._icons.get("flag_en"),
            bg=BG_PANEL, activebackground=BG_PANEL,
            relief="flat", bd=0, cursor="hand2",
            command=self._toggle_lang
        )
        self._btn_lang.pack(side="right", padx=6)

        # Drive logout button (right side) – uses cat_exit icon
        self._btn_logout = tk.Button(
            toolbar, text=self._t("logout"),
            image=self._icons.get("logout"), compound="left",
            fg="#e74c3c", bg=BG_PANEL,
            activebackground=BG_PANEL, activeforeground="#c0392b",
            font=("Segoe UI", 8, "bold"), borderwidth=0, cursor="hand2",
            command=self._logout_drive, padx=6
        )
        self._btn_logout.pack(side="right", padx=10)

        # Separator
        tk.Frame(toolbar, width=1, bg=BG_DARK).pack(side="left", fill="y", padx=15, pady=5)

        # Mode selector
        self._lbl_mode = ttk.Label(toolbar, text=self._t("mode_label"), background=BG_PANEL, foreground=TEXT_DIM)
        self._lbl_mode.pack(side="left")
        
        mode_frame = tk.Frame(toolbar, bg=BG_PANEL)
        mode_frame.pack(side="left", padx=4)
        
        _mode_defs = [
            ("document",    "📄", "mode_document"),
            ("super_sharp", "⚡", "mode_super"),
            ("magic_color", "🪄", "mode_magic"),
            ("bw_strict",   "🖤", "mode_bw"),
            ("grayscale",   "🩶", "mode_gray"),
            ("color",       "🎨", "mode_color"),
        ]
        self._mode_radios = []
        for val, icon, lbl_key in _mode_defs:
            rb = ttk.Radiobutton(mode_frame, text=f"{icon} {self._t(lbl_key)}",
                                 variable=self._mode_var, value=val,
                                 command=self._on_mode_change)
            rb.pack(side="left", padx=2)
            self._mode_radios.append((rb, val, lbl_key, icon))

        tk.Frame(toolbar, width=1, bg=BG_DARK).pack(side="left", fill="y", padx=15, pady=5)
        self._chk_a4 = ttk.Checkbutton(toolbar, text=self._t("fit_a4"),
                                        variable=self._fit_a4_var, style="TCheckbutton")
        self._chk_a4.pack(side="left")

        # ─ Main area
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # Left: page list
        left = ttk.Frame(main, style="Panel.TFrame", width=150)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self._lbl_pagelist = ttk.Label(left, text=self._t("page_list"),
                  background=BG_PANEL, foreground=TEXT_DIM,
                  font=("Segoe UI", 9, "bold"))
        self._lbl_pagelist.pack(pady=(10,4))

        list_container = tk.Frame(left, bg=BG_PANEL)
        list_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_container, style="Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")

        self._page_canvas = tk.Canvas(list_container, bg=BG_PANEL,
                                       highlightthickness=0, yscrollcommand=scrollbar.set)
        self._page_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._page_canvas.yview)

        self._thumb_frame = tk.Frame(self._page_canvas, bg=BG_PANEL)
        self._page_canvas.create_window((0, 0), window=self._thumb_frame, anchor="nw")
        self._thumb_frame.bind("<Configure>",
            lambda e: self._page_canvas.configure(scrollregion=self._page_canvas.bbox("all")))
            
        # Bind MouseWheel to scroll the canvas
        self._page_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Center: preview
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self._lbl_orig_title = ttk.Label(center, text=self._t("original"), style="Title.TLabel")
        self._lbl_orig_title.grid(row=0, column=0, sticky="w", padx=4)
        self._lbl_proc_title = ttk.Label(center, text=self._t("processed"), style="Title.TLabel")
        self._lbl_proc_title.grid(row=0, column=1, sticky="w", padx=4)

        self._orig_label = tk.Label(center, bg=BG_CARD, width=PREVIEW_MAX, height=PREVIEW_MAX,
                                     text=self._t("no_image"), fg=TEXT_DIM, font=("Segoe UI", 11))
        self._orig_label.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

        self._proc_label = tk.Label(center, bg=BG_CARD, width=PREVIEW_MAX, height=PREVIEW_MAX,
                                     text=self._t("no_image"), fg=TEXT_DIM, font=("Segoe UI", 11))
        self._proc_label.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")

        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=1)
        center.rowconfigure(1, weight=1)

        # ─ Status bar
        status_bar = tk.Frame(self.root, bg=BG_PANEL, height=40)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        # Cat fly container (The only progress indicator now)
        self._cat_runway = tk.Frame(status_bar, bg=BG_PANEL, width=160, height=35,
                                     highlightthickness=1, highlightbackground=ACCENT)
        self._cat_runway.pack(side="right", padx=10)
        self._cat_runway.pack_propagate(False)
        
        self._progress_img = tk.Label(self._cat_runway, image=self._icons.get("progress"), bg=BG_PANEL)
        self._progress_img.place(x=2, y=3)

        ttk.Label(status_bar, textvariable=self._status_var, style="Status.TLabel",
                  background=BG_PANEL).pack(side="left", padx=10)

        page_count_frame = ttk.Frame(status_bar, style="Panel.TFrame")
        page_count_frame.pack(side="right", padx=16)
        self._page_count_var = tk.StringVar(value="0 trang")
        ttk.Label(page_count_frame, textvariable=self._page_count_var,
                  background=BG_PANEL, foreground=TEXT_DIM,
                  font=("Segoe UI", 9)).pack()

        # Overlay for rotating cat (Floating label directly on root)
        self._overlay_win = None
        self._overlay_cat_lbl = None
        self._overlay_msg_lbl = None

    # ── Language support ─────────────────────

    def _toggle_lang(self):
        """Switch between VI and EN."""
        self._lang = "EN" if self._lang == "VI" else "VI"
        self._apply_lang()

    def _apply_lang(self):
        """Refresh all translatable UI text for the current language."""
        # Toolbar buttons
        for btn, key in [
            (self._btn_add,   "add_images"),
            (self._btn_drive, "import_drive"),
            (self._btn_clear, "clear_all"),
            (self._btn_pdf,   "export_pdf"),
        ]:
            btn.configure(text=f" {self._t(key)}")
        self._btn_logout.configure(text=self._t("logout"))

        # Mode label
        self._lbl_mode.configure(text=self._t("mode_label"))

        # Mode radio buttons
        for rb, val, lbl_key, icon in self._mode_radios:
            rb.configure(text=f"{icon} {self._t(lbl_key)}")

        # A4 checkbox
        self._chk_a4.configure(text=self._t("fit_a4"))

        # Sidebar / preview labels
        self._lbl_pagelist.configure(text=self._t("page_list"))
        self._lbl_orig_title.configure(text=self._t("original"))
        self._lbl_proc_title.configure(text=self._t("processed"))

        # Empty state placeholders
        if not self._pages:
            self._orig_label.configure(text=self._t("no_image"))
            self._proc_label.configure(text=self._t("no_image"))
            self._status_var.set(self._t("ready"))
            self._page_count_var.set(self._t("pages").format(n=0))

        # Language button shows flag of the OTHER language (click to switch)
        other_flag = "flag_en" if self._lang == "VI" else "flag_vi"
        self._btn_lang.configure(image=self._icons.get(other_flag))

        # Update per-page card texts (page numbers and delete buttons)
        for i, page in enumerate(self._pages):
            card = page.get("card_widget")
            if not card or not card.winfo_exists():
                continue
            for child in card.winfo_children():
                if isinstance(child, tk.Label):
                    if str(child.cget("fg")) == ACCENT:
                        child.configure(text=self._t("page_n").format(n=i + 1))
                elif isinstance(child, tk.Button):
                    child.configure(text=self._t("delete"))

        # Refresh page count display
        n = len(self._pages)
        if n > 0:
            self._page_count_var.set(self._t("pages").format(n=n))
        
    def _start_overlay(self, initial_msg=""):
        if not self._overlay_active:
            self.root.update_idletasks() # Ensure geometry is current
            self._overlay_active = True
            
            # Create a Toplevel for the 'frosted' blur effect
            self._overlay_win = tk.Toplevel(self.root)
            self._overlay_win.overrideredirect(True)
            self._overlay_win.attributes("-alpha", 0.7) # Slightly higher for text clarity
            self._overlay_win.configure(bg="#ffffff") # High white for frost look
            
            # Match root's position and size
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            self._overlay_win.geometry(f"{w}x{h}+{x}+{y}")
            
            # Add rotating label inside the frosted win
            self._overlay_cat_lbl = tk.Label(self._overlay_win, bg="#ffffff", bd=0)
            self._overlay_cat_lbl.place(relx=0.5, rely=0.45, anchor="center")
            
            # Status message label on overlay
            self._overlay_msg_lbl = tk.Label(self._overlay_win, text=initial_msg, 
                                             bg="#ffffff", fg=TEXT_MAIN,
                                             font=("Segoe UI", 14, "bold"))
            self._overlay_msg_lbl.place(relx=0.5, rely=0.8, anchor="center")
            
            self._overlay_angle = 0
            self._animate_overlay()

    def _update_overlay_msg(self, msg):
        if self._overlay_active and self._overlay_msg_lbl:
            self.root.after(0, self._overlay_msg_lbl.configure, {"text": msg})

    def _stop_overlay(self):
        self._overlay_active = False
        if self._overlay_win:
            self._overlay_win.destroy()
            self._overlay_win = None
            self._overlay_cat_lbl = None
            self._overlay_msg_lbl = None

    def _animate_overlay(self):
        if not self._overlay_active:
            return
        
        pil_img = self._icons.get("round_pil")
        if pil_img:
            self._overlay_angle = (self._overlay_angle - 10) % 360 # clockwise is negative angle in PIL
            rotated = pil_img.rotate(self._overlay_angle, resample=Image.BICUBIC)
            photo = ImageTk.PhotoImage(rotated)
            self._overlay_cat_lbl.configure(image=photo)
            self._overlay_cat_lbl._photo = photo
        
        self.root.after(30, self._animate_overlay)

    def _start_animation(self):
        if not self._animating:
            self._animating = True
            self._animate_cat()

    def _animate_cat(self):
        if not self._processing:
            self._animating = False
            self._progress_img.configure(image=self._icons.get("progress"))
            self._progress_img.place(x=2, y=3) # Reset pos
            return

        # Fly back and forth
        self._cat_x += 5 * self._cat_dir
        # Runway width 160. Icon ~28. Max x = 160 - 28 - 2 = 130
        if self._cat_x >= 128:
            self._cat_dir = -1
            self._progress_img.configure(image=self._icons.get("progress_flipped"))
        elif self._cat_x <= 2:
            self._cat_dir = 1
            self._progress_img.configure(image=self._icons.get("progress"))
        
        self._progress_img.place(x=self._cat_x, y=3)
        self.root.after(30, self._animate_cat)

    def _logout_drive(self):
        """Delete stored Google Drive token to log out."""
        app_data = os.environ.get('APPDATA', os.path.expanduser("~"))
        token_path = Path(app_data) / "CDScanner" / "token.json"
        if token_path.exists():
            try:
                token_path.unlink()
                messagebox.showinfo(self._t("logout_success_title"), self._t("logout_success_msg"))
            except Exception as e:
                messagebox.showerror(self._t("logout_err_title"), self._t("logout_err").format(err=e))
        else:
            messagebox.showinfo(self._t("logout_no_login_title"), self._t("logout_no_login"))

    def _import_from_drive(self):
        if self._processing:
            return
        
        folder_name = simpledialog.askstring(self._t("drive_import_title"), self._t("drive_prompt"))
        if not folder_name:
            return

        self._processing = True
        status_msg = self._t("drive_searching").format(name=folder_name)
        self._status_var.set(status_msg)
        self._start_animation()
        self._start_overlay(status_msg)

        choice_event = threading.Event()
        selection = {"idx": -1}

        def worker():
            try:
                ds = DriveService(credentials_path=resource_path("credentials.json"))
                folders = ds.find_folders_by_name(folder_name)
                
                if not folders:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Info", self._t("drive_not_found").format(name=folder_name)))
                    self.root.after(0, self._finish_loading)
                    self.root.after(0, self._stop_overlay)
                    return

                selected_folder_id = None
                if len(folders) > 1:
                    options = []
                    for f in folders:
                        path_str = ds.get_folder_path(f['id'], max_levels=5)
                        options.append(path_str)

                    def show_dialog():
                        if self._overlay_win: self._overlay_win.withdraw()
                        dialog = RadioSelectionDialog(
                            self.root,
                            self._t("drive_multi_title"),
                            self._t("drive_multi_msg"),
                            options,
                            ok_text=self._t("select_btn"),
                            cancel_text=self._t("cancel_btn"),
                        )
                        selection["idx"] = dialog.result
                        if self._overlay_win: self._overlay_win.deiconify()
                        choice_event.set()

                    self.root.after(0, show_dialog)
                    choice_event.wait() # Wait for User

                    if selection["idx"] is None or selection["idx"] == -1:
                        self.root.after(0, self._finish_loading)
                        self.root.after(0, self._stop_overlay)
                        return
                    selected_folder_id = folders[selection["idx"]]['id']
                else:
                    selected_folder_id = folders[0]['id']

                images = ds.get_images_from_folder_id(selected_folder_id)
                if not images:
                    self.root.after(0, lambda: messagebox.showinfo("Info", self._t("drive_no_images")))
                    self.root.after(0, self._finish_loading)
                    self.root.after(0, self._stop_overlay)
                    return

                folder_cache_dir = Path(self._temp_dir) / selected_folder_id
                folder_cache_dir.mkdir(exist_ok=True)

                local_paths = []
                for i, img in enumerate(images):
                    local_path = folder_cache_dir / img['name']
                    
                    if local_path.exists():
                        # Skip download
                        msg = self._t("drive_cached").format(i=i+1, n=len(images), name=img['name'])
                    else:
                        msg = self._t("drive_downloading").format(i=i+1, n=len(images), name=img['name'])
                        ds.download_file(img['id'], local_path)
                    
                    self.root.after(0, self._status_var.set, msg)
                    self._update_overlay_msg(msg)
                    local_paths.append(str(local_path))
                
                # 2. Load the downloaded images into the UI
                mode = self._mode_var.get()
                for i, p in enumerate(local_paths):
                    msg = self._t("drive_processing").format(i=i+1, n=len(local_paths))
                    self.root.after(0, self._status_var.set, msg)
                    self._update_overlay_msg(msg)
                    try:
                        orig_pil, proc_cv2, method = unwarp_image(p)
                        proc_pil = enhance_image(proc_cv2, mode=mode)
                        self.root.after(0, self._add_page, p, orig_pil, proc_cv2, proc_pil, method)
                    except Exception as exc:
                        print(f"Drive image processing error {p}: {exc}")

                self.root.after(0, self._finish_loading)

            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror(
                    self._t("err_drive"), self._t("drive_failed").format(err=err)))
                self.root.after(0, self._finish_loading)

        threading.Thread(target=worker, daemon=True).start()

    def _on_mousewheel(self, event):
        # Support for Windows (event.delta is roughly 120 per notch)
        if self._page_canvas.winfo_exists():
            # Scroll only if the content is taller than the canvas
            if self._thumb_frame.winfo_height() > self._page_canvas.winfo_height():
                self._page_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Actions ────────────────────────────

    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title=self._t("add_title"),
            filetypes=[(self._t("add_types"), "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                       (self._t("all_files"), "*.*")]
        )
        if paths:
            self._load_images(list(paths))

    def _on_drop(self, event):
        # Parse paths from DnD event (may be wrapped in braces for paths with spaces)
        raw = event.data
        paths = []
        # Simple parser for DnD file list
        import re
        for p in re.findall(r'\{([^}]+)\}|(\S+)', raw):
            path = p[0] or p[1]
            if Path(path).is_file():
                paths.append(path)
        if paths:
            self._load_images(paths)

    def _load_images(self, paths: list):
        if self._processing:
            return
        self._processing = True
        status_msg = self._t("processing_n").format(n=len(paths))
        self._status_var.set(status_msg)
        self._start_animation()
        self._start_overlay(status_msg)

        def worker():
            mode = self._mode_var.get()
            for i, p in enumerate(paths):
                msg = self._t("processing_img").format(i=i+1, n=len(paths), name=Path(p).name)
                self.root.after(0, self._status_var.set, msg)
                self._update_overlay_msg(msg)
                try:
                    orig_pil, proc_cv2, method = unwarp_image(p)
                    proc_pil = enhance_image(proc_cv2, mode=mode)
                    self.root.after(0, self._add_page, p, orig_pil, proc_cv2, proc_pil, method)
                except Exception as exc:
                    self.root.after(0, lambda e=exc, f=p:
                        messagebox.showerror(self._t("err_process"),
                                             self._t("err_process_msg").format(file=f, err=e)))

            self.root.after(0, self._finish_loading)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_loading(self):
        self._processing = False
        self._stop_overlay()
        n = len(self._pages)
        self._status_var.set(self._t("loaded_n").format(n=n))
        self._page_count_var.set(self._t("pages").format(n=n))

    def _add_page(self, path: str, orig: Image.Image, proc_cv2: np.ndarray, proc_pil: Image.Image, method: str = "onnx"):
        # Build thumbnail
        thumb = proc_pil.copy()
        thumb.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        thumb_photo = ImageTk.PhotoImage(thumb)

        idx = len(self._pages)
        page_data = {
            "path": path,
            "orig_pil": orig,
            "unwarped_cv2": proc_cv2, # Cache the BGR unwarped image
            "proc_pil": proc_pil,
            "thumb_photo": thumb_photo,
            "method": method,
        }
        self._pages.append(page_data)

        # Build card widget
        card = tk.Frame(self._thumb_frame, bg=BG_CARD, padx=4, pady=4, cursor="hand2")

        img_lbl = tk.Label(card, image=thumb_photo, bg=BG_CARD)
        img_lbl.pack()

        name = Path(path).name
        name_lbl = tk.Label(card, text=name[:14] + "…" if len(name) > 15 else name,
                             bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 8), wraplength=120)
        name_lbl.pack()

        num_lbl = tk.Label(card, text=self._t("page_n").format(n=idx+1), bg=BG_CARD, fg=ACCENT,
                           font=("Segoe UI", 8, "bold"))
        num_lbl.pack()

        _badge = {
            "onnx":         (self._t("method_onnx"),  "#27ae60"),
            "perspective":  (self._t("method_persp"), "#2980b9"),
            "enhance_only": (self._t("method_orig"),  "#d35400"),
        }
        det_text, det_color = _badge.get(method, ("⚠️ Ảnh gốc", "#d35400"))
        det_lbl = tk.Label(card, text=det_text, bg=BG_CARD, fg=det_color,
                           font=("Segoe UI", 7))
        det_lbl.pack()

        del_btn = tk.Button(card, text=self._t("delete"), image=self._icons.get("del"), 
                             compound="left", bg=BG_CARD, fg="#e74c3c",
                             activebackground=BG_CARD, activeforeground="#c0392b",
                             font=("Segoe UI", 8, "bold"), borderwidth=0, cursor="hand1")
        del_btn.pack(pady=2)

        page_data["card_widget"] = card
        self._refresh_page_widgets()
        self._select_page(idx)

    def _refresh_page_widgets(self):
        """Clears and rebuilds the card list, updates indices and bindings."""
        # 1. Clear current packings
        for p in self._pages:
            if "card_widget" in p and p["card_widget"].winfo_exists():
                p["card_widget"].pack_forget()
        
        # 2. Re-pack and update every page
        for i, page in enumerate(self._pages):
            idx = i # capture for lambda
            card = page.get("card_widget")
            if not card or not card.winfo_exists():
                continue
                
            card.pack(fill="x", padx=6, pady=3)
            
            # Update labels and re-bind events (NO add="+")
            for child in card.winfo_children():
                if isinstance(child, tk.Label):
                    # Page Number Label
                    if child.cget("foreground") == ACCENT or child.cget("fg") == ACCENT:
                        child.configure(text=self._t("page_n").format(n=i+1))
                    
                    # Ensure standard labels select and drag
                    if not isinstance(child, tk.Button):
                        child.bind("<Button-1>", lambda e, x=idx: self._select_page(x))
                        child.bind("<B1-Motion>", lambda e, x=idx: self._on_thumb_drag(e, x))
                        child.bind("<ButtonRelease-1>", lambda e, x=idx: self._on_thumb_release(e, x))
                
                elif isinstance(child, tk.Button):
                    # Delete button
                    child.configure(command=lambda x=idx: self._delete_page(x))
            
            # Re-bind card itself
            card.bind("<Button-1>", lambda e, x=idx: self._select_page(x))
            card.bind("<B1-Motion>", lambda e, x=idx: self._on_thumb_drag(e, x))
            card.bind("<ButtonRelease-1>", lambda e, x=idx: self._on_thumb_release(e, x))

    def _on_thumb_drag(self, event, index):
        """Handle visual feedback or state during drag (optional)."""
        pass

    def _on_thumb_release(self, event, index):
        """Perform the move based on drop coordinates."""
        # Find which card is under the mouse cursor
        x, y = event.x_root, event.y_root
        target_index = -1
        
        for i, p in enumerate(self._pages):
            w = p["card_widget"]
            try:
                wx = w.winfo_rootx()
                wy = w.winfo_rooty()
                ww = w.winfo_width()
                wh = w.winfo_height()
                
                if wx <= x <= wx + ww and wy <= y <= wy + wh:
                    target_index = i
                    break
            except:
                continue
        
        if 0 <= index < len(self._pages) and target_index != -1 and target_index != index:
            # Move index to target_index
            item = self._pages.pop(index)
            self._pages.insert(target_index, item)
            self._refresh_page_widgets()
            self._select_page(target_index)

    def _delete_page(self, idx: int):
        if 0 <= idx < len(self._pages):
            page_to_del = self._pages.pop(idx)
            card = page_to_del.get("card_widget")
            if card and card.winfo_exists():
                card.destroy()
            
            self._refresh_page_widgets()
            
            n = len(self._pages)
            self._page_count_var.set(self._t("pages").format(n=n))
            
            if self._pages:
                new_idx = min(idx, len(self._pages) - 1)
                self._select_page(new_idx)
            else:
                self._selected_idx = -1
                self._orig_label.configure(image="", text=self._t("no_image"))
                self._proc_label.configure(image="", text=self._t("no_image"))

    def _select_page(self, idx: int):
        # Deselect previous
        if 0 <= self._selected_idx < len(self._pages):
            prev_card = self._pages[self._selected_idx].get("card_widget")
            if prev_card and prev_card.winfo_exists():
                prev_card.configure(bg=BG_CARD)
                for child in prev_card.winfo_children():
                    try:
                        child.configure(bg=BG_CARD)
                    except Exception:
                        pass

        self._selected_idx = idx
        if 0 <= idx < len(self._pages):
            page = self._pages[idx]
            card = page.get("card_widget")
            if card and card.winfo_exists():
                card.configure(bg=ACCENT2)
                for child in card.winfo_children():
                    try:
                        child.configure(bg=ACCENT2)
                    except Exception:
                        pass

            self._show_preview(page["orig_pil"], page["proc_pil"])

    def _show_preview(self, orig: Image.Image, proc: Image.Image):
        def fit(pil_img: Image.Image, label: tk.Label) -> ImageTk.PhotoImage:
            w = label.winfo_width()  or PREVIEW_MAX
            h = label.winfo_height() or PREVIEW_MAX
            img = pil_img.copy()
            img.thumbnail((w, h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        orig_photo = fit(orig, self._orig_label)
        proc_photo = fit(proc, self._proc_label)

        self._orig_label.configure(image=orig_photo, text="")
        self._proc_label.configure(image=proc_photo, text="")
        # Keep references
        self._orig_label._photo = orig_photo
        self._proc_label._photo = proc_photo

    def _clear_all(self):
        if not self._pages:
            return
        if not messagebox.askyesno(self._t("clear_confirm_title"), self._t("clear_confirm_msg")):
            return
        for page in self._pages:
            card = page.get("card_widget")
            if card and card.winfo_exists():
                card.destroy()
        self._pages.clear()
        self._selected_idx = -1
        self._page_count_var.set(self._t("pages").format(n=0))
        self._status_var.set(self._t("cleared_all"))
        self._orig_label.configure(image="", text=self._t("no_image"))
        self._proc_label.configure(image="", text=self._t("no_image"))

    def _on_mode_change(self):
        """Re-process all loaded images with the new mode."""
        if not self._pages or self._processing:
            return
        self._processing = True
        mode = self._mode_var.get()
        status_msg = self._t("updating_filter").format(mode=mode)
        self._status_var.set(status_msg)
        self._start_animation()
        self._start_overlay(status_msg)

        def worker():
            for i, page in enumerate(self._pages):
                msg = self._t("updating_i").format(i=i+1, n=len(self._pages), name=Path(page['path']).name)
                self.root.after(0, self._status_var.set, msg)
                self._update_overlay_msg(msg)
                try:
                    # Optimized: Skip slow unwarping, use cached CV2 image
                    proc_cv2 = page["unwarped_cv2"]
                    proc_pil = enhance_image(proc_cv2, mode=mode)
                    
                    page["proc_pil"] = proc_pil
                    # Update thumbnail
                    thumb = proc_pil.copy()
                    thumb.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(thumb)
                    page["thumb_photo"] = photo
                    card = page.get("card_widget")
                    if card and card.winfo_exists():
                        children = card.winfo_children()
                        if children:
                            self.root.after(0, lambda l=children[0], ph=photo: l.configure(image=ph) or setattr(l, "_photo", ph))
                except Exception:
                    pass

            self.root.after(0, self._after_mode_change)

        threading.Thread(target=worker, daemon=True).start()

    def _after_mode_change(self):
        self._processing = False
        self._stop_overlay()
        self._status_var.set(self._t("filter_updated"))
        # Refresh preview of selected page
        if 0 <= self._selected_idx < len(self._pages):
            page = self._pages[self._selected_idx]
            self._show_preview(page["orig_pil"], page["proc_pil"])

    def _export_pdf(self):
        if not self._pages:
            messagebox.showwarning(self._t("no_pages_title"), self._t("no_pages_msg"))
            return

        out_path = filedialog.asksaveasfilename(
            title=self._t("pdf_save_title"),
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=self._t("pdf_file"),
        )
        if not out_path:
            return

        status_msg = self._t("pdf_exporting")
        self._status_var.set(status_msg)
        self._start_animation()
        self._start_overlay(status_msg)

        pil_images = [p["proc_pil"] for p in self._pages]
        fit_a4 = self._fit_a4_var.get()

        def worker():
            try:
                result = images_to_pdf(pil_images, out_path, fit_to_a4=fit_a4)
                self.root.after(0, lambda: self._export_done(result))
            except Exception as exc:
                self.root.after(0, lambda e=exc: (
                    self._status_var.set(self._t("err_pdf_status")),
                    self._set_processing_false(),
                    self._stop_overlay(),
                    messagebox.showerror(self._t("err_pdf"), self._t("err_pdf_msg").format(err=e))
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _export_done(self, path: str):
        self._processing = False
        self._stop_overlay()
        self._status_var.set(self._t("pdf_exported").format(name=Path(path).name))
        if messagebox.askyesno(self._t("pdf_success_title"),
                               self._t("pdf_success_msg").format(path=path)):
            os.startfile(path)


    def _set_processing_false(self):
        self._processing = False

# ───────────────────────────────────────────
# Entry point
# ───────────────────────────────────────────

def main():
    if _DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = DocumentScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
