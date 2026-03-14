# app/async_storage/service.py
import anyio
from typing import Any
from .operations import AsyncStorageOperations
from ..config import minio_config
from ..schemas import UploadFileRequest


class AsyncStorageService:
    """
    Asynchronous service for managing file operations on S3-compatible object storage.

    This class acts as a thin orchestration layer between the application and the
    underlying storage operations. It accepts Pydantic-validated request schemas,
    delegates I/O to the operations module, and enforces business rules such as:
    - Automatically applying temp or permanent prefix depending on the upload method.
    - Verifying file existence on disk before uploading.
    - Verifying object existence in the bucket before generating presigned download URLs.

    All methods are static: the class carries no instance state and exists purely
    as a logical namespace for async storage-related business logic.
    """

    @staticmethod
    async def _validate_file_path(file_path: str) -> None:
        """
        Validate that the specified file path corresponds to an existing file on disk.

        Parameters
        ----------
        file_path : str
            Local filesystem path to validate.

        Raises
        ------
        FileNotFoundError
            If no file exists at the given path.
        """

        if not await anyio.Path(file_path).is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

    @staticmethod
    async def upload_temp(request: UploadFileRequest) -> None:
        """
        Upload a local file as a temporary object.

        The file is stored under the temp prefix and will be automatically
        deleted after the configured expiration period.

        Parameters
        ----------
        request : UploadFileRequest
            Validated request containing storage_key and file_path.

        Raises
        ------
        FileNotFoundError
            If the file at file_path does not exist.
        ClientError
            If the upload operation fails.
        """

        await AsyncStorageService._validate_file_path(request.file_path)

        await AsyncStorageOperations.upload(
            bucket_name=minio_config.bucket_name,
            storage_key=f"{minio_config.temp_prefix}{request.storage_key}",
            file_path=request.file_path,
        )

    @staticmethod
    async def upload_permanent(request: UploadFileRequest) -> None:
        """
        Upload a local file as a permanent object.

        The file is stored under the permanent prefix and will not be
        automatically deleted.

        Parameters
        ----------
        request : UploadFileRequest
            Validated request containing storage_key and file_path.

        Raises
        ------
        FileNotFoundError
            If the file at file_path does not exist.
        ClientError
            If the upload operation fails.
        """

        await AsyncStorageService._validate_file_path(request.file_path)

        await AsyncStorageOperations.upload(
            bucket_name=minio_config.bucket_name,
            storage_key=f"{minio_config.permanent_prefix}{request.storage_key}",
            file_path=request.file_path,
        )

    @staticmethod
    async def download(storage_key: str, file_path: str) -> None:
        """
        Download an object from the bucket and save it to the local filesystem.

        Parameters
        ----------
        storage_key : str
            Key of the object to retrieve (including prefix).
        file_path : str
            Local path where the file will be saved.

        Raises
        ------
        ClientError
            If the object does not exist (NoSuchKey) or the download operation fails.
        """

        await AsyncStorageOperations.download(
            bucket_name=minio_config.bucket_name,
            storage_key=storage_key,
            file_path=file_path,
        )

    @staticmethod
    async def delete(storage_key: str) -> None:
        """
        Delete an object from the bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error
        (consistent with S3 semantics).

        Parameters
        ----------
        storage_key : str
            Key of the object to delete (including prefix).

        Raises
        ------
        ClientError
            If the delete operation fails.
        """

        await AsyncStorageOperations.delete(
            bucket_name=minio_config.bucket_name,
            storage_key=storage_key,
        )

    @staticmethod
    async def get_metadata(storage_key: str) -> dict[str, Any]:
        """
        Retrieve metadata about a specific object in the bucket.

        Fetches object headers (e.g., size, last modified, ETag) without downloading content.

        Parameters
        ----------
        storage_key : str
            Key of the object to inspect (including prefix).

        Returns
        -------
        dict[str, Any]
            Raw metadata response including ETag, ContentLength, LastModified,
            ContentType, and other standard S3 object attributes.

        Raises
        ------
        ClientError
            If the object does not exist (404 NotFound).
        """

        return await AsyncStorageOperations.head_object(
            bucket_name=minio_config.bucket_name,
            storage_key=storage_key,
        )

    @staticmethod
    async def generate_presigned_put_url_temp(storage_key: str, content_type: str, expires: int) -> str:
        """
        Generate a presigned URL for uploading a temporary object directly to the storage bucket.

        The object will be stored under the temp prefix and automatically deleted
        after the configured expiration period.

        Parameters
        ----------
        storage_key : str
            Key under which the uploaded object will be stored (without prefix).
        content_type : str
            MIME type of the object to be uploaded.
        expires : int
            URL expiration time in seconds.

        Returns
        -------
        str
            A temporary URL that allows direct upload to the object storage.
            The URL is only valid for the specified expiration period.
        """

        return await AsyncStorageOperations.generate_presigned_put_url(
            bucket_name=minio_config.bucket_name,
            storage_key=f"{minio_config.temp_prefix}{storage_key}",
            content_type=content_type,
            expires=expires,
        )

    @staticmethod
    async def generate_presigned_put_url_permanent(storage_key: str, content_type: str, expires: int) -> str:
        """
        Generate a presigned URL for uploading a permanent object directly to the storage bucket.

        The object will be stored under the permanent prefix and will not be
        automatically deleted.

        Parameters
        ----------
        storage_key : str
            Key under which the uploaded object will be stored (without prefix).
        content_type : str
            MIME type of the object to be uploaded.
        expires : int
            URL expiration time in seconds.

        Returns
        -------
        str
            A temporary URL that allows direct upload to the object storage.
            The URL is only valid for the specified expiration period.
        """

        return await AsyncStorageOperations.generate_presigned_put_url(
            bucket_name=minio_config.bucket_name,
            storage_key=f"{minio_config.permanent_prefix}{storage_key}",
            content_type=content_type,
            expires=expires,
        )

    @staticmethod
    async def generate_presigned_get_url(storage_key: str, expires: int) -> str:
        """
        Generate a presigned URL for downloading an object from the storage bucket.

        Verifies that the object exists before generating the URL, since S3 generates
        presigned URLs for non-existent objects without error.

        Parameters
        ----------
        storage_key : str
            Key of the object to download (including prefix).
        expires : int
            URL expiration time in seconds.

        Returns
        -------
        str
            A temporary URL that allows direct download from the object storage.
            The URL is only valid for the specified expiration period.

        Raises
        ------
        ClientError
            If the object does not exist (404 NotFound).
        """

        await AsyncStorageOperations.head_object(
            bucket_name=minio_config.bucket_name,
            storage_key=storage_key,
        )

        return await AsyncStorageOperations.generate_presigned_get_url(
            bucket_name=minio_config.bucket_name,
            storage_key=storage_key,
            expires=expires,
        )