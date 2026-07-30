from .base import Generator
from generator.model import Object, Field
from dataclasses import dataclass

@dataclass(frozen=True)
class ProtoType: 
    proto_type: str
    import_path: str | None

class ProtoGenerator(Generator): 
    _TYPE_MAP = {
        "string": ProtoType("string", None),
        "boolean": ProtoType("bool", None),
        "number": ProtoType("double", None),
        "timestamp": ProtoType("google.protobuf.Timestamp", "google/protobuf/timestamp.proto")
    }

    _imports: set[str]

    def __init__(self):
        self._imports = set()
        
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

    def _generate_field(
        self, 
        field: Field
    ) -> str:
        converted_field_type = self._get_proto_type(field_type=field.type)
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

            message = self._generate_message(obj)
            imports = "\n".join(sorted(self._imports))

            sections = ['syntax = "proto3";']

            if imports:
                sections.append(imports)

            sections.append(message)

            content = "\n\n".join(sections) + "\n"

            generated_files[f"{obj.name.lower()}.proto"] = content

        return generated_files