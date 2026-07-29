from generator.model import Field, Object

def make_field(
    name: str = "name",
    type: str = "string",
    ref: str | None = None,
    required: bool = True,
    values: list[str] | None = None,
    sensitive: bool = False,
    tag: int | None = None      
) -> Field: 
    return Field(
        name=name, 
        type=type, 
        ref=ref, 
        required=required, 
        values=[] if values is None else values, 
        sensitive=sensitive, 
        tag=tag
    )

def make_object(
    name: str = "Job",
    kind: str = "entity", 
    fields: list[Field] | None = None
) -> Object: 
    return Object(
        name=name, 
        kind=kind,
        fields=[] if fields is None else fields
    )    