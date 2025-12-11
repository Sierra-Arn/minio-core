# app/async_storage/utils.py
from .client import get_async_minio_session
from ..config import minio_config


async def create_buckets() -> None:
    """
    Create the image and document buckets as defined in the MinIO configuration.
    """

    async with get_async_minio_session() as client:
        await client.create_bucket(Bucket=minio_config.bucket_images_name)
        await client.create_bucket(Bucket=minio_config.bucket_documents_name)