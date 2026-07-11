# 📊 KỊCH BẢN CHI TIẾT SLIDE THUYẾT TRÌNH ĐỒ ÁN TỐT NGHIỆP
**ĐỀ TÀI: HỆ THỐNG ADAS HỖ TRỢ LÁI XE THÔNG MINH SỬ DỤNG YOLO11 VÀ THEO DÕI VẬT THỂ THỜI GIAN THỰC**

Tài liệu này được biên soạn chi tiết nhằm phục vụ công tác thiết kế slide (PowerPoint / Canva / Marp) và chuẩn bị nội dung thuyết trình, bảo vệ đồ án tốt nghiệp của Nhóm 8.

---

## 🛠 HƯỚNG DẪN THIẾT KẾ PHẦN NHÌN (VISUAL DESIGN)
- **Màu sắc chủ đạo:** Dark mode theme sang trọng (Xanh Navy đậm `#0B132B`, Xanh lục bảo `#48CAE4`, Đỏ cảnh báo rực `#D90429`, Trắng bạc `#F8F9FA`).
- **Font chữ:** Sans-serif hiện đại, rõ ràng như *Inter* hoặc *Outfit* (Google Fonts).
- **Nguyên tắc trình bày:** Tránh nhiều chữ. Dùng các thẻ (Cards), biểu đồ, sơ đồ và ký hiệu icon trực quan.

---

## 📑 BỐ CỤC CHI TIẾT TỪNG SLIDE (SLIDE DECK OUTLINE)

### SLIDE 1: Trang bìa (Cover Slide)
*   **Tiêu đề lớn:** HỆ THỐNG ADAS HỖ TRỢ LÁI XE THÔNG MINH SỬ DỤNG YOLO11 VÀ THEO DÕI VẬT THỂ THỜI GIAN THỰC
*   **Tiêu đề phụ:** Đồ án Tốt nghiệp Kỹ sư/Cử nhân Công nghệ Thông tin
*   **Thông tin thực hiện:**
    *   *Giảng viên hướng dẫn:* [Tên Giảng Viên]
    *   *Sinh viên thực hiện:* Nhóm 8 (Điền đầy đủ tên 5 thành viên)
    *   *Trường:* Đại học Giao thông vận tải TP.HCM - Khoa Công nghệ Thông tin
*   **Ý tưởng layout:** Hình nền mờ của giao diện điều khiển xe tự lái (Autopilot HUD), có các đường quét laser.

---

### SLIDE 2: Bối cảnh & Đặt vấn đề (Context & Problem Statement)
*   **Tiêu đề:** BỐ CẢNH & ĐẶT VẤN ĐỀ
*   **Nội dung chính:**
    *   **Thực trạng giao thông:** Tai nạn giao thông tại Việt Nam do mất tập trung và không giữ khoảng cách an toàn vẫn ở mức cao. Giao thông mang tính hỗn hợp (xe máy chạy đan xen ô tô mật độ dày).
    *   **Hệ thống thụ động:** Các giải pháp truyền thống (túi khí, dây đai) chỉ giảm thương vong *sau khi* va chạm xảy ra.
    *   **Hạn chế của ADAS thương mại:** Đắt đỏ (Tesla Autopilot, Mobileye) và không tối ưu cho thói quen lái xe hay mật độ xe máy dày đặc tại Việt Nam.
    *   **Câu hỏi nghiên cứu:** Làm sao xây dựng một hệ thống ADAS **giá rẻ, chạy thời gian thực trên GPU phổ thông** nhưng đạt độ chính xác cao và **không báo động giả**?
*   **Gợi ý hình ảnh:** Ảnh chụp giao thông hỗn hợp tại Việt Nam (xe máy chen lấn xung quanh ô tô).

---

### SLIDE 3: Yêu cầu hệ thống (System Requirements)
*   **Tiêu đề:** PHÂN TÍCH YÊU CẦU HỆ THỐNG
*   **Nội dung (Bảng so sánh trực quan):**
    *   **Yêu cầu chức năng (Functional - FR):**
        *   *FR01:* Nhận diện thời gian thực 7 lớp đối tượng giao thông cốt lõi.
        *   *FR02:* Bám vết liên tục (Tracking) duy trì ID vật thể qua các khung hình.
        *   *FR03:* Ước lượng khoảng cách và tính toán TTC (Time-To-Collision).
        *   *FR04:* Phát cảnh báo bằng giọng nói tiếng Việt tức thời.
        *   *FR05:* Web Dashboard trực quan cấu hình tham số.
    *   **Yêu cầu phi chức năng (Non-Functional - NFR):**
        *   *Hiệu năng:* Đạt tốc độ xử lý $\ge 25$ FPS trên phần cứng phổ thông.
        *   *Độ trễ:* Độ trễ end-to-end từ camera đến cảnh báo $< 150ms$.
        *   *UI/UX:* Phong cách Cockpit HUD, mượt mà, không giật lag DOM.

