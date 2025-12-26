from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
from pathlib import Path
from app.core.config import settings
from minio import Minio
from minio.error import S3Error
import io

class StorageInterface(ABC):
    @abstractmethod
    def save(self, file_data: bytes, file_path: str) -> str:
        """Save file and return storage path/URL"""
        pass
    
    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """Retrieve file data"""
        pass
    
    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass

class LocalStorage(StorageInterface):
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, file_data: bytes, file_path: str) -> str:
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(file_data)
        return str(full_path.relative_to(self.base_path))
    
    def get(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(full_path, 'rb') as f:
            return f.read()
    
    def delete(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def exists(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        return full_path.exists()

class MinIOStorage(StorageInterface):
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
    
    def save(self, file_data: bytes, file_path: str) -> str:
        data_stream = io.BytesIO(file_data)
        self.client.put_object(
            self.bucket,
            file_path,
            data_stream,
            length=len(file_data)
        )
        return file_path
    
    def get(self, file_path: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, file_path)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e
    
    def delete(self, file_path: str) -> bool:
        try:
            self.client.remove_object(self.bucket, file_path)
            return True
        except S3Error:
            return False
    
    def exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket, file_path)
            return True
        except S3Error:
            return False

def get_storage() -> StorageInterface:
    if settings.STORAGE_TYPE == "minio":
        return MinIOStorage()
    else:
        return LocalStorage()

