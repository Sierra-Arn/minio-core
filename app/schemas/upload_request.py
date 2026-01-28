# app/schemas/upload_request.py
import os
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .utils import validate_clean_string


class UploadFileRequest(BaseModel):
    """
    Request schema for uploading a local file to an S3-compatible object storage bucket via the REST API.
    The target bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description=(
            "Name to assign to the uploaded object in the bucket. Must be at least 1 character long and not blank."
        )
    )

    file_path: str = Field(
        ...,
        min_length=1,
        description=(
            "Local filesystem path to the file to be uploaded. Must point to an existing regular file."
        )
    )

    @field_validator("storage_key", "file_path")
    @classmethod
    def attributes_clean_string(cls, v: str) -> str:
        """Validate that string fields are non-empty, non-blank and has no leading/trailing whitespace."""
        return validate_clean_string(v, "Name")

    @field_validator("file_path")
    @classmethod
    def file_path_exists(cls, v: str) -> str:
        """Validate that the specified file path corresponds to an existing file on disk."""
        if not os.path.isfile(v):
            raise ValueError(f"File not found: {v}")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "storage_key": "critique-of-pure-reason.pdf",
                    "file_path": "./downloads/kant-philosophy.pdf"
                }
            ]
        }
    )