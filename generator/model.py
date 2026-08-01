from dataclasses import dataclass, field 

@dataclass
class EnumValue:
    name: str
    tag: int | None = None

@dataclass
class Field:
    name: str
    type: str
    ref: str | None
    required: bool
    values: list[EnumValue] = field(default_factory=list)
    sensitive: bool = False
    tag: int | None = None

@dataclass 
class Object:
    name: str
    kind: str
    fields: list[Field] = field(default_factory=list)