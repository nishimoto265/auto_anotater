"""
Persistence Layer例外クラス
データ永続化エラーの分類と詳細情報を提供
"""

class PersistenceError(Exception):
    """永続化層基底例外"""
    pass

class FileIOError(PersistenceError):
    """ファイルI/Oエラー"""
    pass

class ValidationError(PersistenceError):
    """データ検証エラー"""
    pass

class BackupError(PersistenceError):
    """バックアップエラー"""
    pass

class DirectoryError(PersistenceError):
    """ディレクトリエラー"""
    pass

class PerformanceError(PersistenceError):
    """性能目標未達エラー"""
    pass