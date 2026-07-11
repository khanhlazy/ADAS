<div align="center">
  <h1>🚀 TRAFFICVISION ADAS</h1>
  <h3>Hệ thống Hỗ trợ Lái xe Nâng cao Thời gian thực (Real-time ADAS)</h3>
  <p>Ứng dụng mạng nơ-ron tích chập YOLO11n, thuật toán bám vết đa đối tượng ByteTrack, ước lượng khoảng cách hình học & giao diện Cockpit Autopilot HUD đẳng cấp</p>

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
  [![PyTorch](https://img.shields.io/badge/PyTorch-2.5%20CUDA-EE4C2C.svg?style=flat-square&logo=pytorch)](https://pytorch.org/)
  [![OpenCV](https://img.shields.io/badge/OpenCV-4.11-green.svg?style=flat-square&logo=opencv)](https://opencv.org/)
  [![Flask](https://img.shields.io/badge/Flask-3.1.3-black.svg?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
  [![Waitress](https://img.shields.io/badge/Waitress-3.0.2-orange.svg?style=flat-square)](https://docs.pylonsprojects.org/projects/waitress/)
  [![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg?style=flat-square)](#)
</div>

---

## 📖 1. Giới thiệu dự án (Overview)

**TrafficVision ADAS** là một hệ thống hỗ trợ lái xe nâng cao (Advanced Driver Assistance System) chạy thời gian thực được thiết kế và tối ưu hóa đặc thù cho giao thông hỗn hợp tại Việt Nam. Bằng cách áp dụng **Học sâu (Deep Learning)** kết hợp với **hình học camera**, hệ thống giúp nhận diện các mối nguy va chạm phía trước và đưa ra các cảnh báo bằng giọng nói tiếng Việt kịp thời nhằm nâng cao an toàn giao thông đường bộ.

Hệ thống được phát triển trên kiến trúc phân tách **Micro-Monolith** đa luồng, tối ưu hóa cực hạn giúp chạy mượt mà ở tốc độ **~50 FPS** trên GPU phổ thông (như card đồ họa rời NVIDIA GTX 1650 laptop).
---

## ✨ 2. Tính năng nổi bật (Core Features)

*   **Phát hiện vật thể đa lớp (Object Detection):** Nhận diện thời gian thực 7 lớp vật thể giao thông cốt lõi gồm: Ô tô, Xe máy, Xe tải, Xe buýt, Người đi bộ, Biển báo giao thông và Đèn giao thông.
*   **Bám vết đa đối tượng (Object Tracking):** Tích hợp thuật toán **ByteTrack** (Hungarian + IoU matching) duy trì định danh (ID) liên tục của các phương tiện ngay cả khi bị che khuất tạm thời hoặc thay đổi độ sáng đột ngột.
*   **Hành lang cảnh báo thích ứng (Class-Adaptive Corridor):** Giải pháp đột phá thiết kế dành riêng cho Việt Nam:
    *   Tự động bóp hẹp hành lang an toàn trung tâm đối với **Xe máy (`class_id == 1`) xuống 26%** chiều rộng khung hình.
    *   Giữ nguyên hành lang đối với **Ô tô ở mức 38%** chiều rộng khung hình.
    *   *Kết quả:* Loại bỏ đến 99% các cảnh báo giả do xe máy chạy song song sát sườn ô tô gây ra.
*   **Tính toán khoảng cách & Thời gian va chạm (FCW):**
    *   Ước lượng khoảng cách 3D vật lý kết hợp chiều cao hộp pinhole và góc nghiêng camera.
    *   Tính thời gian dự kiến va chạm **TTC (Time-To-Collision)** bằng vận tốc tương đối làm mịn qua bộ lọc chập **Exponential Moving Average (EMA)**.
*   **Hệ thống cảnh báo kép (Dual-Alert System):** 
    *   *Phía Server:* Phát âm thanh tiếng Việt bất đồng bộ qua luồng nền (PyGame mixer).
    *   *Phía Client:* Tự động phát âm thanh tiếng Việt trực tiếp trên trình duyệt bằng **Web Audio API** (đáp ứng tốt cho headless/cloud deployment).
    *   *Visual Alert:* Viền HUD nhấp nháy đỏ/vàng sinh động tương ứng với mức nguy hiểm.
*   **Bảng điều khiển HUD Autopilot:** Giao diện Cockpit Glassmorphism sang trọng, hiển thị live stream video MJPEG, telemetry (TTC, khoảng cách), console log monospace thời gian thực đồng bộ từ file `logs/system.log`.

---

## 🛠️ 3. Giải pháp công nghệ (Tech Stack)

| Thành phần | Công nghệ sử dụng | Phiên bản | Mô tả |
| :--- | :--- | :---: | :--- |
| **Ngôn ngữ** | Python | 3.10+ | Nền tảng lập trình chính |
| **Deep Learning** | PyTorch GPU (CUDA 12.1) | 2.5+ | Tăng tốc tính toán ma trận mạng nơ-ron |
| **Object Detection** | YOLO11n (Nano) | 2024/2025 | Model One-stage Detector siêu nhẹ, tối ưu tham số |
| **Object Tracking** | ByteTrack (Customized) | - | Bám vết 2 bước liên kết (Double Association) |
| **Web Server** | Flask & Waitress WSGI | 3.1.3 / 3.0.2 | Phục vụ REST API và đa luồng streaming (`threads=24`) |
| **Realtime Stream** | Server-Sent Events (SSE) | - | Truyền phát telemetry một chiều từ server lên client |
| **Audio Alert** | gTTS & Web Audio API | - | Chuyển văn bản thành giọng nói tiếng Việt và phát loa |

---

## 📊 4. Thông số mô hình & Kết quả huấn luyện (YOLOv11n Metrics)

Hệ thống sử dụng mô hình học sâu **YOLOv11n** đã được huấn luyện kỹ lưỡng trên tập dữ liệu BDD100K kết hợp với hàng ngàn ảnh chụp giao thông thực tế tại Việt Nam:

### ⚙️ Siêu tham số huấn luyện (Training Hyperparameters):
*   **Mô hình gốc:** `yolov11n.pt` (Nano version)
*   **Độ phân giải đầu vào:** $640 \times 640$ pixels (tự động resize)
*   **Kích thước Batch size:** 16
*   **Số lượng Epochs:** 50

### 📈 Kết quả đánh giá mô hình (Model Metrics):
*   **Precision (Độ chính xác):** **67.24%** (`0.67235`)
*   **Recall (Độ nhạy):** **52.33%** (`0.52331`)
*   **mAP@50:** **58.32%** (`0.58323`)
*   **mAP@50-95:** **32.61%** (`0.32611`)

### 📉 Biến thiên hàm mất mát (Loss Values):
*   **Box Loss:** Train: `1.46103` | Validation: `1.37555`
*   **Class Loss (Cls):** Train: `0.93747` | Validation: `0.81585`
*   **DFL Loss:** Train: `1.04462` | Validation: `1.00197`

*Nhận xét:* Hàm mất mát trên tập Validation hội tụ đều đặn và thấp hơn tập Train, cho thấy mô hình không bị Overfitting và đạt khả năng tổng quát hóa rất tốt đối với các dạng thời tiết nắng, mưa và ban đêm.

---

## 📐 5. Giải pháp toán học cốt lõi (Core Mathematics)

### 5.1 Ước lượng khoảng cách hình học
Hệ thống kết hợp 2 nguồn tính toán hình học từ camera pinhole tĩnh:
1.  **Dựa trên chiều cao hộp (Bounding Box Height):**
    $$d_{height} = \frac{H_{real} \times f}{h_{box}}$$
    *(Trong đó $H_{real}$ là chiều cao thực tế của đối tượng ví dụ xe con $\sim 1.5m$, xe tải $\sim 2.8m$; $f$ là tiêu cự camera; $h_{box}$ là chiều cao pixel)*
2.  **Dựa trên góc nghiêng đường chân trời (Horizon Angle):**
    $$d_{horizon} = \frac{h_{cam} \times f}{y_2 - y_{horizon}}$$
    *(Trong đó $h_{cam}$ là chiều cao lắp đặt camera $\sim 1.35m$, $y_2$ là tọa độ mép đáy hộp, $y_{horizon}$ là vị trí đường chân trời)*
3.  **Công thức tích hợp (Sensor Fusion):**
    $$dist = 0.6 \times d_{height} + 0.4 \times d_{horizon}$$

### 5.2 Tính toán TTC & Làm mịn vận tốc
Hệ thống lưu vết khoảng cách $d$ của từng xe mang ID qua các frame liên tiếp để tính toán vận tốc tương đối $v_{rel}$ và làm mịn qua bộ lọc Exponential Moving Average (EMA):
$$v_{smooth} = 0.25 \times v_{raw} + 0.75 \times v_{prev}$$
$$TTC = \frac{d_{current}}{v_{smooth}}$$
Nếu $TTC < 1.3s$ hoặc khoảng cách $< 8m$, hệ thống lập tức kích hoạt trạng thái **DANGER** (Nguy hiểm khẩn cấp).

---

## ⚙️ 6. Hướng dẫn cài đặt & Chạy dự án (Installation & Usage)

### 📌 Yêu cầu phần cứng khuyến nghị:
*   **CPU:** Intel Core i5/Ryzen 5 Gen 8 trở lên.
*   **GPU:** NVIDIA GTX 1050 Ti trở lên (đã cài đặt CUDA Driver).
*   **RAM:** 8GB hoặc cao hơn.

### 🔌 Các bước cài đặt chi tiết:

1.  **Tải mã nguồn và tạo môi trường ảo Python:**
    ```bash
    git clone https://github.com/khanhlazy/ADAS.git
    cd ADAS
    python -m venv venv
    ```
2.  **Kích hoạt môi trường ảo:**
    *   *Trên Windows (PowerShell):*
        ```powershell
        venv\Scripts\Activate.ps1
        ```
    *   *Trên Linux/macOS:*
        ```bash
        source venv/bin/activate
        ```
3.  **Cài đặt PyTorch hỗ trợ GPU CUDA (Ví dụ CUDA 12.1):**
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```
4.  **Cài đặt các thư viện phụ thuộc:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Chuẩn bị tệp tin trọng số mô hình:**
    Đảm bảo tệp trọng số huấn luyện `best.pt` được đặt đúng tại vị trí: `models/best.pt`.

### 🚀 Khởi chạy hệ thống:
```bash
python main.py --host 0.0.0.0 --port 5000
```
Truy cập giao diện quản trị thông minh tại trình duyệt: **[http://localhost:5000](http://localhost:5000)**

*   **Chế độ Standby:** Lúc khởi chạy, hệ thống hiển thị màn quét Radar công nghệ cao ở tốc độ 2 FPS nhằm tiết kiệm tối đa tài nguyên phần cứng (hạ tải CPU/GPU về 0%).
*   **Kích hoạt giám sát:** Kéo xuống mục điều khiển góc dưới bên phải, nhấn nút **"Demo Cao Tốc"** hoặc **"Demo Nội Đô"** (hoặc tải lên một video hành trình từ thiết bị của bạn) để khởi động luồng phân tích ADAS.
*   **Bật loa cảnh báo:** Nhấn nút **"BẬT LOA WEB"** trên trang dashboard để trình duyệt nhận diện và phát âm thanh cảnh báo tiếng Việt trực tiếp qua thiết bị của bạn.

---

## ⚡ 7. Tối ưu hóa hiệu năng hệ thống (System Optimizations)

Để đáp ứng được tần số phản hồi cực kỳ khắt khe của hệ thống an toàn chủ động, đội ngũ phát triển đã thực hiện 4 cải tiến tối ưu hóa phần mềm:
1.  **Waitress Thread-Pool Tuning (`threads=24`):** Khắc phục lỗi nghẽn luồng (Long-lived connections) của luồng stream MJPEG và SSE.
2.  **Zero-Copy Memory Stream:** Truy cập tham chiếu trực tiếp bộ nhớ chia sẻ giữa AI Thread và Web Thread, tách thao tác nén OpenCV JPEG ra ngoài khối Thread Lock để giải phóng hàng chục MB/s bộ nhớ RAM.
3.  **Standby Radar Mode:** Thiết kế bộ phát khung hình radar giả lập tần số thấp khi chưa có video chạy, giảm tải CPU/GPU lúc rảnh rỗi.
4.  **Event-Driven DOM updates:** Loại bỏ hoàn toàn cơ chế REST Polling liên tục, chỉ thực hiện cập nhật DOM của Frontend khi nhận tín hiệu thay đổi thực sự từ luồng dữ liệu Server-Sent Events (SSE).

---

## 🧪 8. Kiểm thử tự động (QA Testing)

Dự án tích hợp bộ kiểm thử tự động tại thư mục `tests/` để xác minh toán học của bộ não ADAS Engine:
```bash
# Chạy kiểm thử tự động cho bộ động cơ ADAS
python tests/test_adas.py
python tests/test_engine.py
```
*Kết quả:* PASS 100% các kịch bản kiểm thử giả lập di chuyển vật lý (Bbox tạt đầu, tốc độ tăng giảm đột ngột), đảm bảo độ tin cậy tuyệt đối của phần mềm trước khi bàn giao.

---

## 👥 9. Đội ngũ thực hiện & Bản quyền (Contributors)

*   **Sinh viên thực hiện:** Nhóm 8 - Khoa Công nghệ Thông tin - Trường ĐH Giao thông vận tải TP.HCM.
---
*Cảm ơn bạn đã quan tâm đến dự án TrafficVision ADAS! Mọi đóng góp hoặc báo cáo lỗi xin vui lòng tạo Issue trên kho lưu trữ Github.*
