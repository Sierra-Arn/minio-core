# app/utils.py

"""
S3-compatible object storage utilities for MinIO.

Provides client factories for synchronous and asynchronous boto3 connections,
and storage initialization functions (bucket creation and lifecycle configuration).

Can be run directly to create the bucket and setup lifecycle configuration:

    python -m app.utils
"""

import boto3
import aioboto3
from .config import minio_config


def get_sync_client() -> boto3.client:
    """
    Create and return a new S3-compatible boto3 client.

    Unlike database connections that maintain stateful sessions, transactions, and connection pools
    requiring explicit lifecycle management (connect -> use -> close), boto3 S3 clients are:
        - Stateless: No persistent connection state between calls.
        - Self-managing: Internal connection pooling handled by urllib3/botocore.
        - Thread-safe: Safe for concurrent use without locks.
        - Lightweight: No cleanup required, Python's garbage collector handles resource release.

    Therefore, context managers (with/yield) are unnecessary overhead. We simply create a client
    on-demand for each operation, and Python automatically releases resources when the client
    goes out of scope.

    Returns
    -------
    boto3.client
        A fully configured S3-compatible client ready for immediate use.

    Notes
    -----
    - boto3 clients are dynamically created, so static type checkers may not recognize
    their methods. This is expected and safe to ignore.

    - Unlike database connections where sharing a connection across multiple operations
    executes them within the same session or transaction, each S3 API call is always
    an independent HTTP request regardless of whether the same client instance is reused.
    Therefore, creating a fresh client per operation has no practical downside.
    """
    
    return boto3.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        aws_access_key_id=minio_config.root_username,
        aws_secret_access_key=minio_config.root_password,
        region_name="us-east-1", # Required by S3 API, MinIO ignores it
        use_ssl=False,
        verify=False,
    )


def get_async_client() -> aioboto3.Session.client:
    """
    Create and return a new asynchronous S3-compatible aioboto3 client context manager.

    aioboto3 is an async wrapper over botocore — S3 semantics are identical to the
    synchronous client. Each API call is always an independent HTTP request regardless
    of whether the same client instance is reused. Therefore, creating a fresh client
    per operation has no practical downside.

    Unlike the synchronous boto3 client however, aioboto3 uses aiohttp instead of urllib3
    for HTTP transport, which requires explicit lifecycle management. This function MUST
    be used with `async with` to ensure the underlying aiohttp session is properly
    initialized on entry and closed on exit, preventing connection leaks:

        async with get_async_client() as client:
            await client.list_buckets()

    Returns
    -------
    aioboto3.Session.client
        An async context manager that yields a fully configured S3-compatible client
        when entered with `async with`.

    Notes
    -----
    aioboto3 clients are dynamically created, so static type checkers may not recognize
    their methods. This is expected and safe to ignore.
    """
    
    session = aioboto3.Session()
    return session.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        aws_access_key_id=minio_config.root_username,
        aws_secret_access_key=minio_config.root_password,
        region_name="us-east-1", # Required by S3 API, MinIO ignores it
        use_ssl=False,
        verify=False,
    )


def create_bucket() -> None:
    """
    Create a bucket.

    Raises
    ------
    ClientError
        If bucket creation fails.
    """

    client = get_sync_client()
    client.create_bucket(Bucket=minio_config.bucket_name)


def setup_lifecycle() -> None:
    """
    Configure automatic expiration for objects under the temp prefix.

    Objects stored under `temp_prefix` are automatically deleted
    after `temp_expiration_days` days.

    Raises
    ------
    ClientError
        If lifecycle configuration fails.
    """

    client = get_sync_client()
    client.put_bucket_lifecycle_configuration(
        Bucket=minio_config.bucket_name,
        LifecycleConfiguration={
            'Rules': [
                {
                    'ID': f'auto-delete-after-{minio_config.temp_expiration_days}-days',
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': minio_config.temp_expiration_days
                    },
                    'Filter': {
                        'Prefix': minio_config.temp_prefix
                    }
                }
            ]
        }
    )


if __name__ == "__main__":
    create_bucket()
    setup_lifecycle()