---

### SLIDE 4: Giải pháp công nghệ (Technology Stack)
*   **Tiêu đề:** GIẢI PHÁP CÔNG NGHỆ CỐT LÕI
*   **Nội dung (Trình bày dưới dạng lưới icon/logo):**
    *   **AI & Computer Vision:**
        *   *YOLO11n (Nano):* Phiên bản One-stage Detector mới nhất tối ưu hóa tham số.
        *   *ByteTrack:* Thuật toán bám vết đa đối tượng (MOT) dựa trên kết hợp IoU 2 bước.
        *   *PyTorch CUDA 12.1:* Kích hoạt tăng tốc phần cứng thông qua GPU.
    *   **Backend & Servicing:**
        *   *Flask:* Micro-framework tinh gọn cho Python Web API.
        *   *Waitress WSGI:* Máy chủ production đa luồng chuyên nghiệp trên Windows.
        *   *gTTS & PyGame:* Tạo và phát âm thanh cảnh báo bất đồng bộ.
    *   **Frontend Dashboard:**
        *   *HTML5 / Vanilla CSS / JavaScript:* Thiết kế giao diện Glassmorphism phản hồi cao.
        *   *Server-Sent Events (SSE):* Đẩy telemetry thời gian thực 1 chiều độ trễ siêu thấp.
        *   *Web Audio API:* Phát âm thanh cảnh báo trực tiếp từ trình duyệt Client.

---

### SLIDE 5: Kiến trúc đa luồng hệ thống (Multi-threading Architecture)
*   **Tiêu đề:** KIẾN TRÚC ĐA LUỒNG TỐI ƯU HIỆU NĂNG
*   **Nội dung:**
    *   **Bypass Python GIL:** Giải pháp chia tách ứng dụng thành 2 luồng độc lập giao tiếp qua Shared Memory (vùng nhớ dùng chung được bảo vệ bởi Threading Lock và Event):
        1.  **AI Pipeline (Luồng nền):** Liên tục lấy frame từ camera $\rightarrow$ Inference qua YOLO11 + ByteTrack $\rightarrow$ ADASEngine tính toán FCW $\rightarrow$ Ghi đè frame và alerts vào bộ nhớ chung $\rightarrow$ Kích hoạt `frame_update_event`.
        2.  **Flask Web (Luồng chính):** Chạy trên Waitress (`threads=24`).
            *   *Luồng 1:* Đọc frame từ bộ nhớ chung $\rightarrow$ Nén JPEG $\rightarrow$ Đẩy qua MJPEG Stream.
            *   *Luồng 2:* Chờ `frame_update_event` $\rightarrow$ Đọc cảnh báo $\rightarrow$ Gửi JSON qua SSE.
*   **Gợi ý hình ảnh:** Sơ đồ Mermaid Sequence Diagram (hoặc flowchart kiến trúc đa luồng).

---

### SLIDE 6: Luồng xử lý dữ liệu AI (AI Pipeline Data Flow)
*   **Tiêu đề:** LUỒNG XỬ LÝ DỮ LIỆU CỦA ĐỘNG CƠ AI
*   **Nội dung (Sơ đồ khối từ trái qua phải):**
    1.  **Đầu vào:** Video thô (Camera/File) $\rightarrow$ Đưa lên GPU CUDA $\rightarrow$ Resize & Chuẩn hóa.
    2.  **Nhận diện (Detection):** YOLO11n trích xuất Bounding Boxes và Class IDs.
    3.  **Bám vết (Tracking):** ByteTrack kết hợp Hungarian và IoU duy trì ID vật thể.
    4.  **Phân tích ADAS (Engine):** Xác định xe đi đầu trong làn, tính toán khoảng cách vật lý và vận tốc tương đối ($v_{rel}$).
    5.  **Cảnh báo (Decision):** Đưa ra cảnh báo FCW (SAFE/WARNING/DANGER) $\rightarrow$ Kích hoạt phát cảnh báo âm thanh bản địa và gửi dữ liệu lên HUD.

---

