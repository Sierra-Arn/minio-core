# app/schemas/presigned_put_request.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .utils import validate_clean_string


class PresignedPutURLRequest(BaseModel):
    """
    Request schema for generating a pre-signed URL to upload an object directly to object storage.
    The target bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description=(
            "Name to assign to the uploaded object in the bucket. Must be at least 1 character long and not blank."
        )
    )

    expires: int = Field(
        300,
        ge=1,
        le=604800,  # max 7 days (604800 seconds) — S3 limit
        description=(
            "URL expiration time in seconds. Must be between 1 and 604800 (7 days). Default is 300 (5 minutes)."
        )
    )

    content_type: str = Field(
        "binary/octet-stream",
        min_length=1,
        description=(
            "MIME type of the object to be uploaded (e.g., 'image/png', 'application/pdf'). "
            "Must be a valid, non-blank string. Default is 'binary/octet-stream'."
        )
    )

    @field_validator("storage_key", "content_type")
    @classmethod
    def attributes_clean_string(cls, v: str) -> str:
        """Validate that string fields are non-empty, non-blank and have no leading/trailing whitespace."""
        return validate_clean_string(v, "Value")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "storage_key": "critique-of-pure-reason.pdf",
                    "expires": 600,
                    "content_type": "application/pdf"
                }
            ]
        }
    )