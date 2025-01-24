from datetime import datetime


def formatAsDate(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    return value
