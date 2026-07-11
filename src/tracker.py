import numpy as np
from scipy.optimize import linear_sum_assignment

def calculate_iou(boxA, boxB):
    """
    Tính chỉ số IoU (Intersection over Union) giữa hai bounding box.
    Hộp có dạng [x1, y1, x2, y2]
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    unionArea = boxAArea + boxBArea - interArea
    if unionArea == 0:
        return 0.0
    return interArea / float(unionArea)

class Track:
    def __init__(self, bbox, class_id, score, track_id):
        self.track_id = track_id
        self.bbox = np.array(bbox, dtype=float)  # [x1, y1, x2, y2]
        self.class_id = class_id
        self.score = score
        self.age = 1
        self.time_since_update = 0
        self.history = [self.bbox.copy()]
        # Bộ lọc làm mịn cho bounding box (moving average)
        self.alpha = 0.7 

    def predict(self):
        """
        Dự đoán vị trí tiếp theo (đơn giản hóa bằng cách tăng thời gian không cập nhật).
        """
        self.time_since_update += 1
        self.age += 1
        return self.bbox

    def update(self, bbox, class_id, score):
        """
        Cập nhật thông tin track với bounding box mới phát hiện.
        """
        # Áp dụng bộ lọc làm mịn
        self.bbox = self.alpha * np.array(bbox, dtype=float) + (1 - self.alpha) * self.bbox
        self.class_id = class_id
        self.score = score
        self.time_since_update = 0
        self.history.append(self.bbox.copy())
        if len(self.history) > 10:
            self.history.pop(0)

from src.config_loader import config_inst

class ByteTracker:
    """
    Bộ theo dõi đối tượng đa mục tiêu (Multi-Object Tracker) lấy cảm hứng từ ByteTrack.
    Sử dụng IoU Association và thuật toán Hungarian để giải quyết bài toán gán ID.
    """
    def __init__(self, max_age=30, min_hits=3, iou_threshold=None):
        self.max_age = max_age
        self.min_hits = min_hits
        if iou_threshold is None:
            self.iou_threshold = config_inst.get("model.iou_threshold", 0.45)
        else:
            self.iou_threshold = iou_threshold
        self.tracks = []
        self.next_id = 1

    def update(self, detections):
        """
        Cập nhật bộ theo dõi.
        Đầu vào detections: List của dict hoặc tuple [x1, y1, x2, y2, score, class_id]
        Đầu ra: List của các Track đang hoạt động có ID ổn định.
        """
        # Bước 1: Dự đoán vị trí tiếp theo của các tracks hiện tại
        for track in self.tracks:
            track.predict()

        # Phân loại detections đầu vào
        # detections dạng: [[x1, y1, x2, y2, score, class_id], ...]
        if len(detections) == 0:
            # Không có phát hiện mới, tăng time_since_update và lọc các track quá cũ
            self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]
            return [t for t in self.tracks if t.time_since_update == 0]

        # Bước 2: Liên kết (Association) sử dụng IoU và Hungarian Algorithm
        num_tracks = len(self.tracks)
        num_dets = len(detections)

        cost_matrix = np.zeros((num_tracks, num_dets), dtype=np.float32)
        for t, track in enumerate(self.tracks):
            for d, det in enumerate(detections):
                # Chi phí bằng 1 - IoU
                cost_matrix[t, d] = 1.0 - calculate_iou(track.bbox, det[:4])

        # Sử dụng thuật toán Hungarian giải bài toán gán việc tối ưu
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        matched_indices = []
        unmatched_tracks = set(range(num_tracks))
        unmatched_detections = set(range(num_dets))

        for r, c in zip(row_ind, col_ind):
            # Kiểm tra nếu IoU lớn hơn ngưỡng tối thiểu (tức là Cost nhỏ hơn 1 - iou_threshold)
            if cost_matrix[r, c] < (1.0 - self.iou_threshold):
                matched_indices.append((r, c))
                unmatched_tracks.discard(r)
                unmatched_detections.discard(c)

        # Bước 3: Cập nhật các tracks đã liên kết thành công
        for r, c in matched_indices:
            det = detections[c]
            self.tracks[r].update(det[:4], int(det[5]), det[4])

        # Bước 4: Tạo mới tracks từ các detections chưa được liên kết
        for d in unmatched_detections:
            det = detections[d]
            # Chỉ tạo track khi độ tự tin tương đối tốt (>0.3)
            if det[4] > 0.3:
                new_track = Track(det[:4], int(det[5]), det[4], self.next_id)
                self.tracks.append(new_track)
                self.next_id += 1

        # Bước 5: Loại bỏ các tracks không cập nhật trong thời gian dài
        self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]

        # Trả về các tracks đang hoạt động tốt (đã được cập nhật ở frame hiện tại)
        return [t for t in self.tracks if t.time_since_update == 0]
