# **Application Structure**

*This README provides a high-level architectural overview of the project: what each component is for and why it exists. For implementation details refer to the docstrings and comments inside each file.*

## **I. `config.py`**

Defines configuration schema for MinIO using Pydantic Settings, loaded from `.env` with `MINIO_` prefix. Contains connection settings, bucket name, prefix definitions (`temp/`, `permanent/`), and lifecycle expiration policy for temporary objects.

## **II. `utils.py`**

Provides factory functions for creating S3-compatible clients:
- `get_sync_client()` — returns a configured boto3 client for synchronous use.
- `get_async_client()` — returns a configured aioboto3 context manager for asynchronous use.

Also contains storage initialization utilities (`create_bucket`, `setup_lifecycle`, `init_storage`) that must be called explicitly once at application startup — analogous to database migrations.

## **III. `schemas/`**

Contains Pydantic models that validate and structure incoming data before it reaches the service layer. Following REST conventions, schemas are defined **only for operations that require structured input** (i.e., upload). Read, delete, and presigned URL operations accept plain scalar parameters directly.

## **IV. `sync_storage/` and `async_storage/` — Dual Storage Access Layers**

These directories provide **symmetrical implementations** of the same storage access patterns — one for synchronous execution (`sync_storage/`), and the other for asynchronous (`async_storage/`). Both follow identical architectural boundaries but differ only in I/O model.

1. **`operations.py`**  
   **Low-level S3 I/O layer with zero business logic.**  
   Provides a static class that wraps raw boto3/aioboto3 API calls: upload, download, delete, head_object, and presigned URL generation. Operations accept only plain scalar parameters and have no knowledge of bucket configuration, prefixes, or application rules. This layer is a thin, composable abstraction over the S3 client.

2. **`service.py`**  
   **The enforcement layer for business rules and orchestration.**  
   Services:
   - Accept **validated Pydantic schemas** as input (for upload) or **plain scalar parameters** (for all other operations),
   - Automatically apply `temp/` or `permanent/` prefix depending on the upload method,
   - Verify file existence on disk before uploading,
   - Verify object existence in the bucket before generating presigned download URLs,
   - Read `bucket_name` directly from config — callers never specify it explicitly.

   This design ensures that prefix logic, existence checks, and bucket routing are centralized and never leak into the calling code.

## **V. REST-inspired Interface Conventions**

Method signatures across operations and services follow REST conventions to maintain a consistent and predictable interface:
- Upload operations accept **full Pydantic schemas** (analogous to **request body**).
- Download, delete, and metadata operations accept **plain scalar identifiers** like `storage_key: str` (analogous to **path parameters**).
- Presigned URL operations accept **plain scalar parameters** like `storage_key`, `content_type`, and `expires` (analogous to **query parameters**).

This is also reflected in the schema design: Pydantic models are defined **only for upload operations**, as all other operations require no structured input.