# 📋 KẾ HOẠCH DỰ ÁN TỔNG THỂ (MASTER TASK PLAN) - DỰ ÁN ADAS

Tài liệu này quản lý toàn bộ vòng đời phát triển phần mềm (SDLC) của dự án hệ thống ADAS, từ khâu khởi tạo, R&D đến khi bàn giao và bảo trì.

---

## 📍 Giai đoạn 1: Phân tích và Thiết kế Hệ thống (Phase 1: Analysis & Design)
**Trạng thái: Hoàn Thành (Done)**
- [x] Phân tích yêu cầu hệ thống và lập ma trận tính năng (User Requirement & Feature Matrix).
- [x] Lựa chọn công nghệ cốt lõi: YOLO11 (Phát hiện vật thể), ByteTrack (Theo dõi), Flask (Backend).
- [x] Thiết kế kiến trúc tổng thể, vẽ sơ đồ UML, Sequence Diagram, Data Flow.
- [x] Thiết kế luồng dữ liệu đa luồng (Multi-threading) để tối đa hóa hiệu năng GPU.
- [x] Thiết kế giao diện đồ họa Web Dashboard (UI/UX) mang phong cách Glassmorphism.

## 📍 Giai đoạn 2: Chuẩn bị Dữ liệu & Môi trường (Phase 2: Data & Environment)
**Trạng thái: Hoàn Thành (Done)**
- [x] Cài đặt môi trường Python ảo (`venv`), cài đặt CUDA 12.1, PyTorch GPU.
- [x] Thu thập, lọc và gán nhãn tập dữ liệu BDD100k kết hợp với video đường phố Việt Nam.
- [x] Huấn luyện mô hình YOLO11 với 7 lớp đối tượng giao thông (car, moto, bus, truck, person, light, sign).
- [x] Thu thập các video mẫu (Sample Videos) để kiểm thử (Mưa, nắng, ban đêm, cao tốc, đường kẹt xe).

## 📍 Giai đoạn 3: R&D Mô hình AI & Xử lý Ảnh (Phase 3: AI Development)
**Trạng thái: Hoàn Thành (Done) - *Đã Refactor OOP***
- [x] **Object Detection & Tracking:** Tích hợp bộ đôi YOLO11 + ByteTrack.
- [ ] **Lane Detection & Warning:** (Tạm hoãn / Loại khỏi phạm vi phiên bản hiện tại do chưa thực hiện)

## 📍 Giai đoạn 4: Xây dựng Logic ADAS (Phase 4: ADAS Engine Logic)
**Trạng thái: Hoàn Thành (Done)**
- [x] Xây dựng thuật toán tính khoảng cách hình học Camera (Distance Estimation).
- [x] Xây dựng công cụ bộ lọc EMA (Exponential Moving Average) để làm mượt vận tốc.
- [x] Tính toán chỉ số TTC (Time-To-Collision) và đưa ra quyết định cảnh báo (FCW).
- [x] Triển khai chiến lược **Class-Adaptive Corridor**: Thu hẹp khu vực cảnh báo nguy hiểm với lớp xe máy (motorcycle) xuống 26% để phù hợp đường phố Việt Nam.
- [x] Xây dựng Alert System: Hàng đợi (Queue) phát âm thanh tiếng Việt bằng gTTS. Có cơ chế Cooldown và Preemption (Ngắt lời khi khẩn cấp).

## 📍 Giai đoạn 5: Phát triển Web Dashboard (Phase 5: Backend & UI/UX)
**Trạng thái: Hoàn Thành (Done)**
- [x] Xây dựng Backend Flask xử lý API và stream MJPEG.
- [x] Xây dựng Giao diện Web (HTML5/CSS3/JS) với các khối HUD trực quan.
- [x] Binding các input từ Web tới Core AI thông qua RESTful API để tùy chỉnh ngưỡng an toàn.
- [x] Cơ chế Upload Video và điều khiển luồng (Pause/Resume) đồng bộ cả hình ảnh và âm thanh.

## 📍 Giai đoạn 6: Tối ưu hóa Hiệu năng & Kiểm thử (Phase 6: QA & Optimization)
**Trạng thái: Hoàn Thành (Done)**
- [x] Cấu hình chạy streaming cài gói pip (loại bỏ lỗi tràn RAM MemoryError).
- [x] Triển khai **Waitress Thread-Pool Tuning (`threads=24`)** để xử lý song song không nghẽn luồng.
- [x] Triển khai **Standby Radar Mode (2 FPS)** giúp giải phóng CPU/GPU và thông báo trạng thái sẵn sàng.
- [x] Triển khai **Web Audio API** phía Client giải quyết vấn đề Headless/Cloud deployment mất âm thanh.
- [x] Tích hợp **Console Log Monospace** thời gian thực kéo log từ `logs/system.log`.
- [x] Chạy Stress Test hệ thống trong 6h đồng hồ để đảm bảo không bị rò rỉ bộ nhớ.
- [x] Thực hiện Functional Test trên card GTX 1650, ghi nhận tốc độ ổn định 30-35 FPS.
- [x] Fix hoàn toàn lỗi crash unicode khi log tiếng Việt trên Windows Terminal.

## 📍 Giai đoạn 7: Đóng gói và Bàn giao (Phase 7: Packaging & Handover)
**Trạng thái: Đang thực hiện (In Progress)**
- [x] Cấu trúc lại toàn bộ hệ thống tài liệu Markdown (`docs/`) theo chuẩn Enterprise và nộp đồ án.
- [x] Hoàn thiện `README.md` với Badges, hướng dẫn sử dụng và cấu trúc API.
- [ ] Báo cáo đồ án: Soạn Slide thuyết trình PPTX chuyên nghiệp.
- [ ] Quay Video Demo: Dựng video (2-3 phút) trình diễn các ca khó (đường đông xe máy, chuyển làn, trời mưa).
- [ ] Đóng gói Portable/Executable bằng PyInstaller (Tùy chọn nếu cần nộp file chạy).

## 📍 Giai đoạn 8: Phạm vi Tương lai (Future Expansion)
**Trạng thái: Backlog**
- [ ] Triển khai convert mô hình PyTorch sang TensorRT (`.engine`) để deploy lên thiết bị nhúng Jetson Nano/Orin.
- [ ] Kết nối thiết bị thu thập tọa độ GPS để vẽ bản đồ rủi ro (Risk Map) hành trình.
- [ ] Tích hợp camera thứ hai vào cabin để làm DMS (Driver Monitoring System - cảnh báo ngủ gật).
