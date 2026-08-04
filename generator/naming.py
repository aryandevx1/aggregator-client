import re

def pascal_to_snake(name: str) -> str:
    return re.sub(
        r"(?<!^)(?=[A-Z])",
        "_",
        name,
    ).lower()


def snake_to_pascal(name: str) -> str:
    return "".join(
        part.capitalize()
        for part in name.split("_")
    )

def snake_to_go_pascal(value: str) -> str:
    GO_INITIALISMS = {
        "id": "ID",
        "ids": "IDs",
        "url": "URL",
        "urls": "URLs",
        "api": "API",
        "apis": "APIs",
        "http": "HTTP",
        "https": "HTTPS",
        "ip": "IP",
        "ips": "IPs",
        "uuid": "UUID",
        "uuids": "UUIDs",
    }

    return "".join(
        GO_INITIALISMS.get(part, part.capitalize())
        for part in value.split("_")
    )