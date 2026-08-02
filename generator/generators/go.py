from .base import Generator
from generator.model import Object, Field
from dataclasses import dataclass
from generator.naming import pascal_to_snake, snake_to_go_pascal


@dataclass
class GoType: 
    go_type: str
    import_path: str | None = None  


class GoGenerator(Generator): 
    _TYPE_MAP = {
        "string": GoType("string", None),
        "boolean": GoType("bool", None),
        "number": GoType("float64", None),
        "timestamp": GoType("time.Time", "time"), 
        "reference": GoType("string", None), 
        "array": GoType("[]string", None), 
        "composite": GoType("composite", None), 
        "enum": GoType("enum", None)
    }

    _imports: set[str]
    _enums: list[str]

    def __init__(
        self, 
    ):
        self._imports = set()
        self._enums = []

    def _generate_enum(
        self, 
        field: Field, 
        object_name: str
    ) -> str: 
        enum_name = object_name + snake_to_go_pascal(field.name)

        enum_values: list[str] = []
        for value in field.values: 
            value_name = enum_name + snake_to_go_pascal(value.name)
            enum_values.append(f'\t{value_name} {enum_name} = "{value.name}"')

        values = "\n".join(enum_values)

        enum_definition = (
            f"type {enum_name} string\n\n"
            f"const (\n"
            f"{values}\n"
            f")"
        )

        self._enums.append(enum_definition)
        return enum_name

    def _get_go_type(
        self,
        field: Field, 
        object_name: str
    ) -> str:
        converted_type = self._TYPE_MAP.get(field.type)
        if field.type == "composite": 
            return field.ref

        if field.type == "enum": 
            return self._generate_enum(field, object_name)
            

        if converted_type.import_path is not None: 
            self._imports.add(converted_type.import_path)

        return converted_type.go_type

    def _apply_required(
        self,
        field: Field,
        go_type: str,
    ) -> str:
        if field.type == "array":
            return go_type

        if field.required:
            return go_type

        return f"*{go_type}"

    def _generate_json_tag(
        self,
        field: Field,
    ) -> str:
        if field.required:
            return f'`json:"{field.name}"`'

        return f'`json:"{field.name},omitempty"`'

    def _generate_field(
        self, 
        field: Field, 
        object_name: str
    ) -> str :
        go_type = self._get_go_type(field, object_name)
        go_type = self._apply_required(field, go_type)

        field_name = snake_to_go_pascal(field.name)
        json_tag = self._generate_json_tag(field)

        return f"\t{field_name} {go_type} {json_tag}"
    
    def _generate_struct(
        self, 
        current_object: Object 
    ) -> str: 
        fields = "\n".join(
            self._generate_field(field, current_object.name)
            for field in current_object.fields
        )

        return (
            f"type {current_object.name} struct {{\n"
            f"{fields}\n"
            f"}}"
        )

    def _generate_imports(
        self
    ) -> str :
        if not self._imports: 
            return ""

        sorted_imports = sorted(self._imports)
        if len(sorted_imports) == 1:
            return f'import "{sorted_imports[0]}"'

        lines = ["import ("]

        for import_path in sorted_imports:
            lines.append(f'\t"{import_path}"')

        lines.append(")")

        return "\n".join(lines)

    def generate(
        self, 
        objects: list[Object]
    ) -> dict[str, str]:
        generated_files: dict[str, str] = {}

        for obj in objects: 
            self._enums.clear()
            self._imports.clear()

            struct_definition = self._generate_struct(obj)

            sections = ["package domain"]
            imports = self._generate_imports()
            if imports: 
                sections.append(imports)

            if self._enums: 
                sections.extend(self._enums)

            sections.append(struct_definition)
            content = "\n\n".join(sections) + "\n"

            generated_files[
                f"{pascal_to_snake(obj.name)}.go"
            ] = content

        return generated_files