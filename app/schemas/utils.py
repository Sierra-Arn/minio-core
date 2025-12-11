# app/schemas/utils.py

def validate_clean_string(value: str, field_name: str = "Value") -> str:
    """
    Ensure the string is non-empty, non-blank and has no leading/trailing whitespace.

    This is typically used for identifiers, keys, names, or paths where ambiguous
    or invisible whitespace is not acceptable (e.g., S3 object keys, file names).

    Parameters
    ----------
    value : str
        The string to validate.
    field_name : str, optional
        Name of the field for error messages. Default is "Value".

    Returns
    -------
    str
        The original string if valid.

    Raises
    ------
    ValueError
        If the string is empty, blank, or has leading/trailing whitespace.
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be blank")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have leading or trailing whitespace")
    return value