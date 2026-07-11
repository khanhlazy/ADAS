import os
# Tắt cảnh báo log nội bộ của OpenCV (như lỗi không tìm thấy camera)
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
import sys
import argparse
import threading
import time

# Cấu hình encoding UTF-8 cho Windows console để tránh lỗi hiển thị tiếng Việt
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import datetime
class Logger(object):
    def __init__(self, filename="logs/system.log"):
        self.terminal = sys.stdout
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.log = open(filename, "a", encoding="utf-8")
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log.write(f"\n\n{'='*60}\n[START] NEW SESSION RECORDED AT: {timestamp}\n{'='*60}\n")
        self.log.flush()

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()
        
    def reconfigure(self, **kwargs):
        pass

# Ghi đè bộ xuất chuẩn để lưu song song ra file
sys.stdout = Logger("logs/system.log")
sys.stderr = sys.stdout

from src.config_loader import config_inst

def print_banner():
    """In banner giới thiệu đồ án bằng tiếng Việt"""
    banner = """
======================================================================
  HỆ THỐNG TRỢ LÁI THÔNG MINH (ADAS) PHÁT HIỆN LÀN ĐƯỜNG & VẬT THỂ
      Đồ án môn học - Xử lý ảnh và thị giác máy tính
======================================================================
[INFO] Đang khởi động hệ thống, vui lòng chờ giây lát...
[INFO] Lập trình và Thiết kế: Trường ĐH Giao thông vận tải TP.HCM - Nhóm 8
======================================================================
    """
    print(banner)

def check_model_file():
    """Kiểm tra sự tồn tại của mô hình best.pt"""
    model_path = config_inst.get("model.path", "models/best.pt")
    if not os.path.exists(model_path):
        print(f"[CẢNH BÁO] Không tìm thấy file trọng số YOLO11n tại: '{model_path}'")
        print("[HƯỚNG DẪN] Bạn cần copy file 'best.pt' đã được huấn luyện vào thư mục 'models/'.")
        print("[GỢI Ý] Hệ thống sẽ thử tự động tải mô hình yolo11n.pt mặc định để chạy demo.")
        
        # Tạo thư mục models nếu chưa có
        os.makedirs("models", exist_ok=True)
        # Tải mô hình mặc định từ Ultralytics làm phương án dự phòng (fallback)
        try:
            from ultralytics import YOLO
            print("[INFO] Đang tải mô hình yolo11n.pt từ Ultralytics làm dự phòng...")
            yolo = YOLO("yolo11n.pt")
            # Di chuyển/Rename sang models/best.pt để chạy trực tiếp
            os.rename("yolo11n.pt", model_path)
            print(f"[SUCCESS] Đã tải và lưu thành công mô hình dự phòng tại '{model_path}'")
        except Exception as e:
            print(f"[ERROR] Không thể tự động tải mô hình dự phòng. Lỗi: {e}")
            print("[CRITICAL] Chương trình có thể chạy ở chế độ mô phỏng (không tải được AI).")

if __name__ == "__main__":
    print_banner()
    
    # Phân tích tham số dòng lệnh (Command line arguments)
    parser = argparse.ArgumentParser(description="Hệ thống ADAS hỗ trợ lái xe thông minh thời gian thực")
    parser.add_argument("--source", type=str, default=None, 
                        help="Đường dẫn file video, đường dẫn luồng RTSP hoặc chỉ số camera USB (Ví dụ: 0)")
    parser.add_argument("--host", type=str, default=config_inst.get("server.host", "127.0.0.1"), 
                        help="Địa chỉ Host chạy Flask Web Server")
    parser.add_argument("--port", type=int, default=config_inst.get("server.port", 5000), 
                        help="Cổng kết nối Flask Web Server")
    args = parser.parse_args()

    # Kiểm tra và xử lý nguồn video đầu vào (Chuyển chuỗi số sang số nguyên cho camera index)
    source_input = args.source
    if source_input is None:
        source_input = ""  # Bắt đầu trống để người dùng tự chọn tải video từ giao diện Web UI
        print("[INFO] Hệ thống khởi động ở chế độ chờ tải tệp Video từ Dashboard...")
    else:
        if source_input.isdigit():
            source_input = int(source_input)
            print(f"[INFO] Sử dụng thiết bị Camera USB, Index: {source_input}")
        else:
            if os.path.exists(source_input):
                print(f"[INFO] Sử dụng nguồn Video file: '{source_input}'")
            else:
                print(f"[INFO] Sử dụng nguồn RTSP Stream: '{source_input}'")

    # Kiểm tra file trọng số mô hình
    check_model_file()

    # Import các thành phần Flask và luồng chạy ngầm sau khi cấu hình
    from src.app import app, start_pipeline_thread, is_running
    import src.app as app_module

    # Gán nguồn video nguồn vào Flask app module
    app_module.video_source = source_input

    # Khởi chạy luồng ADAS Pipeline chạy song song dưới nền (Daemon Thread)
    pipeline_thread = threading.Thread(
        target=start_pipeline_thread, 
        args=(source_input,), 
        daemon=True
    )
    pipeline_thread.start()
    print("[INFO] ADAS Processing Engine Thread đã được khởi chạy.")

    # Cho phép hệ thống tải và chạy ổn định trước khi mở cổng Web
    time.sleep(1.0)
    print(f"[INFO] Khởi chạy Web Dashboard tại địa chỉ: http://{args.host}:{args.port}")

    # Khởi chạy Flask Web Server bằng Waitress (WSGI cho Production)
    try:
        from waitress import serve
        print(f"[INFO] Bắt đầu khởi chạy Waitress WSGI server trên {args.host}:{args.port}...")
        serve(app, host=args.host, port=args.port, threads=24)
    except KeyboardInterrupt:
        print("\n[INFO] Đang đóng hệ thống ADAS...")
        app_module.is_running = False
        pipeline_thread.join(timeout=2)
        print("[SUCCESS] Đã tắt hệ thống ADAS an toàn. Tạm biệt!")
