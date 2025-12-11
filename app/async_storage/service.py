# app/async_storage/service.py
from typing import Any
from .client import get_async_minio_session
from ..schemas import UploadFileRequest, DownloadFileRequest, DeleteFileRequest, GetFileRequest
from ..config import minio_config


class FileService:
    """
    Asynchronous service for managing file operations on a single S3-compatible storage bucket.

    This class encapsulates all interactions with object storage (e.g., MinIO) for a **fixed bucket**. 
    The service is designed to be instantiated per bucket (e.g., `FileService("documents")`), rather than subclassed,
    because:
        - All buckets follow the same operational semantics (upload, download, delete, metadata).
        - No bucket-specific rules exists that would justify inheritance.

    Each method acquires a fresh async storage client via an async context manager, guaranteeing proper
    resource cleanup and safe concurrency in async environments. Input data is assumed to be pre-validated by Pydantic schemas.

    Attributes
    ----------
    bucket_name : str
        The name of the bucket this service instance operates on. Set at initialization and immutable.
    """

    def __init__(self, bucket_name: str):
        """
        Initialize the service with a target bucket.

        Parameters
        ----------
        bucket_name : str
            Name of the S3-compatible bucket to manage.
            The bucket is assumed to exist; the service does not create it.
        """

        self.bucket_name = bucket_name

    async def upload(self, request: UploadFileRequest) -> None:
        """
        Upload a local file to the service's bucket under the specified storage key.

        The method delegates to the underlying S3-compatible client and assumes the local file
        exists (validated by the request schema). No deduplication or overwrite checks are performed.

        Parameters
        ----------
        request : UploadFileRequest
            Validated request containing:
                - storage_key: the key/path under which to store the file in the bucket,
                - file_path: absolute or relative path to an existing local file.
        """

        async with get_async_minio_session() as client:
            await client.upload_file(
                Filename=request.file_path,
                Bucket=self.bucket_name,
                Key=request.storage_key
            )

    async def download(self, request: DownloadFileRequest) -> None:
        """
        Download an object from the service's bucket and save it to the local filesystem.

        The destination parent directory must exist (validated by the request schema).
        If a file already exists at `file_path`, it will be overwritten.

        Parameters
        ----------
        request : DownloadFileRequest
            Validated request containing:
                - storage_key: key of the object to retrieve,
                - file_path: local path where the file will be saved.
        """
        
        async with get_async_minio_session() as client:
            await client.download_file(
                Bucket=self.bucket_name,
                Key=request.storage_key,
                Filename=request.file_path
            )

    async def delete(self, request: DeleteFileRequest) -> None:
        """
        Delete an object from the service's bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error
        (consistent with S3 semantics). The service does not validate object existence beforehand.

        Parameters
        ----------
        request : DeleteFileRequest
            Validated request containing:
                - storage_key: key of the object to delete.
        """
        
        async with get_async_minio_session() as client:
            await client.delete_object(
                Bucket=self.bucket_name,
                Key=request.storage_key
            )

    async def get(self, request: GetFileRequest) -> dict[str, Any]:
        """
        Retrieve metadata about a specific object in the bucket.

        This method fetches object headers (e.g., size, last modified, ETag) without downloading content.
        It is useful for checking existence, verifying integrity, or inspecting attributes.

        Parameters
        ----------
        request : GetFileRequest
            Validated request containing:
                - storage_key: the key of the object to inspect. Must not be empty or blank.

        Returns
        -------
        dict[str, Any]
            Raw metadata response from the S3-compatible storage, including:
                - ETag
                - ContentLength
                - LastModified
                - ContentType (if set)
                - and other standard S3 object attributes.
        """

        async with get_async_minio_session() as client:
            return await client.head_object(Bucket=self.bucket_name, Key=request.storage_key)

    async def get_all(self, max_keys: int = 100) -> list[dict[str, Any]]:
        """
        Retrieve a paginated list of all objects in the service's bucket.

        This method provides a snapshot of bucket contents (up to `max_keys` items) and is intended
        for administrative, debugging, or low-frequency operational use — not for performance-critical
        or user-facing listing at scale.

        Parameters
        ----------
        max_keys : int, optional
            Maximum number of objects to return in a single response. 
            The value is automatically clamped to the S3-compatible storage limit of 1000.
            Default is `100`.

        Returns
        -------
        list[dict[str, Any]]
            A list of object metadata summaries. Each dictionary includes standard S3 fields:
                - Key: object key (path) in the bucket,
                - Size: object size in bytes,
                - LastModified: datetime of last modification,
                - ETag: entity tag for integrity/versioning,
                - StorageClass: storage tier (e.g., "STANDARD").
            Returns an empty list if the bucket contains no objects.
        """
        async with get_async_minio_session() as client:
            response = await client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=min(max_keys, 1000)
            )
            return response.get("Contents", [])


# Initialize FileService singletons for predefined buckets
# Since the application explicitly creates and manages a fixed set of buckets
# during startup via `minio_config`, and these bucket names remain constant for the application's lifetime,
# it is safe, efficient, and semantically correct to instantiate dedicated
# `FileService` instances once at module level.
documents_service = FileService(bucket_name=minio_config.bucket_documents_name)  
images_service = FileService(bucket_name=minio_config.bucket_images_name)