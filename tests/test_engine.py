import sys
import os
import time
import numpy as np

# Cấu hình encoding UTF-8 cho Windows console để tránh lỗi hiển thị tiếng Việt
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Đảm bảo có thể import được src package từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adas_engine import ADASEngine

class MockTrack:
    """Class giả lập một đối tượng trả về từ ByteTrack"""
    def __init__(self, track_id, bbox, class_id):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.class_id = class_id
        self.distance = float('inf')
        self.ttc = float('inf')

def test_distance_and_ttc():
    """Kiểm thử thuật toán tính toán Khoảng cách và Thời gian va chạm (TTC)"""
    engine = ADASEngine(camera_height=1.35, horizon_ratio=0.55)
    
    frame_shape = (360, 640, 3)
    frame_height = frame_shape[0]
    
    # 1. KHUNG HÌNH ĐẦU TIÊN
    # Giả lập một chiếc xe (class_id = 0) ở vị trí y2 = 300 (tiếp đất)
    track1 = MockTrack(track_id=1, bbox=np.array([220, 200, 380, 300]), class_id=0)
    
    results_f1 = engine.analyze([track1], left_fit=None, right_fit=None, offset=0.0, frame_shape=frame_shape)
    
    # Tính tay d = 1.35 * (450 * 360/720) / (300 - 360*0.55)
    # y_horizon = 198
    # Using the combined formula:
    # dist_height = (1.5 * 580) / 100 = 8.7m
    # dist_horizon = 303.75 / (300 - 198) = 2.9779m
    # dist_long = 0.6 * 8.7 + 0.4 * 2.9779 = 6.4112m
    # dist_3d = sqrt(6.4112^2 + lateral^2) = ~6.415m
    dist_f1 = engine.history_distance[1][0]
    
    print(f"Khoảng cách Frame 1: {dist_f1:.4f}m")
    assert 6.3 < dist_f1 < 6.5, f"LỖI: Khoảng cách tính ra sai! Mong đợi ~6.41m, nhận được {dist_f1}m"
    
    # 2. KHUNG HÌNH THỨ HAI (Sau 0.1 giây)
    # Xe tiến gần lại camera (y2 tăng lên 320)
    engine.last_process_time = time.perf_counter() - 0.1
    # Cập nhật thời gian đã trôi qua cho đối tượng trong bộ nhớ theo dõi
    prev_dist, _ = engine.history_distance[1]
    engine.history_distance[1] = (prev_dist, time.perf_counter() - 0.1)
    
    track1.bbox = np.array([210, 210, 390, 320])
    
    results_f2 = engine.analyze([track1], left_fit=None, right_fit=None, offset=0.0, frame_shape=frame_shape)
    
    target = results_f2["target_vehicle"]
    assert target is not None, "LỖI: Hệ thống phải nhận diện được đây là Xe Đi Đầu (Lead Vehicle)!"
    
    # y_bottom mới = 320
    # dist_height = (1.5 * 580) / 110 = 7.909m
    # dist_horizon = 303.75 / (320 - 198) = 2.4898m
    # dist_long = 0.6 * 7.909 + 0.4 * 2.4898 = 5.7414m
    # dist_3d = ~5.74m
    print(f"Khoảng cách Frame 2: {target['distance']}m")
    assert 5.6 < target['distance'] < 5.8, f"LỖI: Khoảng cách mới tính sai! Nhận được {target['distance']}m"
    
    # Vận tốc tương đối (raw_speed) = (2.9779 - 2.4897) / 0.1 = ~4.88 m/s
    print(f"TTC tính toán được: {target['ttc']} giây")
    assert target["ttc"] < 99.0, "LỖI: TTC phải được tính toán hợp lệ (nhỏ hơn 99.0s) khi xe đang tiến lại gần."
    
    print("\n[SUCCESS] Tất cả các bài test logic ADAS (Khoảng cách, TTC, Tìm xe cùng làn) đều VƯỢT QUA (PASSED)!")

if __name__ == "__main__":
    test_distance_and_ttc()
