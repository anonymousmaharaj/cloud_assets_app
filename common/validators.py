def validate_int(param):
    if param.isdigit() and int(param) > 0:
        return int(param)
    else:
        return None
