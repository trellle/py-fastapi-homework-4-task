from fastapi import Depends
from storages import S3StorageInterface, S3StorageClient
from config import BaseAppSettings, get_settings


def get_s3_storage_client(settings: BaseAppSettings = Depends(get_settings)) -> S3StorageInterface:
    return S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME
    )
