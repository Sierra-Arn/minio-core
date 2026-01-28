# app/schemas/download_request.py
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .utils import validate_clean_string


class DownloadFileRequest(BaseModel):
    """
    Request schema for downloading a file from an S3-compatible object storage bucket to a local path via the REST API.
    The source bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description=(
            "Name of the object to download from the bucket. Must be at least 1 character long and not blank."
        )
    )

    file_path: str = Field(
        ...,
        min_length=1,
        description=(
            "Local filesystem path where the downloaded file will be saved. "
            "The parent directory must exist and be a valid directory."
        )
    )

    @field_validator("storage_key")
    @classmethod
    def storage_key_clean_string(cls, v: str) -> str:
        """Validate that storage key is non-empty, non-blank and has no leading/trailing whitespace."""
        return validate_clean_string(v, "Object name")

    @field_validator("file_path")
    @classmethod
    def file_path_not_blank_and_parent_exists(cls, v: str) -> str:
        """
        Validate that the file path is non-empty, non-blank, has no leading/trailing whitespace
        and its parent directory exists and is a directory.
        """
        
        validate_clean_string(v, "File path")
        parent = Path(v).parent
        if not parent.is_dir():
            raise ValueError(f"Parent path is not a directory: {parent}")
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