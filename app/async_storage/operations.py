# app/async_storage/operations.py
from typing import Any
from ..utils import get_async_client


class AsyncStorageOperations:
    """
    Low-level asynchronous S3 operations for interacting with object storage.

    This class is a pure I/O layer: it performs no validation, applies no business rules,
    and has no knowledge of bucket configuration or prefixes. All parameters are passed
    explicitly by the caller.

    All methods are static: the class carries no instance state and exists purely
    as a logical namespace for async S3-related I/O operations.
    """

    @staticmethod
    async def upload(bucket_name: str, storage_key: str, file_path: str) -> None:
        """
        Upload a local file to the bucket under the specified storage key.

        Parameters
        ----------
        bucket_name : str
            Name of the target bucket.
        storage_key : str
            The key under which to store the file.
        file_path : str
            Absolute or relative path to an existing local file.

        Raises
        ------
        ClientError
            If the upload operation fails.
        FileNotFoundError
            If the file at file_path does not exist.
        """

        async with get_async_client() as client:
            await client.upload_file(Filename=file_path, Bucket=bucket_name, Key=storage_key)

    @staticmethod
    async def download(bucket_name: str, storage_key: str, file_path: str) -> None:
        """
        Download an object from the bucket and save it to the local filesystem.

        Parameters
        ----------
        bucket_name : str
            Name of the source bucket.
        storage_key : str
            Key of the object to retrieve.
        file_path : str
            Local path where the file will be saved.

        Raises
        ------
        ClientError
            If the object does not exist (NoSuchKey) or the download operation fails.
        """

        async with get_async_client() as client:
            await client.download_file(Bucket=bucket_name, Key=storage_key, Filename=file_path)

    @staticmethod
    async def delete(bucket_name: str, storage_key: str) -> None:
        """
        Delete an object from the bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error
        (consistent with S3 semantics).

        Parameters
        ----------
        bucket_name : str
            Name of the target bucket.
        storage_key : str
            Key of the object to delete.

        Raises
        ------
        ClientError
            If the delete operation fails.
        """

        async with get_async_client() as client:
            await client.delete_object(Bucket=bucket_name, Key=storage_key)

    @staticmethod
    async def head_object(bucket_name: str, storage_key: str) -> dict[str, Any]:
        """
        Retrieve metadata about a specific object in the bucket.

        Fetches object headers (e.g., size, last modified, ETag) without downloading content.

        Parameters
        ----------
        bucket_name : str
            Name of the target bucket.
        storage_key : str
            Key of the object to inspect.

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

        async with get_async_client() as client:
            return await client.head_object(Bucket=bucket_name, Key=storage_key)

    @staticmethod
    async def generate_presigned_put_url(
        bucket_name: str,
        storage_key: str,
        content_type: str,
        expires: int,
    ) -> str:
        """
        Generate a presigned URL for uploading an object directly to the storage bucket.

        Parameters
        ----------
        bucket_name : str
            Name of the target bucket.
        storage_key : str
            Key under which the uploaded object will be stored.
        content_type : str
            MIME type of the object to be uploaded.
        expires : int
            URL expiration time in seconds.

        Returns
        -------
        str
            A temporary URL that allows direct upload to the object storage.
        """

        async with get_async_client() as client:
            return await client.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucket_name, 'Key': storage_key, 'ContentType': content_type},
                ExpiresIn=expires,
            )

    @staticmethod
    async def generate_presigned_get_url(bucket_name: str, storage_key: str, expires: int) -> str:
        """
        Generate a presigned URL for downloading an object from the storage bucket.

        Parameters
        ----------
        bucket_name : str
            Name of the target bucket.
        storage_key : str
            Key of the object to download.
        expires : int
            URL expiration time in seconds.

        Returns
        -------
        str
            A temporary URL that allows direct download from the object storage.
        """

        async with get_async_client() as client:
            return await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': storage_key},
                ExpiresIn=expires,
            )