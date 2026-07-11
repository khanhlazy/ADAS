import os
import sys
import yaml

# Cấu hình encoding UTF-8 để tránh lỗi UnicodeEncodeError trên terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class Config:
    """
    Singleton Class quản lý cấu hình hệ thống ADAS từ file config.yaml
    """
    _instance = None
    _config_data = {}

    def __new__(cls, config_path="config/config.yaml"):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config(config_path)
        return cls._instance

    def load_config(self, config_path):
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                print(f"[INFO] Đã tải cấu hình thành công từ '{config_path}'")
            except Exception as e:
                print(f"[CẢNH BÁO] Lỗi đọc cấu hình: {e}. Sử dụng cấu hình mặc định.")
                self._config_data = {}
        else:
            print(f"[CẢNH BÁO] Không tìm thấy file cấu hình tại '{config_path}'. Sử dụng cấu hình mặc định.")
            self._config_data = {}

    def get(self, key_path, default=None):
        """
        Lấy giá trị cấu hình dựa trên đường dẫn dạng 'server.host'
        """
        keys = key_path.split('.')
        val = self._config_data
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val if val is not None else default

# Singleton Instance tiện dụng cho toàn dự án
config_inst = Config()
