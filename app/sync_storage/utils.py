# app/sync_storage/utils.py
from .client import get_sync_minio_session
from ..config import minio_config


def create_buckets() -> None:
    """
    Create the image and document buckets as defined in the MinIO configuration.
    """
    
    with get_sync_minio_session() as client:
        client.create_bucket(Bucket=minio_config.bucket_images_name)
        client.create_bucket(Bucket=minio_config.bucket_documents_name)