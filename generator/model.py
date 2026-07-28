from dataclasses import dataclass, field 

@dataclass
class Field:
    name: str
    type: str
    ref: str | None
    required: bool
    values: list[str] = field(default_factory=list)
    sensitive: bool = False

@dataclass 
class Object:
    name: str
    kind: str
    fields: list[Field] = field(default_factory=list)