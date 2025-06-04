"""
Agent1 Presentation - WindowConfig
ウィンドウ設定・状態管理

機能:
- ウィンドウ位置・サイズ保存
- レイアウト設定管理
- テーマ・外観設定
"""

import json
import os
from typing import Dict, Any, Optional
from PyQt6.QtCore import QSettings, QSize, QPoint
from PyQt6.QtWidgets import QMainWindow


class WindowConfig:
    """
    ウィンドウ設定・状態管理
    
    機能:
    - ウィンドウ位置・サイズ保存
    - レイアウト設定管理
    - テーマ・外観設定
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初期化
        
        Args:
            config_file: 設定ファイルパス（省略時は自動）
        """
        self.config_file = config_file or self._get_default_config_path()
        self.settings = QSettings('FastAnnotation', 'Agent1Presentation')
        self.config_data = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルパス取得"""
        config_dir = os.path.expanduser("~/.fast_annotation")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "presentation_config.json")
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Config load error: {e}")
            
        # デフォルト設定返却
        return self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定取得"""
        return {
            'window': {
                'width': 1920,
                'height': 1080,
                'x': 100,
                'y': 100,
                'maximized': False,
            },
            'layout': {
                'canvas_ratio': 0.7,
                'panel_ratio': 0.3,
                'splitter_sizes': [1344, 576],
            },
            'appearance': {
                'theme': 'default',
                'font_size': 10,
                'show_status_bar': True,
                'show_menu_bar': True,
            },
            'performance': {
                'enable_opengl': True,
                'max_fps': 60,
                'cache_frames': 100,
            },
            'shortcuts': {
                'frame_prev': 'A',
                'frame_next': 'D',
                'bb_create': 'W',
                'bb_delete': 'S',
                'undo': 'Ctrl+Z',
            }
        }
        
    def save_config(self):
        """設定ファイル保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")
            
    def save_window_state(self, window: QMainWindow):
        """ウィンドウ状態保存"""
        try:
            # ウィンドウ状態取得
            geometry = window.geometry()
            
            # 設定更新
            self.config_data['window'].update({
                'width': geometry.width(),
                'height': geometry.height(),
                'x': geometry.x(),
                'y': geometry.y(),
                'maximized': window.isMaximized(),
            })
            
            # スプリッター状態保存
            if hasattr(window, 'main_splitter'):
                sizes = window.main_splitter.sizes()
                self.config_data['layout']['splitter_sizes'] = sizes
                
            # QSettings保存
            self.settings.setValue("geometry", window.saveGeometry())
            self.settings.setValue("windowState", window.saveState())
            
            # ファイル保存
            self.save_config()
            
        except Exception as e:
            print(f"Window state save error: {e}")
            
    def restore_window_state(self, window: QMainWindow):
        """ウィンドウ状態復元"""
        try:
            # QSettingsから復元
            geometry = self.settings.value("geometry")
            if geometry:
                window.restoreGeometry(geometry)
                
            window_state = self.settings.value("windowState")
            if window_state:
                window.restoreState(window_state)
                
            # 設定ファイルから復元
            window_config = self.config_data.get('window', {})
            
            if not geometry:  # QSettingsにない場合
                window.resize(
                    window_config.get('width', 1920),
                    window_config.get('height', 1080)
                )
                window.move(
                    window_config.get('x', 100),
                    window_config.get('y', 100)
                )
                
            if window_config.get('maximized', False):
                window.showMaximized()
                
            # スプリッター状態復元
            if hasattr(window, 'main_splitter'):
                sizes = self.config_data['layout'].get('splitter_sizes', [1344, 576])
                window.main_splitter.setSizes(sizes)
                
        except Exception as e:
            print(f"Window state restore error: {e}")
            
    def get_window_config(self) -> Dict[str, Any]:
        """ウィンドウ設定取得"""
        return self.config_data.get('window', {})
        
    def get_layout_config(self) -> Dict[str, Any]:
        """レイアウト設定取得"""
        return self.config_data.get('layout', {})
        
    def get_appearance_config(self) -> Dict[str, Any]:
        """外観設定取得"""
        return self.config_data.get('appearance', {})
        
    def get_performance_config(self) -> Dict[str, Any]:
        """性能設定取得"""
        return self.config_data.get('performance', {})
        
    def get_shortcuts_config(self) -> Dict[str, str]:
        """ショートカット設定取得"""
        return self.config_data.get('shortcuts', {})
        
    def set_config_value(self, section: str, key: str, value: Any):
        """設定値更新"""
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
        
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """設定値取得"""
        return self.config_data.get(section, {}).get(key, default)
        
    def reset_to_default(self):
        """デフォルト設定にリセット"""
        self.config_data = self._get_default_config()
        self.save_config()
        
    def export_config(self, file_path: str) -> bool:
        """設定エクスポート"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Config export error: {e}")
            return False
            
    def import_config(self, file_path: str) -> bool:
        """設定インポート"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # 妥当性確認後更新
            if self._validate_config(imported_config):
                self.config_data = imported_config
                self.save_config()
                return True
            else:
                print("Invalid config format")
                return False
                
        except Exception as e:
            print(f"Config import error: {e}")
            return False
            
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """設定妥当性確認"""
        try:
            required_sections = ['window', 'layout', 'appearance', 'performance', 'shortcuts']
            
            # セクション存在確認
            for section in required_sections:
                if section not in config:
                    return False
                    
            # 必須フィールド確認
            window_fields = ['width', 'height', 'x', 'y']
            for field in window_fields:
                if field not in config['window']:
                    return False
                if not isinstance(config['window'][field], (int, float)):
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def get_config_info(self) -> Dict[str, Any]:
        """設定情報取得"""
        return {
            'config_file': self.config_file,
            'config_exists': os.path.exists(self.config_file),
            'sections': list(self.config_data.keys()),
            'total_settings': sum(len(v) if isinstance(v, dict) else 1 
                                 for v in self.config_data.values()),
        }


if __name__ == "__main__":
    # テスト実行
    config = WindowConfig()
    
    print("Window Config Test")
    print("==================")
    
    # 設定情報表示
    info = config.get_config_info()
    print(f"Config file: {info['config_file']}")
    print(f"Config exists: {info['config_exists']}")
    print(f"Sections: {info['sections']}")
    print(f"Total settings: {info['total_settings']}")
    
    # 各セクション設定表示
    sections = ['window', 'layout', 'appearance', 'performance', 'shortcuts']
    for section in sections:
        print(f"\n{section.title()} Config:")
        section_config = config.config_data.get(section, {})
        for key, value in section_config.items():
            print(f"  {key}: {value}")
            
    # 設定値変更テスト
    print("\nTesting config value changes...")
    config.set_config_value('performance', 'max_fps', 120)
    print(f"max_fps changed to: {config.get_config_value('performance', 'max_fps')}")
    
    # 保存テスト
    print("\nTesting config save...")
    config.save_config()
    print("Config saved successfully")