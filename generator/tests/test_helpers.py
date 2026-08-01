from generator.model import Field, Object, EnumValue

def make_field(
    name: str = "name",
    type: str = "string",
    ref: str | None = None,
    required: bool = True,
    values: list[str | tuple[str, int] | EnumValue] | None = None,
    sensitive: bool = False,
    tag: int | None = None, 
    value_type: str | None = None      
) -> Field: 
    enum_values: list[EnumValue] = []

    for value in values or []:
        if isinstance(value, EnumValue):
            enum_values.append(value)
        elif isinstance(value, tuple):
            value_name, value_tag = value
            enum_values.append(
                EnumValue(
                    name=value_name,
                    tag=value_tag,
                )
            )
        else:
            enum_values.append(
                EnumValue(
                    name=value,
                    tag=None,
                )
            )

    return Field(
        name=name, 
        type=type, 
        ref=ref, 
        required=required, 
        values=enum_values, 
        sensitive=sensitive, 
        tag=tag, 
        value_type=value_type
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