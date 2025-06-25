"""
pytest設定ファイル
QApplicationの管理とテスト環境のセットアップ
"""

import sys
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp_session():
    """セッション全体で共有されるQApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def qapp(qapp_session):
    """各テスト用のQApplicationフィクスチャ"""
    return qapp_session


def pytest_configure(config):
    """pytest設定"""
    # カスタムマーカーの登録
    config.addinivalue_line(
        "markers", "ui: UI関連のテスト"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テスト"
    )
    config.addinivalue_line(
        "markers", "regression: 回帰テスト"
    )