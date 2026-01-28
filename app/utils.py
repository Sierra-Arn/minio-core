# app/utils.py
import boto3
from botocore.exceptions import ClientError
import aioboto3
from .config import minio_config


def get_client() -> boto3.client:
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
    boto3 clients are dynamically created, so static type checkers may not recognize
    their methods. This is expected and safe to ignore.
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


def create_bucket_if_not_exists(bucket_name: str) -> None:
    """
    Create the bucket if it doesn't already exist.

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket to create.

    Raises
    ------
    ClientError
        If bucket creation fails due to permissions, invalid name, or other errors
        (excluding BucketAlreadyExists and BucketAlreadyOwnedByYou).
    """
    
    try:
        client = get_client()
        client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            print(f"Failed to create bucket '{bucket_name}': {e}")
            raise


def setup_lifecycle(bucket_name: str, expiration_days: int) -> None:
    """
    Configure automatic object expiration based on the expiration_days setting.

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket to configure lifecycle rules for.
    expiration_days : int
        The number of days after which objects in the bucket will automatically expire
        and be deleted.

    Raises
    ------
    ClientError
        If lifecycle configuration fails.
    """

    client = get_client()
    client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            'Rules': [
                {
                    'ID': f'auto-delete-after-{expiration_days}-days',
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': expiration_days
                    },
                    'Filter': {
                        'Prefix': ''
                    }
                }
            ]
        }
    )


def get_async_client() -> aioboto3.Session.client:
    """
    Create and return a new asynchronous S3-compatible aioboto3 client context manager.

    Unlike the synchronous boto3 client which is stateless and doesn't require explicit cleanup,
    aioboto3 clients are asynchronous context managers that:
        - Manage async HTTP connections: Must be properly entered/exited to handle aiohttp sessions.
        - Require explicit lifecycle: Need `async with` to ensure proper connection cleanup.
        - Handle connection pooling: Internal aiohttp ClientSession must be closed to release sockets.
        - Prevent resource leaks: Without proper context management, connections remain open.

    Therefore, this function returns a context manager that MUST be used with `async with`:
        async with get_async_client() as client:
            await client.list_buckets()

    This ensures the underlying aiohttp session is properly initialized on entry and gracefully
    closed on exit, preventing connection leaks and resource exhaustion.

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