# app/schemas/presigned_get_request.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .utils import validate_clean_string


class PresignedGetURLRequest(BaseModel):
    """
    Request schema for generating a pre-signed URL to download an object from object storage.
    The target bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description=(
            "Name of the object in the bucket to generate a download URL for. "
            "Must be at least 1 character long and not blank."
        )
    )

    expires: int = Field(
        300,
        ge=1,
        le=604800,  # max 7 days — S3 limit
        description=(
            "URL expiration time in seconds. Must be between 1 and 604800 (7 days). Default is 300 (5 minutes)."
        )
    )

    @field_validator("storage_key")
    @classmethod
    def attributes_clean_string(cls, v: str) -> str:
        """Validate that storage_key is non-empty, non-blank and has no leading/trailing whitespace."""
        return validate_clean_string(v, "Storage key")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "storage_key": "critique-of-pure-reason.pdf",
                    "expires": 900
                }
            ]
        }
    )