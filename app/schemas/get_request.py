# app/schemas/get_request.py
from .delete_request import DeleteFileRequest


class GetFileRequest(DeleteFileRequest):
    """
    Request schema for retrieving metadata about an object from an S3-compatible object storage bucket via the REST API.
    The bucket is determined by the service configuration, not by the request.
    """

    # Shares identical structure with DeleteFileRequest — both only require a validated storage_key.
    # Inheritance avoids duplication while keeping types distinct for clarity and type safety.
    pass