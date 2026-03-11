import cv2
import numpy as np
from rembg import remove

# 1. Dùng AI xóa nền bàn phím phức tạp (chỉ giữ lại tờ giấy)
input_path = 'input/test.jpg'
with open(input_path, 'rb') as i:
    input_data = i.read()
    
print("Đang nhờ AI tách nền...")
output_data = remove(input_data) # Trả về ảnh tờ giấy có nền trong suốt (PNG)

# 2. Đọc ảnh đã tách nền bằng OpenCV
nparr = np.frombuffer(output_data, np.uint8)
img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

# 3. Lấy ra tờ giấy (phần không trong suốt)
alpha_channel = img[:, :, 3]
_, mask = cv2.threshold(alpha_channel, 254, 255, cv2.THRESH_BINARY)

# 4. Tìm viền và cắt (Bây giờ nền đã là màu đen hoàn toàn, OpenCV nhắm mắt cũng tìm trúng 4 góc)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
c = max(contours, key=cv2.contourArea)

# Lấy Bounding Box cắt luôn cho nhanh
x, y, w, h = cv2.boundingRect(c)
crop = img[y:y+h, x:x+w]

# Chuyển lại về ảnh RGB bình thường (bỏ kênh trong suốt)
final_crop = cv2.cvtColor(crop, cv2.COLOR_BGRA2BGR)

cv2.imwrite("ai_crop_result.jpg", final_crop)
print("Đã crop xong! Kiểm tra file ai_crop_result.jpg")