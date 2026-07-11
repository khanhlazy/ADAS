import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

class ADASEngine:
    """
    Hệ thống phân tích hỗ trợ lái xe nâng cao (ADAS Engine).
    Xác định Lead Vehicle, khoảng cách, TTC, FCW và tích hợp cảnh báo chệch làn LDW.
    """
    def __init__(self, camera_height: float = 1.35, horizon_ratio: float = 0.55):
        self.camera_height = camera_height
        self.horizon_ratio = horizon_ratio
        
        # Tiêu cự ảo chuẩn hóa
        self.f_factor = 450.0
        
        # Ngưỡng TTC an toàn (giây)
        self.ttc_danger = 1.3
        self.ttc_warning = 2.3
        
        # Khoảng cách cảnh báo cứng (mét)
        self.safe_distance_warning = 18.0
        self.safe_distance_danger = 8.0
        
        # Bộ nhớ theo dõi
        self.history_distance: Dict[int, Tuple[float, float]] = {}
        self.history_speed: Dict[int, float] = {}
        self.last_process_time = time.perf_counter()

    def estimate_distance(self, bbox: np.ndarray, class_id: int, frame_height: int) -> float:
        """
        Ước lượng khoảng cách từ Camera tới xe phía trước bằng phương pháp kết hợp:
        1. Sử dụng chiều cao bounding box (ổn định với góc nghiêng camera và độ dốc của đường).
        2. Sử dụng góc nhìn quang học (camera horizon) làm tham chiếu điều chỉnh khi vật thể cách xa đường chân trời.
        3. Tính toán khoảng cách 3D thực tế (Euclidean distance) từ camera tới xe.
        """
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        h_box = max(1.0, y2 - y1)
        
        # Tiêu cự camera giả định dựa trên chiều cao khung hình
        focal_length = 580.0 * (frame_height / 360.0)
        
        # Chiều cao vật lý trung bình của từng nhóm đối tượng (mét)
        real_heights = {
            0: 1.5,   # car
            1: 1.6,   # motorcycle
            2: 3.2,   # bus
            3: 2.8,   # truck
            4: 1.7,   # person
        }
        real_h = real_heights.get(class_id, 1.5)
        
        # 1. Khoảng cách dọc (longitudinal distance) theo chiều cao hộp nhận diện
        dist_height = (real_h * focal_length) / h_box
        
        # 2. Khoảng cách dọc theo góc nghiêng chân vật thể so với đường chân trời
        y_horizon = frame_height * self.horizon_ratio
        # Chỉ sử dụng công thức góc nghiêng nếu vật thể đủ gần (chân xe nằm dưới đường chân trời ít nhất 12 pixel)
        # để tránh sai số nổ khoảng cách khi y2 tiệm cận y_horizon
        if y2 > y_horizon + 12.0:
            scaled_f = self.f_factor * (frame_height / 720.0)
            dist_horizon = (self.camera_height * scaled_f) / (y2 - y_horizon)
            # Kết hợp hai phương pháp: 60% từ kích thước hộp và 40% từ vị trí hình học chân đối tượng
            dist_long = 0.6 * dist_height + 0.4 * dist_horizon
        else:
            dist_long = dist_height
            
        # 3. Tính khoảng cách ngang (lateral distance) và khoảng cách 3D Euclidean từ camera
        w_frame = frame_height * (16.0 / 9.0)
        dx_pixels = cx - (w_frame / 2.0)
        dist_lat = dx_pixels * (dist_long / focal_length)
        
        dist_3d = np.sqrt(dist_long ** 2 + dist_lat ** 2)
            
        return float(np.clip(dist_3d, 2.0, 80.0))

    def is_in_lane(
        self,
        bbox: np.ndarray,
        class_id: int,
        left_fit: Optional[np.ndarray],
        right_fit: Optional[np.ndarray],
        frame_height: int
    ) -> bool:
        """
        Kiểm tra vật thể có nằm trong hành lang an toàn (Driving Corridor) hay không.
        """
        x1, _, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        
        corridor_ratio = 0.26 if class_id == 1 else 0.38
        frame_width = frame_height * (16.0 / 9.0)
        
        # 1. Hành lang trung tâm vật lý (Phòng ngừa lỗi khi mất vạch kẻ đường)
        center_width = frame_width * 0.175
        if (frame_width * 0.5 - center_width) <= cx <= (frame_width * 0.5 + center_width):
            return True
            
        if left_fit is None or right_fit is None or len(left_fit) != 4 or len(right_fit) != 4:
            # Fallback khi mất vạch làn
            fallback_width = frame_width * corridor_ratio * 0.6
            return (frame_width * 0.5 - fallback_width) <= cx <= (frame_width * 0.5 + fallback_width)

        # 2. Kiểm tra hình học đa thức làn đường tại y2 của vật thể
        left_x = left_fit[0] * (y2 ** 3) + left_fit[1] * (y2 ** 2) + left_fit[2] * y2 + left_fit[3]
        right_x = right_fit[0] * (y2 ** 3) + right_fit[1] * (y2 ** 2) + right_fit[2] * y2 + right_fit[3]
        
        lane_w = right_x - left_x
        lane_c = (left_x + right_x) / 2.0
        
        return abs(cx - lane_c) <= (lane_w * corridor_ratio)

    def analyze(
        self,
        tracked_objects: List[Any],
        left_fit: Optional[np.ndarray],
        right_fit: Optional[np.ndarray],
        offset: float,
        frame_shape: Tuple[int, int]
    ) -> Dict[str, Any]:
        """
        Thực hiện phân tích tổng hợp: Khoảng cách, TTC, FCW và tích hợp cảnh báo chệch làn.
        """
        h, w = frame_shape[:2]
        current_time = time.perf_counter()
        dt = current_time - self.last_process_time
        if dt <= 0:
            dt = 0.033
        self.last_process_time = current_time

        target_vehicle = None
        min_distance = float('inf')
        processed_objects = []

        for obj in tracked_objects:
            dist = self.estimate_distance(obj.bbox, obj.class_id, h)
            obj.distance = dist
            
            obj.ttc = float('inf')
            rel_speed = 0.0
            
            # Tính toán vận tốc tương đối và TTC
            if obj.track_id in self.history_distance:
                prev_dist, prev_time = self.history_distance[obj.track_id]
                time_diff = current_time - prev_time
                if time_diff > 0.01:
                    raw_speed = (prev_dist - dist) / time_diff
                    prev_speed = self.history_speed.get(obj.track_id, raw_speed)
                    rel_speed = 0.25 * raw_speed + 0.75 * prev_speed
                    self.history_speed[obj.track_id] = rel_speed
                    
                    if rel_speed > 0.1:
                        obj.ttc = dist / rel_speed
            else:
                self.history_speed[obj.track_id] = 0.0
                
            self.history_distance[obj.track_id] = (dist, current_time)
            
            is_lead = self.is_in_lane(obj.bbox, obj.class_id, left_fit, right_fit, h)
            is_vehicle = obj.class_id in [0, 1, 2, 3] # Car, Motor, Bus, Truck
            
            if is_vehicle and is_lead:
                if dist < min_distance:
                    min_distance = dist
                    target_vehicle = {
                        "id": obj.track_id,
                        "distance": round(dist, 1),
                        "ttc": round(obj.ttc, 1) if obj.ttc != float('inf') else 99.0,
                        "bbox": obj.bbox.tolist(),
                        "class_id": obj.class_id,
                        "rel_speed": rel_speed
                    }
                    
            processed_objects.append({
                "id": obj.track_id,
                "bbox": obj.bbox.tolist(),
                "class_id": obj.class_id,
                "distance": round(dist, 1),
                "ttc": round(obj.ttc, 1) if obj.ttc != float('inf') else 99.0,
                "in_lane": is_lead
            })

        # Cảnh báo va chạm phía trước (FCW)
        fcw_status = "SAFE"
        if target_vehicle is not None:
            dist = target_vehicle["distance"]
            ttc = target_vehicle["ttc"]
            class_id = target_vehicle["class_id"]
            rel_speed = target_vehicle.get("rel_speed", 0.0)
            
            # Điều chỉnh khoảng cách an toàn thích ứng theo loại phương tiện
            if class_id == 1: # Xe máy (nhỏ gọn, phanh nhanh hơn)
                danger_d = self.safe_distance_danger * 0.60
                warning_d = self.safe_distance_warning * 0.60
                danger_t = self.ttc_danger * 0.60
                warning_t = self.ttc_warning * 0.60
            else: # Ô tô, xe tải, xe buýt
                danger_d = self.safe_distance_danger
                warning_d = self.safe_distance_warning
                danger_t = self.ttc_danger
                warning_t = self.ttc_warning
                
            is_closing_fast = (rel_speed > 0.8)
            
            # Cảnh báo khoảng cách cứng hoặc cảnh báo TTC khi đối tượng ở trong vùng ảnh hưởng (gần hơn 1.5x khoảng cách an toàn)
            danger_trigger = (dist < danger_d) or (dist < self.safe_distance_warning * 1.5 and ttc < danger_t and is_closing_fast)
            warning_trigger = (dist < warning_d) or (dist < self.safe_distance_warning * 1.5 and ttc < warning_t and is_closing_fast)
            
            if danger_trigger:
                fcw_status = "DANGER"
            elif warning_trigger:
                fcw_status = "WARNING"

        # Cảnh báo lệch làn (LDW)
        ldw_status = "BÌNH THƯỜNG"

        # Tránh rò rỉ bộ nhớ lịch sử tracking
        active_ids = {obj.track_id for obj in tracked_objects}
        keys_to_delete = [k for k in self.history_distance.keys() if k not in active_ids]
        for k in keys_to_delete:
            self.history_distance.pop(k, None)
            self.history_speed.pop(k, None)

        return {
            "fcw_status": fcw_status,
            "ldw_status": ldw_status,
            "ldw_offset": round(offset, 2),
            "target_vehicle": target_vehicle,
            "all_objects": processed_objects
        }
