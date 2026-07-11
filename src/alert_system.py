import os
import time
import threading
import queue
from src.config_loader import config_inst

# Tắt thông báo chào mừng từ pygame khi import
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

class AlertSystem:
    """
    Hệ thống phát cảnh báo giọng nói bằng tiếng Việt (Audio Alert System):
    - Tự động sinh file âm thanh bằng gTTS tại lần chạy đầu tiên.
    - Sử dụng hàng đợi (Queue) và 1 luồng công việc duy nhất (Single Worker Thread) để đảm bảo an toàn đa luồng.
    - Hỗ trợ ngắt âm thanh hiện tại ngay lập tức khi phát hiện cảnh báo nguy hiểm khẩn cấp (FCW DANGER).
    - Quản lý thời gian chờ (Cooldown) giữa các cảnh báo để tránh lặp âm gây khó chịu.
    """
    def __init__(self, audio_dir="static/audio", cooldown_seconds=12.0, global_cooldown_seconds=6.0):
        self.audio_dir = audio_dir
        self.cooldown_seconds = cooldown_seconds
        self.global_cooldown_seconds = global_cooldown_seconds
        
        # Đọc cấu hình âm lượng và kích hoạt
        self.voice_enabled = config_inst.get("alerts.voice_enabled", True)
        self.volume = config_inst.get("alerts.volume", 1.0)
        
        # Tạo thư mục chứa âm thanh nếu chưa tồn tại
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Định nghĩa các loại cảnh báo và văn bản tiếng Việt tương ứng
        self.alerts_config = {
            "startup": ("he_thong_khoi_dong.mp3", "Hệ thống hỗ trợ lái xe ADAS đã khởi động thành công."),
            "fcw_danger": ("khoang_cach_nguy_hiem.mp3", "Cảnh báo! Khoảng cách nguy hiểm. Chú ý xe phía trước!"),
            "fcw_warning": ("chu_y_giu_khoang_cach.mp3", "Chú ý giữ khoảng cách an toàn."),
            "ldw_left": ("lech_lan_trai.mp3", "Cảnh báo! Lệch làn bên trái."),
            "ldw_right": ("lech_lan_phai.mp3", "Cảnh báo! Lệch làn bên phải.")
        }
        
        # Sinh các file âm thanh tiếng Việt nếu chưa có
        self._generate_alert_files()
        
        # Khởi tạo mixer của pygame để phát âm thanh
        try:
            pygame.mixer.init()
            self.sound_enabled = self.voice_enabled
            if self.sound_enabled:
                # Thiết lập âm lượng (giá trị từ 0.0 đến 1.0)
                pygame.mixer.music.set_volume(self.volume)
            print("[INFO] Audio mixer initialized successfully.")
        except Exception as e:
            print(f"[WARNING] Could not initialize Pygame mixer. Audio disabled. Error: {e}")
            self.sound_enabled = False
            
        # Hàng đợi âm thanh và worker thread để đảm bảo an toàn đa luồng
        self.audio_queue = queue.Queue()
        self.last_played = {}
        self.last_global_play_time = 0.0
        
        if self.sound_enabled:
            self.worker_thread = threading.Thread(target=self._audio_worker, daemon=True)
            self.worker_thread.start()
            
            # Phát âm thanh chào mừng khởi động
            self.trigger_alert("startup")

    def _generate_alert_files(self):
        """
        Sinh các file âm thanh cảnh báo tiếng Việt bằng gTTS nếu chưa tồn tại.
        """
        for key, (filename, text) in self.alerts_config.items():
            filepath = os.path.join(self.audio_dir, filename)
            if not os.path.exists(filepath):
                print(f"[INFO] Generating audio alert file: {filename}...")
                try:
                    from gtts import gTTS
                     # Nén giọng đọc để phát nhanh, ngắn gọn hơn
                    tts = gTTS(text=text, lang='vi')
                    tts.save(filepath)
                    print(f"[SUCCESS] Saved {filepath}")
                except Exception as e:
                    print(f"[ERROR] Could not connect to Google TTS to generate {filename}. Error: {e}")
                    print("[INFO] Fallback: System will continue but might lack voice alert until connected to internet.")

    def _audio_worker(self):
        """
        Luồng công việc duy nhất chạy ngầm để phát âm thanh tuần tự từ hàng đợi.
        Đảm bảo không bao giờ gọi hàm pygame.mixer từ nhiều thread song song.
        """
        while True:
            try:
                filepath = self.audio_queue.get()
                if filepath is None:
                    break
                
                if not os.path.exists(filepath):
                    try:
                        self.audio_queue.task_done()
                    except ValueError:
                        pass
                    continue
                
                try:
                    # Nạp và phát âm thanh
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.play()
                    
                    # Chờ phát xong hoặc hàng đợi bị xóa bởi cảnh báo khẩn cấp mới
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                except Exception as e:
                    print(f"[WARNING] Error in audio playback: {e}")
                
                try:
                    self.audio_queue.task_done()
                except ValueError:
                    pass
            except Exception as e:
                print(f"[ERROR] Audio worker error: {e}")
                time.sleep(0.5)

    def trigger_alert(self, alert_type):
        """
        Kích hoạt phát âm thanh cảnh báo an toàn.
        Hỗ trợ mức ưu tiên khẩn cấp cho fcw_danger.
        """
        if not self.sound_enabled or alert_type not in self.alerts_config:
            return
            
        current_time = time.time()
        
        # Chỉ kiểm tra Cooldown cho các loại cảnh báo thường (bỏ qua startup và fcw_danger khẩn cấp)
        if alert_type not in ["startup", "fcw_danger"]:
            # 1. Kiểm tra Cooldown toàn cục giữa mọi loại cảnh báo thường (tránh các câu phát đè/gần nhau)
            if current_time - self.last_global_play_time < self.global_cooldown_seconds:
                return
                
            # 2. Kiểm tra Cooldown của riêng loại cảnh báo này
            last_time = self.last_played.get(alert_type, 0.0)
            if current_time - last_time < self.cooldown_seconds:
                return
                
        # Cập nhật thời điểm phát gần nhất
        self.last_played[alert_type] = current_time
        if alert_type != "startup":
            self.last_global_play_time = current_time
        
        filename, _ = self.alerts_config[alert_type]
        filepath = os.path.join(self.audio_dir, filename)
        
        # Nếu là cảnh báo khẩn cấp FCW DANGER, ta ưu tiên hàng đầu:
        # Ngắt âm thanh cảnh báo nhẹ đang phát và dọn hàng đợi để phát Danger ngay
        if alert_type == "fcw_danger":
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    try:
                        self.audio_queue.task_done()
                    except ValueError:
                        pass
                except queue.Empty:
                    break
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
                
        self.audio_queue.put(filepath)

    def clear_queue_and_stop(self):
        """
        Dọn dẹp sạch hàng đợi và lập tức dừng phát âm thanh hiện tại.
        Được gọi khi người dùng tạm dừng luồng chạy từ Web UI.
        """
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                try:
                    self.audio_queue.task_done()
                except ValueError:
                    pass
            except queue.Empty:
                break
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
