import os
import shutil
import pathlib
from typing import Union, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
import psutil

class FileManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = pathlib.Path(base_dir) if base_dir else pathlib.Path.cwd()
        self.logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=4)

    def safe_read(self, filepath: Union[str, pathlib.Path], chunk_size: int = 1024*1024) -> bytes:
        path = self._validate_path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            with open(path, 'rb') as f:
                return f.read(chunk_size)
        except Exception as e:
            self.logger.error(f"Failed to read file {path}: {e}")
            raise

    def safe_write(self, filepath: Union[str, pathlib.Path], data: bytes) -> bool:
        path = self._validate_path(filepath)
        temp_path = path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(data)
            temp_path.rename(path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def create_directory(self, dirpath: Union[str, pathlib.Path]) -> pathlib.Path:
        path = self._validate_path(dirpath)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def move_file(self, src: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> pathlib.Path:
        src_path = self._validate_path(src)
        dst_path = self._validate_path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
            
        try:
            shutil.move(str(src_path), str(dst_path))
            return dst_path
        except Exception as e:
            self.logger.error(f"Failed to move file from {src_path} to {dst_path}: {e}")
            raise

    def copy_file(self, src: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> pathlib.Path:
        src_path = self._validate_path(src)
        dst_path = self._validate_path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
            
        try:
            shutil.copy2(str(src_path), str(dst_path))
            return dst_path
        except Exception as e:
            self.logger.error(f"Failed to copy file from {src_path} to {dst_path}: {e}")
            raise

    def batch_operation(self, operation: str, files: List[Union[str, pathlib.Path]], 
                       dst: Optional[Union[str, pathlib.Path]] = None) -> List[pathlib.Path]:
        results = []
        for file in files:
            try:
                if operation == "copy" and dst:
                    results.append(self.copy_file(file, dst))
                elif operation == "move" and dst:
                    results.append(self.move_file(file, dst))
                elif operation == "delete":
                    self._validate_path(file).unlink()
                    results.append(None)
            except Exception as e:
                self.logger.error(f"Batch operation failed for {file}: {e}")
                raise
        return results

    def create_backup(self, filepath: Union[str, pathlib.Path]) -> pathlib.Path:
        path = self._validate_path(filepath)
        backup_path = path.with_suffix(f'.bak')
        return self.copy_file(path, backup_path)

    def restore_backup(self, backup_path: Union[str, pathlib.Path]) -> pathlib.Path:
        path = self._validate_path(backup_path)
        original_path = path.with_suffix('')
        return self.move_file(path, original_path)

    def check_disk_space(self, required_bytes: int) -> bool:
        usage = psutil.disk_usage(self.base_dir)
        return usage.free >= required_bytes

    def verify_file_integrity(self, filepath: Union[str, pathlib.Path], expected_hash: str = None) -> bool:
        path = self._validate_path(filepath)
        
        if not path.exists():
            return False
            
        try:
            with open(path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return True if expected_hash is None else file_hash == expected_hash
        except Exception:
            return False

    def _validate_path(self, path: Union[str, pathlib.Path]) -> pathlib.Path:
        if isinstance(path, str):
            path = pathlib.Path(path)
        
        try:
            resolved_path = path.resolve()
            if not str(resolved_path).startswith(str(self.base_dir)):
                raise ValueError(f"Path {path} is outside base directory")
            return resolved_path
        except Exception as e:
            self.logger.error(f"Path validation failed for {path}: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._executor.shutdown(wait=True)