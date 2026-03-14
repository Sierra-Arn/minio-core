# app/schemas/upload_request.py
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo


class UploadFileRequest(BaseModel):
    """
    Request schema for uploading a local file to an S3-compatible object storage bucket via the REST API.
    The target bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description="Name to assign to the uploaded object in the bucket. Must be at least 1 character long and not blank."
    )

    file_path: str = Field(
        ...,
        min_length=1,
        description="Local filesystem path to the file to be uploaded."
    )

    @field_validator("storage_key", "file_path")
    @classmethod
    def validate_clean_string(cls, v: str, info: ValidationInfo) -> str:
        """Validate that string fields are non-empty, non-blank and have no leading/trailing whitespace."""
        field_name = info.field_name

        if not v:
            raise ValueError(f"{field_name} cannot be empty")
        if not v.strip():
            raise ValueError(f"{field_name} cannot be blank")
        if v != v.strip():
            raise ValueError(f"{field_name} must not have leading or trailing whitespace")

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