### SLIDE 7: Triển khai Mô hình YOLOv11n (YOLOv11n Model Training)
*   **Tiêu đề:** TRIỂN KHAI HUẤN LUYỆN MÔ HÌNH YOLOV11N
*   **Thông số huấn luyện (Trực quan hóa hình ảnh 1):**
    *   **Mô hình chọn:** **YOLOv11n** (Nano version) - Siêu nhẹ, tốc độ cao, phù hợp thiết bị Edge.
    *   **Bộ dữ liệu:** **BDD100K Subset** (Autonomous Driving Dataset) kết hợp hình ảnh đường phố Việt Nam.
    *   **Độ phân giải đầu vào:** $640 \times 640$ pixels (Resize tự động).
    *   **Batch Size:** $16$ hình ảnh/mẻ huấn luyện.
    *   **Số lượng Epochs:** $50$ chu kỳ huấn luyện hoàn chỉnh.
*   **Chiến lược tối ưu hóa suy luận (Inference Optimization):**
    *   Bật chế độ **FP16 Half-Precision** nâng tốc độ tính toán Tensor Core của GPU lên gấp đôi.
    *   Lọc bỏ 100% các lớp vật thể ngoài tầm quan tâm trực tiếp trong mã C++ của Ultralytics.

---

### SLIDE 8: Kết quả huấn luyện YOLOv11n (Training Results & Metrics)
*   **Tiêu đề:** KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH YOLOV11N
*   **Chỉ số đo lường chất lượng (Trực quan hóa hình ảnh 2):**
    *   **Precision (Độ chính xác):** $67.24\%$ (`0.67235`)
    *   **Recall (Độ nhạy):** $52.33\%$ (`0.52331`)
    *   **mAP@50:** $58.32\%$ (`0.58323`)
    *   **mAP@50-95:** $32.61\%$ (`0.32611`)
*   **Giá trị hàm mất mát (Loss Values):**
    
    | Chỉ số loss | Huấn luyện (Train) | Đánh giá (Validation) |
    | :--- | :---: | :---: |
    | **Box Loss** (Mất mát vị trí hộp) | 1.46103 | 1.37555 |
    | **Class Loss** (Mất mát phân loại) | 0.93747 | 0.81585 |
    | **DFL Loss** (Mất mát phân phối hộp) | 1.04462 | 1.00197 |
*   *Nhận xét:* Mô hình hội tụ tốt, các chỉ số loss trên tập validation thấp hơn tập train chứng tỏ không xảy ra hiện tượng quá khớp (Overfitting), mô hình có tính tổng quát hóa cao.

---

### SLIDE 9: Thuật toán Bám vết đa đối tượng ByteTrack (Multi-Object Tracking)
*   **Tiêu đề:** THUẬT TOÁN BÁM VẾT BẰNG BYTETRACK
*   **Nội dung chính:**
    *   **Giải quyết bài toán che khuất (Occlusion):** Khác với các thuật toán cũ (như SORT) vứt bỏ các hộp có độ tin cậy thấp, ByteTrack giữ lại tất cả.
    *   **Nguyên lý 2 bước liên kết (Double Association):**
        *   *Bước 1:* Liên kết các bounding box độ tin cậy cao ($\ge 0.5$) với các vết (Tracks) hiện có qua Hungarian Algorithm và IoU.
        *   *Bước 2:* So khớp các bounding box độ tin cậy thấp ($0.1 \rightarrow 0.5$) còn lại với các Tracks chưa được gán để cứu lại các vật thể bị che khuất một nửa hoặc đi vào vùng tối/bóng râm.
    *   **Làm mịn tọa độ:** Áp dụng bộ lọc Exponential Moving Average (EMA) với hệ số làm mịn $\alpha = 0.7$ để loại bỏ hiện tượng rung giật hộp (Bbox jitter).

---

### SLIDE 10: Ước lượng khoảng cách & Tính toán va chạm (ADAS Core Engine)
*   **Tiêu đề:** ĐỘNG CƠ TÍNH KHOẢNG CÁCH & THỜI GIAN VA CHẠM
*   **Công thức ước lượng khoảng cách hình học:**
    *   Kết hợp hai luồng thông tin hình học Pinhole Camera:
        1.  *Theo chiều cao hộp:* $d_{height} = \frac{H_{real} \times f}{h_{bbox}}$ (với $H_{real}$ của xe con = 1.5m, xe tải = 2.8m).
        2.  *Theo góc nghiêng mặt đất:* $d_{horizon} = \frac{h_{cam} \times f}{y_2 - y_{horizon}}$
        3.  *Khoảng cách tích hợp:* $dist = 0.6 \times d_{height} + 0.4 \times d_{horizon}$
    *   Khoảng cách 3D thực tế: $dist_{3d} = \sqrt{dist_{long}^2 + dist_{lat}^2}$
