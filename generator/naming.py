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