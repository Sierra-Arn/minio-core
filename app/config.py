# app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinIOConfig(BaseSettings):
    """
    Configuration schema for MinIO object storage.

    Attributes
    ----------
    host : str
        Hostname or IP address of the MinIO server. Default is `"127.0.0.1"`.
    external_port : int
        TCP port the server listens on. Must be in the range 1-65535.
        Default is `9000` (standard MinIO port).
    root_username : str
        MinIO root username (acts as AWS access key).
    root_password : str
        MinIO root password (acts as AWS secret key).
    bucket_name : str
        Name of the MinIO bucket designated for storing files.
    temp_prefix : str
        Prefix for temporary files. Default is `"temp/"`.
    permanent_prefix : str
        Prefix for permanent files. Default is `"permanent/"`.
    temp_expiration_days : int
        Number of days after which objects under temp_prefix are automatically deleted.
        Default is `1`.

    Notes:
    ------
    1. Automatically loads settings from a `.env` file in the current working directory
       using a module-specific prefix specified.
    2. The `.env` file must use UTF-8 encoding. 
    3. Variable names are case-insensitive.
    4. Any extra (unrecognized) variables are silently ignored.
    5. The configuration is immutable after instantiation.
    6. During instantiation, values are resolved in the following order of precedence 
       (from highest to lowest priority):
        1. **Explicitly passed arguments** — values provided directly to the constructor.
        2. **Environment variables** — including those loaded from the `.env` file,
           prefixed according to the subclass's `env_prefix`.
        3. **Code-defined defaults** — fallback values specified as field defaults
           in the class definition.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        env_prefix="MINIO_"
    )

    host: str = "127.0.0.1"
    external_port: int = Field(9000, ge=1, le=65535)
    root_username: str
    root_password: str
    bucket_name: str
    temp_prefix: str = "temp/"
    permanent_prefix: str = "permanent/"
    temp_expiration_days: int = Field(1, ge=1)

    @property
    def connection_url(self) -> str:
        """
        Build MinIO connection URL from configuration settings.

        Returns
        -------
        str
            Complete MinIO connection URL in the format: http://host:port
        """
        return f"http://{self.host}:{self.external_port}"


minio_config = MinIOConfig()