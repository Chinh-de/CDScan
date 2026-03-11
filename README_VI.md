# Hướng dẫn sử dụng CDScaner (Tiếng Việt)

## Giới thiệu

CDScaner là ứng dụng Windows dùng để quét tài liệu bằng cách nhập ảnh, xử lý góc, cân bằng màu và xuất ra file PDF. Giao diện đơn giản, dễ dùng, có hỗ trợ hai ngôn ngữ (tiếng Việt/tiếng Anh) và tích hợp Google Drive.

## Cài đặt

1. Mở PowerShell hoặc cmd.
2. Tạo môi trường ảo (khuyến nghị):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Cài đặt thư viện:
   ```powershell
   pip install -r requirements.txt
   ```
4. Nếu bạn muốn sử dụng Google Drive, hãy đặt file `credentials.json` (tải từ Google API Console) vào thư mục gốc.

## Khởi động ứng dụng

Chạy lệnh:
```powershell
python main_app.py
```
Cửa sổ sẽ mở ra ở chế độ toàn màn hình (maximized).

## Các phần chính của giao diện

- **Thanh công cụ (ở trên cùng)** chứa:
  - Nút `Thêm ảnh` (📁): chọn file từ ổ cứng.
  - Nút biểu tượng Drive (☁️): nhập ảnh từ một thư mục Google Drive.
  - Nút `Xóa tất cả` (❌): xóa mọi trang đã tải.
  - Nút `Xuất PDF` (📄): xuất các trang hiện tại thành file PDF.
  - Nút lá cờ: chuyển đổi ngôn ngữ (biểu tượng lá cờ cho biết ngôn ngữ bạn sẽ chuyển sang).
  - Nút đăng xuất (🧑‍💻): xóa token Google Drive hiện tại.
  - Dãy radio cho các chế độ xử lý (tài liệu, siêu nét, sinh động, đen trắng, xám, tự nhiên).
  - Checkbox `Khổ A4` để căn kích thước khi xuất PDF.

- **Thanh bên trái**: danh sách thu nhỏ (thumbnail) trang. Kéo để thay đổi vị trí, nhấn nút `Xóa` trên mỗi thẻ để bỏ.

- **Khu vực chính giữa**: xem trước ảnh gốc bên trái và ảnh đã xử lý bên phải.

- **Thanh trạng thái (ở đáy)**: hiển thị thông báo và tiến trình xử lý.

## Thêm và xử lý ảnh

1. Nhấn `Thêm ảnh` hoặc kéo tệp từ Windows Explorer vào cửa sổ.
2. Ứng dụng sẽ phân tích và xử lý từng ảnh (căn chỉnh, lọc).
3. Thumbnails xuất hiện bên trái.
4. Nhấn vào thumbnail để xem ảnh gốc và sau xử lý.
5. Nhấn và kéo thumbnail để thay đổi thứ tự trang.
6. Nhấn nút `Xóa` trên thumbnail để loại bỏ trang.

## Thay đổi chế độ xử lý

- Trên thanh công cụ, chọn một trong các chế độ:
  - **Tài liệu**: chai hơn, ít màu.
  - **Siêu nét**: tăng chi tiết.
  - **Sinh động**: màu tươi bật.
  - **Đen trắng**: loại bỏ màu.
  - **Xám**: chỉ còn độ xám.
  - **Tự nhiên**: giữ lại màu gốc.

Ứng dụng sẽ tái xử lý tất cả trang ngay lập tức.

## Nhập ảnh từ Google Drive

1. Nhấn nút Drive (☁️).
2. Nhập tên thư mục trên Drive rồi xác nhận.
3. Nếu có nhiều thư mục cùng tên, hộp thoại sẽ yêu cầu chọn.
4. Ảnh trong thư mục sẽ được tải về bộ nhớ tạm và xử lý giống như ảnh bình thường.
5. Lưu ý: lần đầu sẽ yêu cầu đăng nhập Google.

## Xuất PDF

1. Nhấn `Xuất PDF`.
2. Chọn nơi lưu file và tên.
3. Nếu chọn `Khổ A4`, các trang sẽ được căn theo khổ A4.
4. Sau khi xuất xong, ứng dụng sẽ hỏi bạn có muốn mở file đó ngay không.

## Chuyển đổi ngôn ngữ

Nhấn vào **icon lá cờ** trên thanh công cụ để chuyển giữa tiếng Việt và tiếng Anh. Biểu tượng hiện tại hiển thị ngôn ngữ bạn *sẽ chuyển đến*.

## Đăng xuất Google Drive

- Nhấn nút `Đăng xuất` để xóa token Google Drive.
- Khi cần nhập lại, bạn sẽ phải xác thực lại lần lượt.

## Mẹo & xử lý sự cố

- Nếu ứng dụng bị đơ trong quá trình xử lý, hãy kiên nhẫn – đó là do giác quan đang chạy luồng nền.
- Đảm bảo kết nối Internet ổn định khi dùng Drive.
- Nếu muốn dọn sạch bộ nhớ tạm, bạn có thể đóng ứng dụng – thư mục tạm sẽ bị xoá.

## Đóng ứng dụng

Nhấn nút đóng cửa sổ hoặc ALT+F4; bộ nhớ tạm sẽ tự động xoá.

---

Chúc bạn sử dụng hiệu quả! Nếu cần thêm tính năng, đóng góp lên kho GitHub hoặc gửi PR.