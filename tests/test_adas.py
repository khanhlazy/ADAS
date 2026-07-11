import unittest
import numpy as np
import sys
import os

# Thêm thư mục gốc vào đường dẫn import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config_loader import config_inst
from src.adas_engine import ADASEngine
from src.tracker import ByteTracker, Track

class TestADASSystem(unittest.TestCase):
    
    def test_01_config_loader(self):
        """Kiểm tra Config Loader tải đúng tham số từ config.yaml"""
        # Kiểm tra các giá trị mặc định hoặc đã cấu hình
        self.assertIsNotNone(config_inst.get("server.port"))
        self.assertEqual(config_inst.get("model.conf_threshold"), 0.25)
        self.assertEqual(config_inst.get("ldw.threshold"), 0.55)

    def test_02_distance_estimation(self):
        """Kiểm tra thuật toán ước lượng khoảng cách hình học"""
        engine = ADASEngine()
        # Giả lập bounding box ở dưới chân trời (ví dụ: đáy ở y=600px trên ảnh cao 720px)
        # Khoảng cách phải là một số dương hợp lệ
        bbox = [500, 400, 600, 600]
        dist = engine.estimate_distance(bbox, 0, 720)
        self.assertTrue(2.0 <= dist <= 80.0)

    def test_03_is_in_lane_adaptive_corridor(self):
        """Kiểm tra hành lang va chạm trực diện thích ứng (Saigon standard)"""
        engine = ADASEngine()
        # Giả lập vạch làn thẳng đứng (Đa thức bậc 3)
        left_fit = [0, 0, 0, 300]   # Vạch trái ở x = 300
        right_fit = [0, 0, 0, 700]  # Vạch phải ở x = 700
        # lane_center = 500, lane_width = 400
        
        # 1. Xe máy chạy chính giữa làn (x_center = 500) -> Nằm trong hành lang
        bbox_motor_center = [490, 500, 510, 600]
        self.assertTrue(engine.is_in_lane(bbox_motor_center, 1, left_fit, right_fit, 720))
        
        # 2. Xe máy chạy sát biên trái (x_center = 330) -> Khoảng cách đến tâm = 170 > 400 * 0.26 (104px)
        # Nằm ngoài hành lang va chạm trực diện (được bỏ qua để tránh báo động giả)
        bbox_motor_side = [320, 500, 340, 600]
        self.assertFalse(engine.is_in_lane(bbox_motor_side, 1, left_fit, right_fit, 720))
        
        # 3. Ô tô chạy lệch nhẹ sang bên trái (x_center = 400) -> Khoảng cách đến tâm = 100 < 400 * 0.38 (152px)
        # Ô tô có kích thước rộng nên vẫn nằm trong hành lang nguy hiểm của xe chủ
        bbox_car_side = [350, 500, 450, 600]
        self.assertTrue(engine.is_in_lane(bbox_car_side, 0, left_fit, right_fit, 720))

    def test_04_tracker_association(self):
        """Kiểm tra bộ theo dõi ByteTracker gán ID ổn định"""
        tracker = ByteTracker(max_age=5, min_hits=1)
        
        # Frame 1: Phát hiện 1 xe ở vị trí [100, 100, 200, 200]
        detections_f1 = [[100, 100, 200, 200, 0.9, 0]]
        tracks_f1 = tracker.update(detections_f1)
        self.assertEqual(len(tracks_f1), 1)
        track_id = tracks_f1[0].track_id
        
        # Frame 2: Xe dịch chuyển nhẹ sang vị trí [105, 102, 205, 202]
        detections_f2 = [[105, 102, 205, 202, 0.88, 0]]
        tracks_f2 = tracker.update(detections_f2)
        self.assertEqual(len(tracks_f2), 1)
        # ID phải được giữ nguyên ổn định
        self.assertEqual(tracks_f2[0].track_id, track_id)

if __name__ == "__main__":
    unittest.main()
