# app/async_storage/client.py
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import aioboto3
from ..config import minio_config


@asynccontextmanager
async def get_async_minio_session() -> AsyncGenerator[aioboto3.Session.client, None]:
    """
    Asynchronous context manager for safe and automatic MinIO client lifecycle management.

    Provides a scoped S3-compatible client that is:
    1. Instantiated upon entry using application-wide MinIO credentials and endpoint,
    2. Yielded to the calling code block for S3 operations (e.g., upload, download, delete),
    3. Automatically closed upon exit to ensure clean resource cleanup in async environments.

    Yields
    ------
    aioboto3.client
        A fully configured, ready-to-use asynchronous MinIO (S3) client.

    Notes
    -----
    - Unlike boto3 clients, aioboto3 clients are not stateless and must be properly
      closed to release underlying async HTTP connections. Hence, the context manager
      ensures proper cleanup via 'async with'.
    - The client is created dynamically at runtime via aioboto3's session factory.
      As a result, static type checkers (e.g., mypy, Pylance) may not
      recognize its methods or attributes, leading to "unresolved attribute"
      warnings. This is expected and safe to ignore in S3-compatible usage.
    """

    session = aioboto3.Session(
        aws_access_key_id=minio_config.root_username,
        aws_secret_access_key=minio_config.root_password,
        region_name="us-east-1",  # Required by S3 API, MinIO ignores it
    )
    async with session.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        use_ssl=False,
        verify=False,
    ) as client:
        yield client