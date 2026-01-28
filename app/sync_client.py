# app/sync_client.py
from typing import Any
import os
import mimetypes
from botocore.exceptions import ClientError
from .schemas import (
    UploadFileRequest, 
    DownloadFileRequest, 
    DeleteFileRequest, 
    GetFileMetadataRequest, 
    PresignedPutURLRequest, 
    PresignedGetURLRequest
)
from .config import minio_config
from .utils import get_client, setup_lifecycle, create_bucket_if_not_exists


class ObjectStorageClient:
    """
    Synchronous client for managing file operations on a single S3-compatible storage bucket.

    This class encapsulates all interactions with object storage (e.g., MinIO) for a fixed bucket.
    The client is designed to be instantiated per bucket rather than subclassed because all buckets
    follow the same operational semantics without bucket-specific rules that would justify inheritance.

    Each public method creates a fresh S3 client on-demand. Input data is assumed to be pre-validated
    by Pydantic schemas before reaching these methods.

    Attributes
    ----------
    bucket_name : str
        The name of the bucket this client instance operates on.
    max_file_size : int
        Maximum allowed file size in bytes.
    allowed_mime_types : set[str]
        Set of allowed MIME types.
    expiration_days : int | None
        Number of days after which objects are automatically deleted, or None for no expiration.
    """

    def __init__(
        self,
        bucket_name: str,
        max_file_size: int,
        allowed_mime_types: list[str],
        expiration_days: int | None = None,
    ):
        """
        Initialize the target bucket and optional constraints.

        The bucket is created if it does not exist. If an expiration policy is specified,
        it is automatically configured after bucket creation.

        Parameters
        ----------
        bucket_name : str
            Name of the S3-compatible bucket to manage.
        max_file_size : int
            Maximum file size in bytes.
        allowed_mime_types : list[str]
            list of allowed MIME types. Internally converted to a set for performance.
        expiration_days : int | None, optional
            Number of days after which objects in the bucket are automatically deleted.
            If None, no expiration policy is set. Default is None.
        """
        
        self.bucket_name = bucket_name
        self.max_file_size = max_file_size
        self.allowed_mime_types = set(allowed_mime_types) if allowed_mime_types is not None else None
        self.expiration_days = expiration_days

        create_bucket_if_not_exists(bucket_name=self.bucket_name)

        if self.expiration_days is not None:
            setup_lifecycle(bucket_name=self.bucket_name, expiration_days=self.expiration_days)


    def _validate_file_size(self, file_path: str) -> None:
        """
        Validate that the file size does not exceed the configured maximum.

        Parameters
        ----------
        file_path : str
            Path to the file to validate.

        Raises
        ------
        ValueError
            If file size exceeds max_file_size.
        """

        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValueError(
                f"File size {file_size} bytes exceeds maximum allowed size of {self.max_file_size} bytes"
            )


    def _validate_mime_type(self, mime_type: str) -> None:
        """
        Validate that the given MIME type is allowed for this bucket.

        Parameters
        ----------
        mime_type : str
            The MIME type to validate (e.g., 'image/jpeg', 'application/pdf').

        Raises
        ------
        ValueError
            If the MIME type is not in the allowed set.
        """

        if self.allowed_mime_types is not None:
            if mime_type not in self.allowed_mime_types:
                raise ValueError(
                    f"MIME type '{mime_type}' is not allowed. Allowed types: {sorted(self.allowed_mime_types)}"
                )


    def upload(self, request: UploadFileRequest) -> None:
        """
        Upload a local file to the bucket under the specified storage key.

        Parameters
        ----------
        request : UploadFileRequest
            Validated request containing storage_key (the key/path under which to store the file)
            and file_path (absolute or relative path to an existing local file).

        Raises
        ------
        ValueError
            If file validation fails (size or MIME type constraints).
        ClientError
            If the upload operation fails.
        """

        self._validate_file_size(request.file_path)
        mime_type, _ = mimetypes.guess_type(request.file_path)
        self._validate_mime_type(mime_type)

        client = get_client()
        client.upload_file(
            Filename=request.file_path,
            Bucket=self.bucket_name,
            Key=request.storage_key
        )

    def download(self, request: DownloadFileRequest) -> None:
        """
        Download an object from the bucket and save it to the local filesystem.

        Parameters
        ----------
        request : DownloadFileRequest
            Validated request containing storage_key (key of the object to retrieve)
            and file_path (local path where the file will be saved).

        Raises
        ------
        ClientError
            If the object does not exist (NoSuchKey) or the download operation fails.
        """
        
        client = get_client()
        client.download_file(
            Bucket=self.bucket_name,
            Key=request.storage_key,
            Filename=request.file_path
        )


    def delete(self, request: DeleteFileRequest) -> None:
        """
        Delete an object from the bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error
        (consistent with S3 semantics). The client does not validate object existence beforehand.

        Parameters
        ----------
        request : DeleteFileRequest
            Validated request containing storage_key (key of the object to delete).

        Raises
        ------
        ClientError
            If the delete operation fails for reasons other than the object not existing.
        """
        
        client = get_client()
        client.delete_object(
            Bucket=self.bucket_name,
            Key=request.storage_key
        )


    def get_metadata(self, request: GetFileMetadataRequest) -> dict[str, Any]:
        """
        Retrieve metadata about a specific object in the bucket.

        This method fetches object headers (e.g., size, last modified, ETag) without downloading content.
        It is useful for checking existence, verifying integrity, or inspecting attributes.

        Parameters
        ----------
        request : GetFileRequest
            Validated request containing storage_key (key of the object to inspect).

        Returns
        -------
        dict[str, Any]
            Raw metadata response from the S3-compatible storage, including ETag, ContentLength,
            LastModified, ContentType (if set), and other standard S3 object attributes.

        Raises
        ------
        ClientError
            If the object does not exist (404 NotFound).
        """
        
        client = get_client()
        return client.head_object(Bucket=self.bucket_name, Key=request.storage_key)


    def generate_presigned_put_url(self, request: PresignedPutURLRequest) -> str:
        """
        Generate a presigned URL for uploading an object directly to the storage bucket.

        This enables client-side uploads without routing data through the application server,
        reducing bandwidth costs and latency. The client must include the correct Content-Type
        header when making the PUT request.

        Parameters
        ----------
        request : PresignedPutURLRequest
            Validated request containing storage_key, expires, and content_type.

        Returns
        -------
        str
            A temporary URL that allows direct upload to the object storage.
            The URL is only valid for the specified expiration period.

        Raises
        ------
        ValueError
            If `content_type` is not allowed according to `allowed_mime_types`.
        """
        
        self._validate_mime_type(request.content_type)

        client = get_client()
        return client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': request.storage_key,
                'ContentType': request.content_type
            },
            ExpiresIn=request.expires
        )

    def generate_presigned_get_url(self, request: PresignedGetURLRequest) -> str:
        """
        Generate a presigned URL for downloading an object from the storage bucket.

        This enables client-side downloads without routing data through the application server,
        reducing bandwidth costs and improving performance for large files.

        Parameters
        ----------
        request : PresignedGetURLRequest
            Validated request containing storage_key and expires.

        Returns
        -------
        str
            A temporary URL that allows direct download from the object storage.
            The URL is only valid for the specified expiration period.
        """

        try:
            metadata_request = GetFileMetadataRequest(storage_key=request.storage_key)
            self.get_metadata(metadata_request)
        except ClientError as e:
            raise

        client = get_client()
        return client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': request.storage_key
            },
            ExpiresIn=request.expires
        )


# Initialize ObjectStorageClient singletons for predefined buckets.
# Since the application explicitly creates and manages a fixed set of buckets during startup
# via minio_config, and these bucket names remain constant for the application's lifetime,
# it is safe, efficient, and semantically correct to instantiate dedicated ObjectStorageClient
# instances once at module level.

documents_storage_client = ObjectStorageClient(
    bucket_name=minio_config.documents_bucket_name,
    max_file_size=minio_config.documents_max_file_size,
    allowed_mime_types=minio_config.documents_allowed_mime_types,
    expiration_days=minio_config.documents_expiration_days
)

images_storage_client = ObjectStorageClient(
    bucket_name=minio_config.images_bucket_name,
    max_file_size=minio_config.images_max_file_size,
    allowed_mime_types=minio_config.images_allowed_mime_types,
    expiration_days=minio_config.images_expiration_days
)