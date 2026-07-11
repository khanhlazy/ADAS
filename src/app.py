import cv2
import time
import threading
import os
import json
import concurrent.futures
from werkzeug.utils import secure_filename
from flask import Flask, render_template, Response, jsonify, request

from src.detector import YOLODetector
from src.lane_detector import LaneDetector
from src.tracker import ByteTracker
from src.adas_engine import ADASEngine
from src.alert_system import AlertSystem
from src.config_loader import config_inst

app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

# Biến toàn cục lưu trữ trạng thái hệ thống
global_frame = None
global_alerts = {
    "fps": 0.0,
    "ldw_status": "BÌNH THƯỜNG",
    "ldw_offset": 0.0,
    "fcw_status": "SAFE",
    "target_vehicle": None,
    "objects_detected": {
        "car": 0, "motorcycle": 0, "bus": 0, "truck": 0,
        "person": 0, "traffic sign": 0, "traffic light": 0
    },
    "curvature": 0.0
}

# Các đối tượng điều khiển luồng
pipeline_lock = threading.Lock()
frame_update_event = threading.Event()
video_source = 0  # Camera mặc định
is_running = True
is_pipeline_paused = False
global_pipeline = None

# Định nghĩa bảng màu vẽ overlay
COLORS = {
    "car": (0, 255, 0),        # Xanh lá
    "motorcycle": (255, 255, 0), # Vàng chanh
    "bus": (0, 255, 255),      # Vàng cát
    "truck": (255, 165, 0),    # Cam
    "person": (255, 105, 180), # Hồng cánh sen
    "traffic sign": (255, 0, 255), # Tím
    "traffic light": (0, 191, 255), # Xanh dương sáng
    "lead_danger": (0, 0, 255), # Đỏ (Cực kỳ nguy hiểm)
    "lead_warning": (0, 255, 255), # Vàng (Cảnh báo)
}

