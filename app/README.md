# **Application Structure**

*This README provides a high-level architectural overview of the project: what each component is for and why it exists. For implementation details refer to the docstrings and comments inside each file.*

## **I. Overall**

1. **`config.py`**  
   Defines configuration schemas for MinIO using Pydantic Settings, loaded from `.env` with `MINIO_` prefix.

2. **`schemas/`**  
   Contains Pydantic models that validate and structure incoming data before it is persisted to the object storage, ensuring data integrity and type safety.

3. **`utils.py`**  
   Provides core utilities for interacting with MinIO storage:
   - **Client creation**:  
   Functions to obtain synchronous (`get_client`) and asynchronous (`get_async_client`) S3-compatible clients.
   - **Bucket initialization**:  
   Creates buckets if they don't exist (`create_bucket_if_not_exists`).
   - **Lifecycle management**:  
   Configures automatic object expiration policies (`setup_lifecycle`) based on retention settings.

4. **`sync_client.py`**  
   Synchronous data access layer.

5. **`async_client.py`**  
   Asynchronous data access layer.

## **II. `sync_client.py` and `async_client.py` — Dual Data Access Layers**

Both modules provide the same API through `ObjectStorageClient` class, differing only in their execution model (synchronous vs. asynchronous). The client encapsulates all S3-compatible storage operations for a single bucket:

- **Lifecycle management**:  
Automatically creates the bucket and configures expiration policies on initialization.
- **File operations**:  
Upload, download, delete, and retrieve metadata for objects.
- **Presigned URLs**:  
Generate temporary URLs for direct client-side uploads (`PUT`) and downloads (`GET`), bypassing the application server.
- **Validation**:  
Enforces file size limits and MIME type restrictions before operations.

Each module instantiates singleton clients for predefined buckets (e.g., `documents_storage_client`, `images_storage_client`) at module level, ensuring bucket initialization happens once during application startup. The async version uses `aioboto3` with proper `async with` context management, while the sync version uses standard `boto3`.