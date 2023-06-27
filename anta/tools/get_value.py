"""
Get a value from a dictionary or nested dictionaries.
"""
from typing import Any, Dict, Optional


# pylint: disable=too-many-arguments
def get_value(
    dictionary: Dict[Any, Any], key: str, default: Optional[Any] = None, required: bool = False, org_key: Optional[str] = None, separator: str = "."
) -> Any:
    """
    Get a value from a dictionary or nested dictionaries.
    Key supports dot-notation like "foo.bar" to do deeper lookups.
    Returns the supplied default value or None if the key is not found and required is False.
    Parameters
    ----------
    dictionary : dict
        Dictionary to get key from
    key : str
        Dictionary Key - supporting dot-notation for nested dictionaries
    default : any
        Default value returned if the key is not found
    required : bool
        Fail if the key is not found
    org_key : str
        Internal variable used for raising exception with the full key name even when called recursively
    separator: str
        String to use as the separator parameter in the split function. Useful in cases when the key
        can contain variables with "." inside (e.g. hostnames)
    Returns
    -------
    any
        Value or default value
    Raises
    ------
    ValueError
        If the key is not found and required == True
    """

    if org_key is None:
        org_key = key
    keys = str(key).split(separator)
    value = dictionary.get(keys[0])
    if value is None:
        if required is True:
            raise ValueError(org_key)
        return default

    if len(keys) > 1:
        return get_value(value, separator.join(keys[1:]), default=default, required=required, org_key=org_key, separator=separator)
    return value
