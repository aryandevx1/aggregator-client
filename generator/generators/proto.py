from .base import Generator
from generator.model import Object, Field
from dataclasses import dataclass
from generator.naming import pascal_to_snake, snake_to_pascal

@dataclass(frozen=True)
class ProtoType: 
    proto_type: str
    import_path: str | None

class ProtoGenerator(Generator): 
    _TYPE_MAP = {
        "string": ProtoType("string", None),
        "boolean": ProtoType("bool", None),
        "number": ProtoType("double", None),
        "timestamp": ProtoType("google.protobuf.Timestamp", "google/protobuf/timestamp.proto"), 
        "enum": ProtoType("enum", None), 
        "composite": ProtoType("composite", None), 
        "reference": ProtoType("reference", None)
    }

    _imports: set[str]
    _enums: list[str]

    def __init__(self):
        self._imports = set()
        self._enums = []

    def _get_proto_type(
        self, 
        field_type: str
    ) -> str: 
        converted_field = self._TYPE_MAP.get(field_type)
        if converted_field is None: 
            raise ValueError(
                f"Invalid field type, {field_type} is not supported"
            )

        if converted_field.import_path is not None: 
            self._imports.add(f'import "{converted_field.import_path}";')
        
        return converted_field.proto_type
    
    def _generate_enum(
        self,
        field: Field
    ) -> None:  
        enum_values: list[str] = []
        for value in field.values:
            enum_values.append(f"  {field.name.upper()}_{value.name.upper()} = {value.tag};")

        values = "\n".join(enum_values)
        enum_proto_str = (
            f"enum {snake_to_pascal(field.name)} {{\n"
            f"  {field.name.upper()}_UNSPECIFIED = 0;\n"
            f"{values}\n"
            f"}}"
        )

        self._enums.append(enum_proto_str)

    def _generate_field(
        self, 
        field: Field
    ) -> str:
        converted_field_type = self._get_proto_type(field_type=field.type)
        if converted_field_type == "enum": 
            self._generate_enum(field)
            converted_field_type = snake_to_pascal(field.name)

        if converted_field_type in ["composite", "reference"]: 
            converted_field_type = field.ref
            self._imports.add(f'import "{pascal_to_snake(field.ref)}.proto";')

        return f"  {converted_field_type} {field.name} = {field.tag};" 

    def _generate_message(
        self, 
        current_object: Object,  
    ) -> str:
        field_list = [
            self._generate_field(field) 
            for field in current_object.fields
        ]

        fields = "\n".join(field_list)

        return (
            f"message {current_object.name} {{\n"
            f"{fields}\n"
            f"}}"
        )

    def generate(
        self,
        objects: list[Object],
    ) -> dict[str, str]:
        generated_files: dict[str, str] = {}

        for obj in objects:
            self._imports.clear()
            self._enums.clear()

            message = self._generate_message(obj)
            imports = "\n".join(sorted(self._imports))
            enums = "\n\n".join(self._enums)
            sections = ['syntax = "proto3";']

            if imports:
                sections.append(imports)
            if enums: 
                sections.append(enums)

            sections.append(message)

            content = "\n\n".join(sections) + "\n"

            generated_files[f"{pascal_to_snake(obj.name)}.proto"] = content

        return generated_files