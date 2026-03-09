# CDScaner

Document Scanner – Windows desktop application built with Tkinter and OpenCV/ONNX.

This project provides a graphical interface for importing photos of documents, enhancing them using an ONNX model, previewing pages, and exporting to PDF. It also supports importing images directly from Google Drive and offers Vietnamese/English multilingual UI with a language toggle.

## Features

- Drag-and-drop or file dialog for selecting document images
- Automatic perspective correction and enhancement (color, B&W, grayscale, etc.)
- Thumbnail list with drag-to-reorder, delete and page count
- Real-time preview of original and processed images
- Export processed pages to a multi-page PDF (optionally fit to A4)
- Integration with Google Drive (login/logout, download folder contents)
- Cute cat-themed UI with animated progress indicator
- Vietnamese/English language switcher (flag icon in toolbar)
- Window starts maximized and is responsive
- Packaged with PyInstaller via `build_exe.bat`

## Requirements

The application runs on Windows and requires Python 3.11+.
Install dependencies using:

```sh
python -m pip install -r requirements.txt
```

> Note: `tkinter` is part of the standard library, but `tkinterdnd2` is required for drag-and-drop support.

## Setup

1. Clone or download the repository.
2. Place your `credentials.json` (Google Drive API) in the project root if you intend to use Drive imports.
3. Optionally create a virtual environment:

   ```sh
   python -m venv venv
   venv\Scripts\Activate.ps1  # PowerShell
   pip install -r requirements.txt
   ```

## Running in Development

Launch the app directly with Python:

```sh
python main_app.py
```

The window will open maximized. Use the toolbar buttons to add images, import from Drive, clear pages, export to PDF, or log out of Google Drive. The language toggle (flag icon) switches between Vietnamese and English.

## Usage Instructions / Hướng dẫn sử dụng

### English
1. **Start the application** – run `python main_app.py` or open the compiled `CDscaner.exe`.
2. **Add images** – click the "Add Images" button or drag files into the window.
3. **Import from Google Drive** – click the cloud icon and enter a folder name; the first login will prompt for credentials.
4. **Preview** – click a thumbnail to view original and processed versions side by side.
5. **Reorder/Delete pages** – drag thumbnails or hit the delete button on each card.
6. **Change processing mode** – select one of the mode radio buttons on the toolbar.
7. **Switch language** – click the flag icon in the toolbar. The icon always shows the language you can switch *to*.
8. **Export PDF** – press "Export PDF" and choose a save location; use the A4 checkbox to fit pages to A4.
9. **Logout Drive** – click the logout button when using Google Drive to clear your token.

### Tiếng Việt
1. **Khởi động** – chạy `python main_app.py` hoặc mở `CDscaner.exe` sau khi đóng gói.
2. **Thêm ảnh** – nhấn nút "Thêm ảnh" hoặc kéo thả tệp vào cửa sổ.
3. **Nhập từ Google Drive** – nhấn biểu tượng đám mây và nhập tên thư mục; lần đầu sẽ yêu cầu đăng nhập.
4. **Xem trước** – nhấn vào thumbnail để xem ảnh gốc và đã xử lý.
5. **Sắp xếp/Xóa trang** – kéo thumbnail hoặc nhấn nút xóa trên mỗi thẻ.
6. **Thay đổi chế độ xử lý** – chọn nút radio chế độ trên thanh công cụ.
7. **Đổi ngôn ngữ** – nhấn vào biểu tượng lá cờ trên thanh; biểu tượng hiển thị ngôn ngữ sẽ chuyển đến.
8. **Xuất PDF** – nhấn "Xuất PDF" và chọn nơi lưu; tích chọn khổ A4 để vừa trang theo A4.
9. **Đăng xuất Drive** – nhấn nút đăng xuất khi dùng Drive để xoá token.
## Building an Executable

A `build_exe.bat` script is included for PyInstaller packaging. Run:

```sh
build_exe.bat
```

which generates a standalone `CDscaner.exe` in the `dist` folder.

## Folder Structure

```
.
├── main_app.py        # primary GUI
├── scanner_core.py    # image processing logic
├── pdf_exporter.py    # convert images to PDF
├── drive_service.py   # Google Drive helper
├── requirements.txt   # Python dependencies
├── static/            # icons and resources
├── input/             # sample documents (optional)
├── test/              # test scripts (demo.py, test_smoke.py)
└── build_exe.bat      # packaging script
```

## Localization

UI strings are stored in a `TRANSLATIONS` dictionary within `main_app.py`. The language toggle button displays a flag icon and switches both static labels and dynamic messages at runtime.

## License

This project is provided under the MIT License (see `LICENSE` if included).

## Troubleshooting

- If the UI freezes while processing, wait a few seconds; the app performs long-running operations in background threads.
- Google Drive functionality requires valid credentials and an active internet connection.

## Contribution

Feel free to fork and submit pull requests. Corrections, new enhancements and translations are welcome.
