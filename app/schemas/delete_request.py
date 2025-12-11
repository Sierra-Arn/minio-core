# app/schemas/delete_request.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .utils import validate_clean_string


class DeleteFileRequest(BaseModel):
    """
    Request schema for deleting an object from an S3-compatible object storage bucket via the REST API.
    The bucket is determined by the service configuration, not by the request.
    """

    storage_key: str = Field(
        ...,
        min_length=1,
        description=(
            "Name of the object to delete from the bucket. Must be at least 1 character long and not blank."
        )
    )

    @field_validator("storage_key")
    @classmethod
    def storage_key_clean_string(cls, v: str) -> str:
        """Validate that storage key is non-empty, non-blank and has no leading/trailing whitespace."""
        return validate_clean_string(v, "Object name")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "storage_key": "critique-of-pure-reason.pdf"
                },
                {
                    "storage_key": "cute-cat.png"
                }
            ]
        }
    )