class ADASPipeline:
    def __init__(self, source):
        self.source = source
        self.detector = YOLODetector()
        self.lane_detector = LaneDetector()
        self.tracker = ByteTracker()
        self.adas_engine = ADASEngine()
        self.alert_system = AlertSystem()
        self.show_lane = True
        
        # Đọc độ phân giải xử lý từ cấu hình
        self.video_width = config_inst.get("video.width", 640)
        self.video_height = config_inst.get("video.height", 360)
        
        # Mở luồng camera hoặc file video (nếu rỗng thì khởi tạo đối tượng rỗng)
        self.cap = cv2.VideoCapture(self.source if self.source else "")
        if self.cap.isOpened():
            has_frame, _ = self.cap.read()
            if not has_frame:
                print(f"[WARNING] Could not read from source: {self.source}")
                self.cap.release()

    def draw_overlays(self, frame, results):
        """
        Vẽ Bounding Boxes của phương tiện (kèm ID, khoảng cách), 
        thông báo FCW, LDW và bảng HUD hệ thống lên khung hình.
        """
        h, w = frame.shape[:2]
        fcw = results["fcw_status"]
        ldw = results["ldw_status"]
        offset = results["ldw_offset"]
        target = results["target_vehicle"]
        all_objs = results["all_objects"]
        
        # Vẽ các xe được track
        for obj in all_objs:
            x1, y1, x2, y2 = [int(coord) for coord in obj["bbox"]]
            obj_id = obj["id"]
            class_id = obj["class_id"]
            distance = obj["distance"]
            in_lane = obj["in_lane"]
            
            # Tên lớp
            class_name = self.detector.class_names.get(class_id, "Unknown")
            
            # Chọn màu vẽ
            color = COLORS.get(class_name, (255, 255, 255))
            
            # Kiểm tra nếu là Xe Đi Đầu (Lead Vehicle)
            is_lead = (target is not None and obj_id == target["id"])
            
            if is_lead:
                if fcw == "DANGER":
                    color = COLORS["lead_danger"]
                    thickness = 3
                elif fcw == "WARNING":
                    color = COLORS["lead_warning"]
                    thickness = 3
                else:
                    color = (0, 200, 255) # Xanh dương lục
                    thickness = 2
            else:
                thickness = 1 if not in_lane else 2

            # Vẽ bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # TỐI ƯU CẢNH BÁO: Chỉ vẽ nhãn thông tin cho Phương tiện & Người
            if class_id in [0, 1, 2, 3, 4]:
                target_pt = ((x1 + x2) // 2, y2)
                
                # KHẮC PHỤC MẠNG NHỆN LASER: Chỉ vẽ 1 dây Radar DUY NHẤT tới Target Vehicle
                # (Tránh trường hợp nhận diện làn đường sai khiến mọi xe đều bị nhận là in_lane)
                target_id = results["target_vehicle"]["id"] if results["target_vehicle"] else None
                is_target = (obj_id == target_id)
                
                if is_target:
                    origin_pt = (w // 2, h - 15)
                    cv2.line(frame, origin_pt, target_pt, color, 3, cv2.LINE_AA)
                    cv2.circle(frame, target_pt, 5, color, -1, cv2.LINE_AA)
                
                # Vẽ nhãn thông tin Tracking ID và khoảng cách
                label = f"ID:{obj_id} | {distance:.1f}m"
                if is_lead:
                    label = f"[LEAD] ID:{obj_id} | {distance:.1f}m"
                    
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.rectangle(frame, (x1, y1 - 18), (x1 + text_w, y1), color, -1)
                
                text_color = (0, 0, 0)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1, cv2.LINE_AA)

        # Cảnh báo âm thanh và Dashboard Logs
        if fcw == "DANGER":
            self.alert_system.trigger_alert("fcw_danger")
        elif fcw == "WARNING":
            self.alert_system.trigger_alert("fcw_warning")

        if ldw == "LỆCH TRÁI":
            self.alert_system.trigger_alert("ldw_left")
        elif ldw == "LỆCH PHẢI":
            self.alert_system.trigger_alert("ldw_right")

        # Vẽ tâm điểm cảm biến (Ego-origin - Red dot) ở đáy màn hình
        origin_pt = (w // 2, h - 15)
        cv2.circle(frame, origin_pt, 6, (0, 0, 255), -1, cv2.LINE_AA) # Nhân màu đỏ
        cv2.circle(frame, origin_pt, 8, (255, 255, 255), 1, cv2.LINE_AA) # Viền trắng
        
        return frame

    def run(self):
        global global_frame, global_alerts, is_running, video_source, is_pipeline_paused
        
        current_source = self.source
        fps_limiter_dt = 1.0 / 50.0  # Giới hạn tối đa 50 FPS
        
        # TỐI ƯU HÓA LUỒNG & BỘ NHỚ CẤP DOANH NGHIỆP (ENTERPRISE OPTIMIZATION):
        # Tạo 1 ThreadPool duy nhất chạy xuyên suốt vòng đời hệ thống.
        # Khắc phục hoàn toàn lỗi RuntimeError khi đóng ứng dụng và 
        # loại bỏ chi phí Context-Switching khổng lồ khi tạo thread mới mỗi khung hình.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            while is_running:
                # Nếu đang tạm dừng, tắt tiếng cảnh báo và ngủ ngắn để tiết kiệm tài nguyên
                if is_pipeline_paused:
                    self.alert_system.clear_queue_and_stop()
                    time.sleep(0.2)
                    continue

                # Kiểm tra xem nguồn video toàn cục có bị thay đổi từ bên ngoài không (như qua upload file)
                if video_source != current_source:
                    print(f"[INFO] Chuyển nguồn video từ {current_source} sang {video_source}")
                    self.cap.release()
                    self.cap = cv2.VideoCapture(video_source)
                    current_source = video_source
                    # Reset tracking history để tránh nhảy ID
                    self.tracker = ByteTracker(max_age=25, min_hits=2, iou_threshold=0.3)
                    self.adas_engine.history_distance.clear()
                    continue

                start_time = time.time()
                
                ret, frame = self.cap.read()
                if not ret:
                    # Nếu chạy bằng file video, tự động lặp lại video khi kết thúc
                    if isinstance(current_source, str) and os.path.exists(current_source):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        time.sleep(0.5)
                        continue

                # Tiền xử lý điều chỉnh độ phân giải về kích thước cấu hình để tối ưu hóa hiệu năng (tăng FPS mượt mà)
                h, w = frame.shape[:2]
                if w != self.video_width or h != self.video_height:
                    frame = cv2.resize(frame, (self.video_width, self.video_height))

                # Chạy YOLO11 (GPU Bound) và Lane Detection (CPU Bound) SONG SONG trên Executor có sẵn
                try:
                    t_yolo_start = time.time()
                    
                    # Đồng bộ hóa bỏ qua khung hình (skip frame) cho cả YOLO và Lane Segmentation
                    # Chạy cả 2 mô hình trên khung hình lẻ, tái sử dụng kết quả trên khung hình chẵn
                    run_yolo = (self.lane_detector.frame_counter % 2 == 0)
                    
                    if run_yolo:
                        future_yolo = executor.submit(self.detector.detect, frame)
                    else:
                        future_yolo = None
                        
                    future_lane = executor.submit(self.lane_detector.detect_lanes, frame, self.show_lane)
                    
                    if future_yolo is not None:
                        detections = future_yolo.result()
                        self.last_detections = detections
                    else:
                        detections = self.last_detections if hasattr(self, "last_detections") else []
                        
                    t_yolo_end = time.time()
                    
                    frame_with_lane, offset, left_fit, right_fit, curvature = future_lane.result()
                    t_lane_end = time.time()
                except RuntimeError:
                    # Bỏ qua lỗi khi Python interpreter tự động đóng ThreadPoolExecutor lúc tắt app (Ctrl+C)
                    break
            
                # 2. Tracking ByteTrack (Nhanh, chạy tuần tự sau YOLO)
                tracked_objects = self.tracker.update(detections)
                
                # 3. Phân tích ADAS Engine
                self.adas_engine.horizon_ratio = self.lane_detector.horizon_ratio
                adas_results = self.adas_engine.analyze(tracked_objects, left_fit, right_fit, offset, frame.shape)
                
                # 5. Vẽ overlay kết quả lên ảnh
                processed_frame = self.draw_overlays(frame_with_lane, adas_results)

                # Cập nhật trạng thái đếm số vật thể phát hiện được
                counts = {
                    "car": 0, "motorcycle": 0, "bus": 0, "truck": 0,
                    "person": 0, "traffic sign": 0, "traffic light": 0
                }
                for det in detections:
                    class_id = int(det[5])
                    class_name = self.detector.class_names.get(class_id, "")
                    if class_name in counts:
                        counts[class_name] += 1

                # 6. Tính toán FPS và cập nhật biến toàn cục
                end_time = time.time()
                process_dt = end_time - start_time
                current_fps = 1.0 / process_dt if process_dt > 0 else 30.0

                # In thông số hiệu năng mỗi 50 frames để phân tích bottleneck (cả chẵn và lẻ)
                f_count = self.lane_detector.frame_counter
                if f_count % 50 in (0, 1):
                    yolo_dt = (t_yolo_end - t_yolo_start) * 1000
                    lane_wait_dt = (t_lane_end - t_yolo_end) * 1000
                    total_dt = process_dt * 1000
                    print(f"[PERF] Frame {f_count} | run_yolo: {run_yolo} | YOLO {yolo_dt:.1f}ms | Lane Wait {lane_wait_dt:.1f}ms | Total {total_dt:.1f}ms (FPS: {current_fps:.1f})")

                with pipeline_lock:
                    global_frame = processed_frame.copy()
                    global_alerts = {
                        "fps": current_fps,
                        "ldw_status": adas_results["ldw_status"],
                        "ldw_offset": adas_results["ldw_offset"],
                        "fcw_status": adas_results["fcw_status"],
                        "target_vehicle": adas_results["target_vehicle"],
                        "objects_detected": counts,
                        "curvature": curvature
                    }
                
                # Gửi tín hiệu thông báo có frame mới để Backend đẩy qua SSE
                frame_update_event.set()

                # Khống chế khung hình theo FPS đích để video chạy đúng tốc độ thực tế
                sleep_time = fps_limiter_dt - (time.time() - start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        self.cap.release()

def start_pipeline_thread(source):
    global global_pipeline
    global_pipeline = ADASPipeline(source)
    global_pipeline.run()

@app.route('/')
def index():
    """Trang chủ Dashboard"""
    return render_template('index.html')

def make_standby_frame(w=640, h=360):
    """Tạo khung hình chờ phong cách công nghệ cao khi chưa tải video"""
    import numpy as np
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Vẽ viền và tâm ngắm radar
    cv2.rectangle(img, (20, 20), (w-20, h-20), (50, 40, 20), 1, cv2.LINE_AA)
    cx, cy = w // 2, h // 2
    cv2.circle(img, (cx, cy), 50, (40, 30, 15), 1, cv2.LINE_AA)
    cv2.circle(img, (cx, cy), 100, (40, 30, 15), 1, cv2.LINE_AA)
    cv2.line(img, (cx - 140, cy), (cx + 140, cy), (40, 30, 15), 1, cv2.LINE_AA)
    cv2.line(img, (cx, cy - 140), (cx, cy + 140), (40, 30, 15), 1, cv2.LINE_AA)
    
    # Văn bản hướng dẫn
    text1 = "TRAFFICVISION ADAS - STANDBY"
    text2 = "CHON VIDEO DEMO HOAC TAI TEP LEN"
    text3 = "DE BAT DAU TRAI NGHIEM"
    
    cv2.putText(img, text1, (cx - 165, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 210, 0), 2, cv2.LINE_AA)
    cv2.putText(img, text2, (cx - 180, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 139), 1, cv2.LINE_AA)
    cv2.putText(img, text3, (cx - 110, cy + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 139), 1, cv2.LINE_AA)
    return img

def gen_frames():
    """Bộ tạo luồng (generator) sinh ảnh JPEG phục vụ Motion JPEG (MJPEG) stream"""
    global global_frame
    standby_frame = None
    while is_running:
        local_frame = None
        with pipeline_lock:
            if global_frame is not None:
                local_frame = global_frame.copy()
        
        # Nếu chưa có frame từ video, hiển thị ảnh chờ standby để giải phóng hàng đợi threads
        if local_frame is None:
            if standby_frame is None:
                standby_frame = make_standby_frame()
            local_frame = standby_frame
            sleep_dt = 0.5  # Chạy 2 FPS khi standby để tiết kiệm CPU tối đa
        else:
            sleep_dt = 0.02  # ~50 FPS khi chạy video bình thường
            
        ret, buffer = cv2.imencode('.jpg', local_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(sleep_dt)

@app.route('/video_feed')
def video_feed():
    """Endpoint cung cấp luồng video trực tiếp"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/alerts')
def api_alerts():
    """Endpoint Server-Sent Events (SSE) đẩy dữ liệu ADAS realtime về Frontend, dứt điểm lỗi Polling."""
    def generate():
        while is_running:
            # Đợi cho tới khi luồng AI báo hiệu có frame mới (timeout 1 giây để tránh dead-lock)
            if frame_update_event.wait(timeout=1.0):
                frame_update_event.clear()
                with pipeline_lock:
                    data = json.dumps(global_alerts)
                yield f"data: {data}\n\n"
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

@app.route('/api/logs')
def api_logs():
    """Trích xuất 25 dòng log cuối cùng từ logs/system.log để đưa lên Web Console"""
    log_path = "logs/system.log"
    if not os.path.exists(log_path):
        return jsonify([])
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Lấy 25 dòng cuối không rỗng
            last_lines = [line.strip() for line in lines[-25:] if line.strip()]
            return jsonify(last_lines)
    except Exception as e:
        return jsonify([f"[ERROR] Không thể đọc log: {e}"])

@app.route('/api/config', methods=['POST'])
def api_config():
    """Endpoint nhận chỉnh sửa ngưỡng cài đặt từ UI"""
    global global_pipeline
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Payload JSON rỗng"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Dữ liệu JSON không hợp lệ"}), 400
        
    print(f"[CONFIG] Received new config parameters: {data}")
    
    if global_pipeline is not None:
        with pipeline_lock:
            # Cập nhật các thông số an toàn cho ADAS Engine
            if 'safe_distance' in data:
                safe_dist = float(data['safe_distance'])
                global_pipeline.adas_engine.safe_distance_warning = safe_dist
                global_pipeline.adas_engine.safe_distance_danger = safe_dist * 0.6
                print(f"[CONFIG] Updated warning distance to {safe_dist}m and danger distance to {safe_dist * 0.6:.1f}m")
            if 'ttc_threshold' in data:
                ttc_val = float(data['ttc_threshold'])
                global_pipeline.adas_engine.ttc_warning = ttc_val
                global_pipeline.adas_engine.ttc_danger = ttc_val * 0.6
                print(f"[CONFIG] Updated warning TTC to {ttc_val}s and danger TTC to {ttc_val * 0.6:.1f}s")
            if 'show_lane' in data:
                global_pipeline.show_lane = bool(data['show_lane'])
                print(f"[CONFIG] Updated show_lane to {global_pipeline.show_lane}")
            if 'voice_enabled' in data:
                global_pipeline.alert_system.sound_enabled = bool(data['voice_enabled'])
                global_pipeline.alert_system.voice_enabled = bool(data['voice_enabled'])
                print(f"[CONFIG] Updated voice_enabled to {global_pipeline.alert_system.voice_enabled}")
            if 'volume' in data:
                vol = float(data['volume'])
                global_pipeline.alert_system.volume = vol
                try:
                    import pygame
                    pygame.mixer.music.set_volume(vol)
                except Exception:
                    pass
                print(f"[CONFIG] Updated volume to {vol}")
                
    return jsonify({"status": "success", "message": "Cấu hình đã được cập nhật thành công!"})

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("models", exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def api_upload():
    global video_source
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Không tìm thấy file nào được gửi lên"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Tên file không hợp lệ"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"status": "error", "message": "Tên file không hợp lệ sau khi làm sạch"}), 400
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Cập nhật video_source toàn cục
        with pipeline_lock:
            video_source = filepath
            
        print(f"[UPLOAD] Video file uploaded and saved to: {filepath}")
        return jsonify({
            "status": "success", 
            "message": f"Tải lên thành công! Đang chuyển sang xử lý tệp: {filename}",
            "filepath": filepath
        })
    else:
        return jsonify({"status": "error", "message": "Định dạng file không được hỗ trợ. Chỉ hỗ trợ mp4, avi, mkv, mov, webm"}), 400

@app.route('/api/select_video', methods=['POST'])
def api_select_video():
    global video_source
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
        
    filename = data.get('filename')
    if not filename:
        return jsonify({"status": "error", "message": "Không nhận diện được tên tệp video"}), 400
        
    # Sửa lỗi bảo mật Path Traversal bằng os.path.basename & abspath
    filename = secure_filename(os.path.basename(filename))
    if not filename:
        return jsonify({"status": "error", "message": "Tên file không hợp lệ"}), 400
        
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
    
    # Đảm bảo filepath cuối cùng vẫn nằm trong thư mục UPLOAD_FOLDER và là tệp tin thực tế
    if not filepath.startswith(upload_dir) or not os.path.isfile(filepath):
        return jsonify({"status": "error", "message": "File không tồn tại hoặc đường dẫn không hợp lệ."}), 404
        
    with pipeline_lock:
        video_source = filepath
        
    print(f"[CONTROL] Chuyển nguồn video phát sang: {filepath}")
    return jsonify({
        "status": "success",
        "message": f"Đã chuyển nguồn phát sang: {filename}"
    })

@app.route('/api/control', methods=['POST'])
def api_control():
    global is_pipeline_paused, global_pipeline
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
        
    action = data.get('action')
    if action == 'pause':
        is_pipeline_paused = True
        if global_pipeline:
            global_pipeline.alert_system.clear_queue_and_stop()
        print("[CONTROL] ADAS Pipeline paused.")
    elif action == 'resume':
        is_pipeline_paused = False
        print("[CONTROL] ADAS Pipeline resumed.")
    return jsonify({"status": "success", "is_paused": is_pipeline_paused})
