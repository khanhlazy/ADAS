import numpy as np
from typing import Tuple, Optional

class LaneDetector:
    """
    Dummy LaneDetector. Lane detection is disabled/removed from active pipeline.
    """
    def __init__(self):
        self.device = "cpu"
        self.model = None
        self.horizon_ratio = 0.55
        self.frame_counter = 0
        print("[INFO] Lane detection is disabled per user request.")

    def detect_lanes(self, frame: np.ndarray, draw_overlay: bool = True) -> Tuple[np.ndarray, float, Optional[np.ndarray], Optional[np.ndarray], float]:
        self.frame_counter += 1
        return frame.copy(), 0.0, None, None, 0.0
