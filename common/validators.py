"""Validators for queries ana parameters."""


def validate_int(param):
    """Validate get parameter in query.

    Pass the parameter from the get request to check this value
    """
    if param.isdigit() and int(param) > 0:
        return int(param)
    else:
        return None
