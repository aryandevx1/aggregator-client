from .base import Generator
from generator.model import Object, Field
from generator.naming import pascal_to_snake, snake_to_go_pascal

class GoConverterGenerator(Generator): 
    _domain_import_path: str 
    _proto_import_path: str

    def __init__(
        self,
        domain_import_path: str, 
        proto_import_path: str
    ) -> None: 
        self._domain_import_path = domain_import_path
        self._proto_import_path = proto_import_path

    def _generate_nil_check(
        self
    ) -> str :
        return (
            f"\tif value == nil {{\n"
            f"\t\treturn nil, nil\n"
            f"\t}}"
        )

    def _generate_clone_function(
        self, 
    ) -> str:
        return(
            f"func clone[T any](\n"
            f"\tvalue *T,\n"
            f") *T {{\n"
            f"\tif value == nil {{\n"
            f"\t\treturn nil\n"
            f"\t}}\n\n"
            f"\tcopied := *value\n"
            f"\treturn &copied\n"
            f"}}"
        )

    def _generate_clone_slice_function(
        self, 
    ) -> str:
        return(
            f"func cloneSlice[T any](\n"
            f"\tvalue []T,\n"
            f") []T {{\n"
            f"\tif value == nil {{\n"
            f"\t\treturn nil\n"
            f"\t}}\n\n"
            f"\tcopied := make([]T, len(value))\n"
            f"\tcopy(copied, value)\n"
            f"\treturn copied\n"
            f"}}"
        )

    def _generate_field_assignment(
        self,
        field: Field
    ) -> str :
        go_field_name = snake_to_go_pascal(field.name)
        expression: str
        if field.type == "array": 
            expression = f"cloneSlice(value.{go_field_name})"
        elif field.required:
            expression = f"*value.{go_field_name}"
        else:
            expression = f"clone(value.{go_field_name})"

        return (
            f"\t\t{go_field_name}: {expression},"
        )

    def _generate_required_field_checks(
        self, 
        field: Field, 
        object_name: str
    ) -> str: 
        go_field_name = snake_to_go_pascal(field.name)

        if field.type == "array":
            return (
                f"\tif len(value.{go_field_name}) == 0 {{\n"
                f'\t\treturn nil, errors.New('
                f'"{pascal_to_snake(object_name)}.{pascal_to_snake(field.name)} must contain at least one item")\n'
                f"\t}}"
            )
        
        return (
            f"\tif value.{go_field_name} == nil {{\n"
            f'\t\treturn nil, errors.New("{pascal_to_snake(object_name)}.{pascal_to_snake(field.name)} is required")\n'
            f"\t}}"
        )

    def _generate_converter(
        self, 
        current_object: Object
    ) -> str :
        fields: list[str] = [
            self._generate_field_assignment(field)
            for field in current_object.fields
        ]

        required_field_checks: list[str] = [
            self._generate_required_field_checks(field, current_object.name)
            for field in current_object.fields 
            if field.required 
        ]

        fields_str = "\n".join(fields)
        required_checks = "\n\n".join(required_field_checks)

        sections = [
            (
                f"func {current_object.name}FromProto(\n"
                f"\tvalue *pb.{current_object.name},\n"
                f") (*domain.{current_object.name}, error) {{"
            ),
            self._generate_nil_check().rstrip(),
        ]

        if required_checks:
            sections.append(required_checks)

        sections.append(
            f"\treturn &domain.{current_object.name}{{\n"
            f"{fields_str}\n"
            f"\t}}, nil"
        )

        return "\n\n".join(sections) + "\n}"

    def _generate_imports(
        self, 
        current_object: Object
    ) -> str: 
        imports = ["import ("]

        if any(field.required for field in current_object.fields): 
            imports.append('\t"errors"')
            imports.append("")

        imports.append(
            f'\tdomain "{self._domain_import_path}"'
        )
        imports.append(
            f'\tpb "{self._proto_import_path}"'
        )
        imports.append(")")
        return "\n".join(imports)

    def _generate_helpers(
        self, 
    ) -> str :
        return (
            f"package mapper\n\n"
            f"{self._generate_clone_function()}\n\n"
            f"{self._generate_clone_slice_function()}\n"
        )

    def generate(
        self, 
        objects: list[Object]
    ) -> dict[str, str]:
        generated_files: dict[str, str] = {
            "helpers.go": self._generate_helpers()
        }
        for obj in objects: 
            converter = self._generate_converter(obj)
            imports = self._generate_imports(obj)
            content = (
                f"package mapper\n\n"
                f"{imports}\n\n"
                f"{converter}\n"
            )

            filename = f"{pascal_to_snake(obj.name)}_converter.go"
            generated_files[filename] = content


        return generated_files 
