import os
import shutil
from pathlib import Path
from typing import Protocol, BinaryIO

class StorageService(Protocol):

    def save_file(self, filename: str, file_obj: BinaryIO) -> str:
        ...

    def get_file_path(self, filename: str) -> str:
        ...

class LocalStorageService:

    def __init__(self, base_dir: str='data/cv_uploads'):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, file_obj: BinaryIO) -> str:
        file_path = self.base_dir / filename
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file_obj, buffer)
        return str(Path('cv_uploads') / filename).replace('\\', '/')

    def get_file_path(self, filename: str) -> str:
        if 'cv_uploads' in filename:
            return str(Path('data') / filename)
        return str(self.base_dir / filename)

    def get_local_path(self, filename: str) -> str:
        return self.get_file_path(filename)

class S3StorageService:

    def __init__(self, bucket_name: str):
        import boto3
        self.s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.bucket_name = bucket_name

    def save_file(self, filename: str, file_obj: BinaryIO) -> str:
        self.s3.upload_fileobj(file_obj, self.bucket_name, filename)
        return f's3://{self.bucket_name}/{filename}'

    def get_file_path(self, filename: str) -> str:
        return filename

    def get_local_path(self, filename: str) -> str:
        import tempfile
        import os
        key = filename.split('/')[-1] if filename.startswith('s3://') else filename
        fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(key)[1])
        os.close(fd)
        self.s3.download_file(self.bucket_name, key, temp_path)
        return temp_path

def get_storage_service() -> StorageService:
    bucket = os.getenv('S3_BUCKET_NAME')
    if bucket:
        return S3StorageService(bucket_name=bucket)
    return LocalStorageService()