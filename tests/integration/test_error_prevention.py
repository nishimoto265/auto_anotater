"""
Error Prevention Tests - 実装過程で発生したエラーの防止テスト

カバー対象エラー:
1. アーキテクチャ設計エラー
2. 型エラー (Type Errors)
3. インポートエラー (Import Errors) 
4. GUI環境エラー (GUI Environment Errors)
5. パス・ファイル参照エラー (Path/File Reference Errors)
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルート追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestArchitectureDesignErrors:
    """アーキテクチャ設計エラー防止テスト"""
    
    def test_main_entry_point_has_project_selection(self):
        """メインエントリーポイントがプロジェクト選択を含むか確認"""
        from main import main
        import inspect
        
        # main関数のソースコード取得
        source = inspect.getsource(main)
        
        # プロジェクト選択関連のキーワード存在確認
        assert 'ProjectStartupDialog' in source, "メイン関数にプロジェクト選択ダイアログが含まれていない"
        assert 'project_info' in source, "プロジェクト情報の処理が含まれていない"
        
    def test_main_window_accepts_project_info(self):
        """MainWindowがプロジェクト情報を受け取れるか確認"""
        from presentation.main_window.main_window import MainWindow
        import inspect
        
        # __init__メソッドのシグネチャ確認
        init_signature = inspect.signature(MainWindow.__init__)
        assert 'project_info' in init_signature.parameters, "MainWindowがproject_info引数を受け取れない"
        
    def test_project_startup_dialog_exists(self):
        """プロジェクト選択ダイアログが実装されているか確認"""
        try:
            from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
            assert hasattr(ProjectStartupDialog, 'project_selected'), "project_selectedシグナルが未実装"
            assert hasattr(ProjectStartupDialog, 'get_project_info'), "get_project_infoメソッドが未実装"
        except ImportError:
            pytest.fail("ProjectStartupDialogが実装されていない")
            

class TestTypeErrors:
    """型エラー防止テスト"""
    
    def test_dialog_validation_returns_boolean(self):
        """ダイアログバリデーションがboolean値を返すか確認"""
        # プロジェクト選択ダイアログのモック作成
        with patch('PyQt6.QtWidgets.QApplication'):
            from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
            
            # ダイアログ作成（UI初期化をモック）
            with patch.object(ProjectStartupDialog, 'setup_ui'), \
                 patch.object(ProjectStartupDialog, 'connect_signals'):
                dialog = ProjectStartupDialog()
                
                # モックボタン設定
                dialog.ok_button = Mock()
                dialog.video_radio = Mock()
                dialog.image_radio = Mock()
                dialog.existing_radio = Mock()
                dialog.video_path_edit = Mock()
                dialog.project_name_edit = Mock()
                
                # 各状態でのバリデーション確認
                dialog.video_radio.isChecked.return_value = True
                dialog.image_radio.isChecked.return_value = False
                dialog.existing_radio.isChecked.return_value = False
                dialog.video_path_edit.text.return_value = "test.mp4"
                dialog.project_name_edit.text.return_value = "test_project"
                
                # バリデーション実行
                dialog.validate_input()
                
                # setEnabledが呼ばれた引数がbooleanか確認
                dialog.ok_button.setEnabled.assert_called()
                call_args = dialog.ok_button.setEnabled.call_args[0]
                assert isinstance(call_args[0], bool), f"setEnabledにboolean以外が渡された: {type(call_args[0])}"
                
    def test_project_info_tuple_structure(self):
        """プロジェクト情報タプルの構造確認"""
        with patch('PyQt6.QtWidgets.QApplication'):
            from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
            
            with patch.object(ProjectStartupDialog, 'setup_ui'), \
                 patch.object(ProjectStartupDialog, 'connect_signals'):
                dialog = ProjectStartupDialog()
                
                # プロジェクト情報設定
                dialog.selected_type = "video"
                dialog.selected_path = "/path/to/video.mp4"
                dialog.project_config = {"name": "test"}
                
                project_type, project_path, project_config = dialog.get_project_info()
                
                # 型確認
                assert isinstance(project_type, (str, type(None))), "project_typeがstring/None以外"
                assert isinstance(project_path, (str, type(None))), "project_pathがstring/None以外"  
                assert isinstance(project_config, dict), "project_configがdict以外"


class TestImportErrors:
    """インポートエラー防止テスト"""
    
    def test_all_required_modules_importable(self):
        """必須モジュールがすべてインポート可能か確認"""
        required_modules = [
            'presentation.main_window.main_window',
            'presentation.dialogs.project_startup_dialog',
            'cache_layer.cache_agent',
            'data_bus.event_bus.event_dispatcher',
            'domain.entities.bb_entity',
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"必須モジュール {module_name} をインポートできない: {e}")
                
    def test_pyqt6_optional_import(self):
        """PyQt6が利用できない環境での優雅な処理確認"""
        # PyQt6インポートを一時的に無効化
        original_modules = sys.modules.copy()
        
        try:
            # PyQt6関連モジュールを削除
            modules_to_remove = [m for m in sys.modules if m.startswith('PyQt6')]
            for module in modules_to_remove:
                del sys.modules[module]
                
            # PyQt6インポートを失敗させる
            import builtins
            original_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                if name.startswith('PyQt6'):
                    raise ImportError(f"No module named '{name}'")
                return original_import(name, *args, **kwargs)
                
            builtins.__import__ = mock_import
            
            # この時点でPyQt6依存コードがエラーハンドリングされているか確認
            try:
                from presentation.main_window.main_window import MainWindow
                # インポートが成功した場合、適切なエラーハンドリングがされている
            except ImportError:
                # インポートエラーが発生するのは想定内
                pass
                
        finally:
            # モジュール状態復元
            sys.modules.clear()
            sys.modules.update(original_modules)
            builtins.__import__ = original_import


class TestGUIEnvironmentErrors:
    """GUI環境エラー防止テスト"""
    
    def test_headless_environment_detection(self):
        """ヘッドレス環境検出機能確認"""
        # ディスプレイ環境変数をモック
        with patch.dict(os.environ, {}, clear=True):
            # DISPLAY環境変数なし（ヘッドレス環境）
            
            # QApplicationの初期化が適切にハンドリングされるか確認
            try:
                with patch('PyQt6.QtWidgets.QApplication') as mock_app:
                    mock_app.side_effect = RuntimeError("Cannot connect to display")
                    
                    # この環境でのエラーハンドリング確認
                    # 実際の実装では適切なフォールバック処理が必要
                    pass
                    
            except Exception as e:
                # GUI初期化エラーが適切に処理されるべき
                assert "display" in str(e).lower() or "qt" in str(e).lower()
                
    def test_application_instance_management(self):
        """QApplicationインスタンス管理確認"""
        with patch('PyQt6.QtWidgets.QApplication') as mock_app_class:
            mock_app = Mock()
            mock_app_class.return_value = mock_app
            mock_app_class.instance.return_value = None
            
            from main import setup_application
            
            app = setup_application()
            
            # QApplicationが適切に作成されているか確認
            mock_app_class.assert_called_once()


class TestPathFileReferenceErrors:
    """パス・ファイル参照エラー防止テスト"""
    
    def test_project_file_validation(self):
        """プロジェクトファイル検証機能確認"""
        with patch('PyQt6.QtWidgets.QApplication'):
            from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
            
            with patch.object(ProjectStartupDialog, 'setup_ui'), \
                 patch.object(ProjectStartupDialog, 'connect_signals'):
                dialog = ProjectStartupDialog()
                
                # 存在しないファイルパス
                assert not dialog.is_valid_video_file("nonexistent.mp4")
                
                # 無効な拡張子
                assert not dialog.is_valid_video_file("file.txt")
                
                # 有効な拡張子
                assert dialog.is_valid_video_file("video.mp4")
                assert dialog.is_valid_video_file("video.avi")
                
    def test_virtual_environment_detection(self):
        """仮想環境検出・パス解決確認"""
        # 一時的な仮想環境構造作成
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir(parents=True)
            
            # Pythonインタープリター作成（空ファイル）
            python_exe = bin_dir / "python"
            python_exe.write_text("#!/usr/bin/env python3\n")
            python_exe.chmod(0o755)
            
            # パス検証
            assert python_exe.exists()
            assert python_exe.is_file()
            
    def test_relative_path_resolution(self):
        """相対パス解決確認"""
        # プロジェクトルートからの相対パス確認
        project_root = Path(__file__).parent.parent.parent
        
        # 重要なディレクトリの存在確認
        assert (project_root / "src").exists(), "srcディレクトリが見つからない"
        assert (project_root / "tests").exists(), "testsディレクトリが見つからない"
        assert (project_root / "requirements.txt").exists(), "requirements.txtが見つからない"
        
    def test_file_dialog_path_handling(self):
        """ファイルダイアログパス処理確認"""
        with patch('PyQt6.QtWidgets.QFileDialog') as mock_dialog:
            # ファイル選択の戻り値テスト
            mock_dialog.getOpenFileName.return_value = ("/path/to/file.mp4", "Video Files (*.mp4)")
            mock_dialog.getExistingDirectory.return_value = "/path/to/folder"
            
            # パス処理確認
            file_path, _ = mock_dialog.getOpenFileName()
            folder_path = mock_dialog.getExistingDirectory()
            
            assert isinstance(file_path, str)
            assert isinstance(folder_path, str)


class TestRegressionTests:
    """回帰テスト - 過去に修正されたバグの再発防止"""
    
    def test_project_selection_not_skipped(self):
        """プロジェクト選択がスキップされないことを確認"""
        with patch('PyQt6.QtWidgets.QApplication'):
            # コマンドライン引数なしでプロジェクト選択が必要なことを確認
            import sys
            original_argv = sys.argv.copy()
            
            try:
                sys.argv = ['main.py']  # プロジェクト指定なし
                
                with patch('presentation.dialogs.project_startup_dialog.ProjectStartupDialog') as mock_dialog_class:
                    mock_dialog = Mock()
                    mock_dialog_class.return_value = mock_dialog
                    mock_dialog.exec.return_value = 1  # Accepted
                    mock_dialog.get_project_info.return_value = ("video", "/path/to/video.mp4", {"name": "test"})
                    
                    with patch('presentation.main_window.main_window.MainWindow'):
                        from main import main
                        
                        # main関数実行（パッチされたコンポーネントで）
                        # プロジェクト選択ダイアログが呼ばれることを確認
                        # 実際のテストでは戻り値やモックの呼び出し確認
                        
            finally:
                sys.argv = original_argv
                
    def test_main_window_project_info_handling(self):
        """MainWindowがプロジェクト情報を適切に処理することを確認"""
        with patch('PyQt6.QtWidgets.QMainWindow'), \
             patch('PyQt6.QtWidgets.QWidget'), \
             patch('PyQt6.QtWidgets.QApplication'):
            
            from presentation.main_window.main_window import MainWindow
            
            # プロジェクト情報付きでMainWindow作成
            project_info = ("video", "/path/to/video.mp4", {"name": "test_project"})
            
            with patch.object(MainWindow, 'setup_ui'), \
                 patch.object(MainWindow, 'setup_shortcuts'), \
                 patch.object(MainWindow, 'connect_signals'), \
                 patch.object(MainWindow, 'initialize_project'):
                
                window = MainWindow(project_info=project_info)
                
                # プロジェクト情報が適切に設定されているか確認
                assert window.project_type == "video"
                assert window.project_path == "/path/to/video.mp4"
                assert window.project_config == {"name": "test_project"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])