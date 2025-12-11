# **Application Structure**

*This README provides a high-level architectural overview of the project: what each component is for and why it exists. For implementation details refer to the docstrings and comments inside each file.*

## **I. Overall**

1. **`config.py`**  
   Defines configuration schemas for MinIO using Pydantic Settings, loaded from `.env` with `MINIO_` prefix.

2. **`schemas/`**  
   Contains Pydantic models that validate and structure incoming data before it is persisted to the object storage, ensuring data integrity and type safety.

3. **`sync_storage//`**  
   Synchronous data access layer.

4. **`async_storage//`**  
   Asynchronous data access layer.

## **II. `sync_storage/` and `async_storage/` — Dual Data Access Layers**

These directories provide **symmetrical implementations** of the same data access patterns — one for synchronous execution (`sync_storage/`), and the other for asynchronous (`async_storage/`). Both follow identical architectural boundaries but differ only in I/O model, enabling consistent logic across blocking and non-blocking contexts.

1. **`client.py`**  
   Provides a context-managed, bucket-aware MinIO (S3-compatible) client factory — synchronous or asynchronous — that guarantees:
   - Safe client instantiation using centralized MinIO credentials and endpoint,
   - Proper resource cleanup (e.g., closing async HTTP connections),
   - Isolation of storage client per operation, with no shared state.

2. **`utils.py`**  
   Exposes one-time setup routines, such as bucket creation, using the configured storage client. Intended for initialization.

3. **`service.py`**  
   Encapsulates all file operations (upload, download, delete, metadata, listing) for a fixed bucket. Accepts pre-validated Pydantic requests and delegates to the storage client, ensuring consistent, reusable, and testable data access logic.