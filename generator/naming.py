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
    initialisms = {
        "id": "ID",
        "url": "URL",
        "api": "API",
        "http": "HTTP",
        "https": "HTTPS",
        "ip": "IP",
        "uuid": "UUID",
    }

    return "".join(
        initialisms.get(part, part.capitalize())
        for part in value.split("_")
    )