*   **Tính toán TTC (Time-To-Collision):**
    *   Vận tốc tương đối: $v_{rel} = \frac{d_{prev} - d_{current}}{\Delta t}$
    *   Làm mịn vận tốc bằng EMA ($\alpha = 0.25$) để triệt nhiễu.
    *   Thời gian va chạm: $TTC = \frac{d_{current}}{v_{rel}}$ (chỉ tính khi $v_{rel} > 0.1\text{ m/s}$).

---

### SLIDE 11: Thuật toán Thích ứng Giao thông Việt Nam (Class-Adaptive Corridor)
*   **Tiêu đề:** THUẬT TOÁN HÀNH LÀNG AN TOÀN THÍCH ỨNG (VIỆT NAM)
*   **Nội dung giải pháp đột phá:**
    *   **Thực trạng:** Giao thông đô thị Việt Nam có mật độ xe máy cực cao, thường chạy sát hai bên sườn ô tô. Nếu áp dụng hành lang an toàn cố định của phương Tây, hệ thống sẽ báo giả liên tục (False Positives).
    *   **Giải pháp "Hành lang thích ứng theo lớp xe":**
        *   *Đối với xe ô tô/xe tải:* Hành lang an toàn chiếm $38\%$ độ rộng khung hình tính từ tâm.
        *   *Đối với xe máy:* Thu hẹp hành lang an toàn xuống chỉ còn $26\%$ độ rộng khung hình.
    *   **Kết quả:** Hệ thống chỉ cảnh báo va chạm đối với xe máy tạt đầu trực tiếp trước mặt xe chủ, hoàn toàn bỏ qua các xe máy đang di chuyển an toàn bên sườn xe.
*   **Gợi ý hình ảnh:** Hình vẽ minh họa hai vùng hành lang rộng (ô tô) và hẹp (xe máy) trên khung hình đường phố.

---

### SLIDE 12: Hệ thống cảnh báo âm thanh tiếng Việt (Dual-Alert System)
*   **Tiêu đề:** HỆ THỐNG CẢNH BÁO KÉP SONG SONG (DUAL-ALERT)
*   **Kiến trúc cảnh báo hai đầu:**
    1.  **Phía Máy chủ (Backend):** Sử dụng `pygame.mixer` chạy trên một luồng phụ tách biệt.
    2.  **Phía Trình duyệt (Client-side Fallback):** Tải và cache sẵn tệp tin `.mp3` tiếng Việt bằng **Web Audio API** của HTML5. Phát trực tiếp trên thiết bị khách hàng khi nhận tín hiệu cảnh báo qua SSE. Giải quyết triệt để lỗi mất tiếng khi chạy server trên Cloud/Headless.
*   **Thuật toán điều phối âm thanh thông minh:**
    *   *Preemption (Ưu tiên ngắt lời):* Trạng thái nguy hiểm (`DANGER`) sẽ xóa sạch hàng đợi âm thanh và phát loa ngay lập tức, ngắt ngang các câu nói thông thường khác.
    *   *Cooldown (Thời gian chờ):* Thiết lập 12 giây cho mỗi loại cảnh báo để tránh việc hệ thống lặp từ liên tục gây khó chịu cho tài xế.

---

### SLIDE 13: Giao diện Web Dashboard phong cách Cockpit
*   **Tiêu đề:** GIAO DIỆN GIÁM SÁT COCKPIT GLASSMORPHISM
*   **Các tính năng nổi bật của Dashboard:**
    *   **Visual HUD Autopilot:** Luồng video trung tâm lớn, bo viền nhấp nháy đỏ/vàng sinh động tương thích với trạng thái cảnh báo nguy hiểm.
    *   **Telemetry Panel:** Hiển thị trực quan tốc độ xử lý (FPS), khoảng cách (Distance) và thời gian va chạm (TTC) của mục tiêu nguy hiểm nhất.
    *   **Live Console Log:** Đồng bộ thời gian thực 25 dòng nhật ký cuối cùng từ tệp tin log hệ thống (`logs/system.log`) lên giao diện bằng phông chữ monospace, tự động tô màu các cảnh báo nguy hiểm.
    *   **Interactive Control:** Hỗ trợ điều chỉnh thanh trượt cấu hình khoảng cách an toàn, tải video trực tiếp qua AJAX và nút Bật loa Web tiện lợi.
*   **Gợi ý hình ảnh:** Ảnh chụp màn hình Dashboard của dự án.

---

