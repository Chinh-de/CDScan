"""
main_app.py
Document Scanner – Windows Desktop App
Tkinter-based GUI: import images, preview processing, manage pages, export PDF.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk

# Try to enable drag-and-drop
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

from scanner_core import process_image
from pdf_exporter import images_to_pdf


# ───────────────────────────────────────────
# Constants / Theme (Cat Style - Warm/Pastel)
# ───────────────────────────────────────────

BG_DARK     = "#fdf6e3"   # Cream background
BG_PANEL    = "#fffbf0"   # Lighter cream
BG_CARD     = "#ffe3e3"   # Soft pink for cards
ACCENT      = "#ff9a9e"   # Coral pink
ACCENT2     = "#a18cd1"   # Soft purple for selection
TEXT_LIGHT  = "#4a4a4a"   # Dark gray text for readability
TEXT_DIM    = "#8a8a8a"   # Medium gray
TEXT_WHITE  = "#ffffff"   # White (on buttons)

THUMB_W, THUMB_H = 110, 145
PREVIEW_MAX = 480


# ───────────────────────────────────────────
# App class
# ───────────────────────────────────────────

class DocumentScannerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Meow Scanner 🐾 – Quét tài liệu")
        self.root.geometry("1180x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        self._pages: list[dict] = []          # {"path", "orig_pil", "proc_pil", "thumb_photo", "label_widget"}
        self._selected_idx: int = -1
        self._mode_var    = tk.StringVar(value="color")
        self._status_var  = tk.StringVar(value="Sẵn sàng")
        self._fit_a4_var  = tk.BooleanVar(value=True)
        self._processing  = False

        self._setup_styles()
        self._build_ui()

        if _DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)

    # ── Styles ──────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame",        background=BG_DARK)
        style.configure("Panel.TFrame",  background=BG_PANEL)
        style.configure("Card.TFrame",   background=BG_CARD)
        style.configure("TLabel",        background=BG_DARK,  foreground=TEXT_LIGHT, font=("Segoe UI", 10))
        style.configure("Title.TLabel",  background=BG_DARK,  foreground=TEXT_LIGHT, font=("Segoe UI", 13, "bold"))
        style.configure("Dim.TLabel",    background=BG_PANEL, foreground=TEXT_DIM,   font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=BG_DARK,  foreground=ACCENT2,    font=("Segoe UI", 9, "italic"))

        # Buttons
        for name, bg, fg in [
            ("Add.TButton",    ACCENT,   TEXT_WHITE),
            ("Export.TButton", "#27ae60", TEXT_WHITE),
            ("Del.TButton",    "#c0392b", TEXT_WHITE),
            ("Clear.TButton",  "#7f8c8d", TEXT_WHITE),
        ]:
            style.configure(name, background=bg, foreground=fg,
                            font=("Segoe UI", 10, "bold"),
                            borderwidth=0, focusthickness=0, padding=8)
            style.map(name, background=[("active", BG_CARD)])

        style.configure("TRadiobutton", background=BG_PANEL,
                        foreground=TEXT_LIGHT, font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=BG_PANEL,
                        foreground=TEXT_LIGHT, font=("Segoe UI", 10))
        style.configure("Vertical.TScrollbar", background=BG_CARD,
                        troughcolor=BG_PANEL, borderwidth=0, arrowsize=12)
        style.configure("TProgressbar", background=ACCENT, troughcolor=BG_PANEL)

    # ── Build UI ────────────────────────────

    def _build_ui(self):
        # ─ Top toolbar
        toolbar = ttk.Frame(self.root, style="Panel.TFrame", padding=(12, 8))
        toolbar.pack(fill="x", side="top")

        ttk.Label(toolbar, text="Meow Scanner 🐱", style="Title.TLabel").pack(side="left", padx=(0, 16))

        ttk.Button(toolbar, text="🐟 Thêm ảnh",    style="Add.TButton",   command=self._add_images).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🗑 Xóa giỏ",     style="Clear.TButton", command=self._clear_all).pack(side="left", padx=4)
        ttk.Button(toolbar, text="� Xuất PDF",    style="Export.TButton",command=self._export_pdf).pack(side="left", padx=4)

        # Separator
        ttk.Label(toolbar, text="│", foreground=TEXT_DIM, background=BG_PANEL).pack(side="left", padx=8)

        # Mode selector
        ttk.Label(toolbar, text="Chế độ:", background=BG_PANEL, foreground=TEXT_DIM).pack(side="left")
        
        mode_frame = tk.Frame(toolbar, bg=BG_PANEL)
        mode_frame.pack(side="left", padx=4)
        
        for val, icon, lbl in [("document","📄","Tài liệu"),
                               ("super_sharp","⚡","Siêu nét"),
                               ("magic_color","🪄","Sinh động"),
                               ("bw_strict","🖤","Đen trắng"),
                               ("grayscale","🩶","Xám"),
                               ("color","🎨","Tự nhiên")]:
            ttk.Radiobutton(mode_frame, text=f"{icon} {lbl}", variable=self._mode_var,
                            value=val, command=self._on_mode_change).pack(side="left", padx=2)

        ttk.Label(toolbar, text="│", foreground=TEXT_DIM, background=BG_PANEL).pack(side="left", padx=8)
        ttk.Checkbutton(toolbar, text="Khổ A4", variable=self._fit_a4_var).pack(side="left")

        # ─ Main area
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # Left: page list
        left = ttk.Frame(main, style="Panel.TFrame", width=150)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        ttk.Label(left, text="Danh sách trang",
                  background=BG_PANEL, foreground=TEXT_DIM,
                  font=("Segoe UI", 9, "bold")).pack(pady=(10,4))

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

        ttk.Label(center, text="Ảnh gốc", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(center, text="Sau xử lý", style="Title.TLabel").grid(row=0, column=1, sticky="w", padx=4)

        self._orig_label = tk.Label(center, bg=BG_CARD, width=PREVIEW_MAX, height=PREVIEW_MAX,
                                     text="Chưa có ảnh", fg=TEXT_DIM, font=("Segoe UI", 11))
        self._orig_label.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

        self._proc_label = tk.Label(center, bg=BG_CARD, width=PREVIEW_MAX, height=PREVIEW_MAX,
                                     text="Chưa có ảnh", fg=TEXT_DIM, font=("Segoe UI", 11))
        self._proc_label.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")

        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=1)
        center.rowconfigure(1, weight=1)

        # ─ Status bar
        status_bar = ttk.Frame(self.root, style="Panel.TFrame", padding=(10, 4))
        status_bar.pack(fill="x", side="bottom")

        self._progress = ttk.Progressbar(status_bar, mode="indeterminate", length=150)
        self._progress.pack(side="right", padx=8)

        ttk.Label(status_bar, textvariable=self._status_var, style="Status.TLabel",
                  background=BG_PANEL).pack(side="left")

        page_count_frame = ttk.Frame(status_bar, style="Panel.TFrame")
        page_count_frame.pack(side="right", padx=16)
        self._page_count_var = tk.StringVar(value="0 trang")
        ttk.Label(page_count_frame, textvariable=self._page_count_var,
                  background=BG_PANEL, foreground=TEXT_DIM,
                  font=("Segoe UI", 9)).pack()

    def _on_mousewheel(self, event):
        # Support for Windows (event.delta is roughly 120 per notch)
        if self._page_canvas.winfo_exists():
            # Scroll only if the content is taller than the canvas
            if self._thumb_frame.winfo_height() > self._page_canvas.winfo_height():
                self._page_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Actions ────────────────────────────

    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title="Chọn ảnh tài liệu",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"), ("Tất cả", "*.*")]
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
        self._status_var.set(f"Đang xử lý {len(paths)} ảnh…")
        self._progress.start(10)

        def worker():
            mode = self._mode_var.get()
            for p in paths:
                try:
                    orig_pil, proc_pil, method = process_image(p, mode=mode)
                    self.root.after(0, self._add_page, p, orig_pil, proc_pil, method)
                except Exception as exc:
                    self.root.after(0, lambda e=exc, f=p:
                        messagebox.showerror("Lỗi xử lý ảnh", f"Không thể xử lý:\n{f}\n\n{e}"))

            self.root.after(0, self._finish_loading)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_loading(self):
        self._processing = False
        self._progress.stop()
        n = len(self._pages)
        self._status_var.set(f"Đã tải {n} trang")
        self._page_count_var.set(f"{n} trang")

    def _add_page(self, path: str, orig: Image.Image, proc: Image.Image, method: str = "onnx"):
        # Build thumbnail
        thumb = proc.copy()
        thumb.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        thumb_photo = ImageTk.PhotoImage(thumb)

        idx = len(self._pages)
        page_data = {
            "path": path,
            "orig_pil": orig,
            "proc_pil": proc,
            "thumb_photo": thumb_photo,
            "method": method,
        }
        self._pages.append(page_data)

        # Build card widget
        card = tk.Frame(self._thumb_frame, bg=BG_CARD, padx=4, pady=4, cursor="hand2")
        card.pack(fill="x", padx=6, pady=3)

        img_lbl = tk.Label(card, image=thumb_photo, bg=BG_CARD)
        img_lbl.pack()

        name = Path(path).name
        name_lbl = tk.Label(card, text=name[:14] + "…" if len(name) > 15 else name,
                             bg=BG_CARD, fg=TEXT_DIM, font=("Segoe UI", 8), wraplength=120)
        name_lbl.pack()

        num_lbl = tk.Label(card, text=f"Trang {idx+1}", bg=BG_CARD, fg=ACCENT,
                           font=("Segoe UI", 8, "bold"))
        num_lbl.pack()

        _badge = {
            "onnx":         ("🧠 AI",         "#2ecc71"),
            "perspective":  ("✅ Khung",       "#3498db"),
            "enhance_only": ("⚠️ Ảnh gốc",   "#f39c12"),
        }
        det_text, det_color = _badge.get(method, ("⚠️ Ảnh gốc", "#f39c12"))
        det_lbl = tk.Label(card, text=det_text, bg=BG_CARD, fg=det_color,
                           font=("Segoe UI", 7))
        det_lbl.pack()

        del_btn = tk.Button(card, text="✕", bg=BG_DARK, fg=ACCENT,
                             font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2",
                             command=lambda i=idx: self._delete_page(i))
        del_btn.pack()

        page_data["card_widget"] = card

        # Bind selection
        for w in (card, img_lbl, name_lbl, num_lbl, det_lbl):
            w.bind("<Button-1>", lambda e, i=idx: self._select_page(i))

        self._select_page(idx)

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

    def _delete_page(self, idx: int):
        if 0 <= idx < len(self._pages):
            card = self._pages[idx].get("card_widget")
            if card:
                card.destroy()
            self._pages.pop(idx)
            # Re-index remaining cards
            for i, page in enumerate(self._pages):
                c = page.get("card_widget")
                if c and c.winfo_exists():
                    children = c.winfo_children()
                    # Update page number label (3rd label child)
                    for child in children:
                        if isinstance(child, tk.Label) and child.cget("fg") == ACCENT:
                            child.configure(text=f"Trang {i+1}")
            n = len(self._pages)
            self._page_count_var.set(f"{n} trang")
            # Select adjacent
            if self._pages:
                new_idx = min(idx, len(self._pages) - 1)
                self._select_page(new_idx)
            else:
                self._selected_idx = -1
                self._orig_label.configure(image="", text="Chưa có ảnh")
                self._proc_label.configure(image="", text="Chưa có ảnh")

    def _clear_all(self):
        if not self._pages:
            return
        if not messagebox.askyesno("Xóa tất cả", "Xóa toàn bộ danh sách trang?"):
            return
        for page in self._pages:
            card = page.get("card_widget")
            if card:
                card.destroy()
        self._pages.clear()
        self._selected_idx = -1
        self._page_count_var.set("0 trang")
        self._status_var.set("Đã xóa tất cả")
        self._orig_label.configure(image="", text="Chưa có ảnh")
        self._proc_label.configure(image="", text="Chưa có ảnh")

    def _on_mode_change(self):
        """Re-process all loaded images with the new mode."""
        if not self._pages or self._processing:
            return
        self._processing = True
        self._status_var.set("Đang đổi chế độ xử lý…")
        self._progress.start(10)
        mode = self._mode_var.get()

        def worker():
            for page in self._pages:
                try:
                    orig, proc, method = process_image(page["path"], mode=mode)
                    page["orig_pil"] = orig
                    page["proc_pil"] = proc
                    page["method"]   = method
                    # Update thumbnail
                    thumb = proc.copy()
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
        self._progress.stop()
        self._status_var.set("Đã cập nhật chế độ xử lý")
        # Refresh preview of selected page
        if 0 <= self._selected_idx < len(self._pages):
            page = self._pages[self._selected_idx]
            self._show_preview(page["orig_pil"], page["proc_pil"])

    def _export_pdf(self):
        if not self._pages:
            messagebox.showwarning("Chưa có ảnh", "Hãy thêm ít nhất một ảnh trước khi xuất PDF.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Lưu PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="tai_lieu_scan.pdf",
        )
        if not out_path:
            return

        self._status_var.set("Đang xuất PDF…")
        self._progress.start(10)

        pil_images = [p["proc_pil"] for p in self._pages]
        fit_a4 = self._fit_a4_var.get()

        def worker():
            try:
                result = images_to_pdf(pil_images, out_path, fit_to_a4=fit_a4)
                self.root.after(0, lambda: self._export_done(result))
            except Exception as exc:
                self.root.after(0, lambda e=exc: (
                    self._progress.stop(),
                    self._status_var.set("Lỗi xuất PDF"),
                    messagebox.showerror("Lỗi", f"Không thể xuất PDF:\n{e}")
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _export_done(self, path: str):
        self._progress.stop()
        self._status_var.set(f"Đã xuất: {Path(path).name}")
        if messagebox.askyesno("Xuất thành công", f"PDF đã lưu tại:\n{path}\n\nMở file ngay?"):
            os.startfile(path)


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
