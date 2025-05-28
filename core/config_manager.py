import json
import os
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PerformanceConfig:
    cache_size_gb: int = 20
    preload_frames: int = 100
    copy_frames_default: int = 50
    auto_save_interval: int = 30
    max_memory_usage_gb: int = 64

@dataclass
class UIConfig:
    theme: str = "white_black_modern"
    font_size: int = 10
    frame_display_size: List[int] = None
    sidebar_width: int = 250

    def __post_init__(self):
        if self.frame_display_size is None:
            self.frame_display_size = [800, 600]

class ConfigManager:
    def __init__(self, config_path: str = "config/app_config.json"):
        self.config_path = Path(config_path)
        self.default_config = {
            "individual_ids": list(range(16)),
            "action_ids": ["sit", "stand", "milk", "water", "food"],
            "colors": {
                str(i): self._generate_hsv_color(i) for i in range(16)
            },
            "ui": UIConfig().__dict__,
            "performance": PerformanceConfig().__dict__,
            "video_processing": {
                "target_fps": 5,
                "source_fps": 30,
                "output_format": "jpg",
                "output_quality": 95
            }
        }
        self.config = self.load_config()

    def _generate_hsv_color(self, index: int) -> str:
        hue = (index * 22.5) % 360
        return f"hsl({hue}, 100%, 50%)"

    def load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self.default_config.copy()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return self._validate_config(config)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self) -> bool:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path = self.config_path.with_suffix('.json.bak')
            
            if self.config_path.exists():
                shutil.copy(self.config_path, backup_path)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.default_config.copy()
        
        for key, value in config.items():
            if key not in validated:
                continue
                
            if key == "individual_ids":
                validated[key] = [i for i in value if isinstance(i, int) and 0 <= i <= 15]
            elif key == "action_ids":
                validated[key] = [str(action) for action in value if isinstance(action, str)]
            elif key == "colors":
                validated[key] = {str(k): str(v) for k, v in value.items() if k.isdigit()}
            elif key in ["ui", "performance", "video_processing"]:
                validated[key].update({k: v for k, v in value.items() if k in validated[key]})
        
        return validated

    def get_setting(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
        
        return value

    def set_setting(self, key: str, value: Any) -> bool:
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                return False
            config = config[k]
            
        config[keys[-1]] = value
        return self.save_config()

    def reset_to_default(self, key: Optional[str] = None) -> bool:
        if key is None:
            self.config = self.default_config.copy()
        else:
            keys = key.split('.')
            value = self.default_config
            for k in keys:
                if k not in value:
                    return False
                value = value[k]
            
            current = self.config
            for k in keys[:-1]:
                current = current[k]
            current[keys[-1]] = value
            
        return self.save_config()

    def add_action_id(self, action: str) -> bool:
        if action not in self.config["action_ids"]:
            self.config["action_ids"].append(action)
            return self.save_config()
        return False

    def remove_action_id(self, action: str) -> bool:
        if action in self.config["action_ids"]:
            self.config["action_ids"].remove(action)
            return self.save_config()
        return False