### SLIDE 14: Tối ưu hóa hiệu năng hệ thống (Engineering Optimizations)
*   **Tiêu đề:** TỐI ƯU HÓA HIỆU NĂNG & NÚT THẮT CỔ CHAI
*   **Nội dung (3 nâng cấp cốt lõi):**
    1.  **Waitress Thread-Pool Tuning (`threads=24`):** Thay vì 4 threads mặc định bị chiếm dụng bởi luồng MJPEG stream và SSE dẫn đến treo server, việc nâng lên 24 threads giúp xử lý trơn tru mọi API đồng thời.
    2.  **Standby Radar Mode (Tiết kiệm CPU/GPU):** Khi không chạy video, hệ thống tự động phát màn hình Radar HUD tĩnh ở tốc độ 2 FPS. Giúp client không bị treo chờ kết nối, giảm tải CPU/GPU hệ thống về 0% khi standby.
    3.  **Khử trùng lặp DOM (DOM Thrashing):** Sử dụng Vanilla JS kiểm tra giá trị thực sự thay đổi trước khi viết lại DOM, giảm tải CPU trình duyệt phía client.

---

### SLIDE 15: Kiểm thử tự động & Đánh giá thực nghiệm (QA & Testing)
*   **Tiêu đề:** KIỂM THỬ TỰ ĐỘNG & ĐÁNH GIÁ THỰC NGHIỆM
*   **Kiểm thử tự động (Unit Test Mocking):**
    *   Tệp `tests/test_engine.py` giả lập tọa độ Bounding Box của phương tiện đang di chuyển lại gần qua từng khung hình.
    *   Kiểm tra tính toán khoảng cách và đảm bảo TTC giảm dần chính xác $\rightarrow$ Vượt qua (Pass) 100% các ca kiểm thử toán học.
*   **Chỉ số hiệu năng thực nghiệm (Laptop Gaming GPU GTX 1650):**
    
    | Công đoạn xử lý | Thời gian (ms) | Ghi chú |
    | :--- | :---: | :--- |
    | GPU Preprocessing | 0.5 ms | Chạy trên CUDA |
    | YOLO11n Inference | 16.0 ms | Chạy trên CUDA |
    | ByteTrack | 2.0 ms | Thuật toán tối ưu hóa |
    | ADAS Engine | 0.5 ms | Phép toán hình học nhẹ |
    | **Tổng thời gian xử lý** | **19.0 ms** | **Đạt tốc độ ~50 FPS (Real-time mượt mà)** |

---

### SLIDE 16: Hướng phát triển tương lai (Future Roadmap)
*   **Tiêu đề:** HƯỚNG PHÁT TRIỂN TƯƠNG LAI
*   **Nội dung chính:**
    1.  **Tích hợp Lane Detection học sâu:** Tích hợp mô hình phân đoạn làn đường (như Ultra-Fast Lane Detection) để đo độ lệch làn chủ động (LDW).
    2.  **Giao thức truyền tải WebRTC:** Thay thế MJPEG Stream bằng WebRTC mã hóa H.264 trực tiếp trên GPU để giảm băng thông từ 15Mbps xuống 1Mbps.
    3.  **Hệ thống DMS cảnh báo ngủ gật:** Lắp đặt camera trong cabin, nhận diện khuôn mặt và hướng mắt tài xế để cảnh báo mất tập trung.
    4.  **Biên dịch sang TensorRT (.engine):** Triển khai biên dịch mô hình đạt tốc độ $> 60$ FPS trên các bo mạch nhúng Edge AI giá rẻ (Jetson Nano/Orin).

---

### SLIDE 17: Kết luận & Hỏi đáp (Q&A)
*   **Tiêu đề:** KẾT LUẬN & HỎI ĐÁP
*   **Nội dung tóm tắt:**
    *   Đồ án đã thiết kế và triển khai hoàn thiện hệ thống ADAS đáp ứng tốc độ thời gian thực (50 FPS) trên GPU phổ thông.
    *   Đóng góp thuật toán "Hành lang thích ứng theo lớp" giải quyết đặc thù giao thông đô thị hỗn hợp Việt Nam.
    *   Xây dựng giao diện Cockpit hiện đại và hệ thống âm thanh cứu mạng đồng bộ.
*   **Lời cảm ơn:** Nhóm xin chân thành cảm ơn Hội đồng bảo vệ và Giảng viên hướng dẫn!
*   **Ý tưởng layout:** Chữ "HỎI ĐÁP / Q&A" lớn ở trung tâm đi kèm thông tin liên hệ của nhóm.

---
*(Hết tài liệu kịch bản Slide)*
