import pathlib
import yaml

from .model import Object, Field

from .errors import (
    SchemaDirectoryError,
    SchemaFileError,
    SchemaParseError,
    SchemaStructureError,
)

class Loader:
    def __init__(self, dir_path: str):
        self.dir_path = dir_path    

    def _validate_dir(self, schema_dir: pathlib.Path) -> None: 
        if not schema_dir.exists(): 
            raise SchemaDirectoryError(
                f"Schema directory does not exist: {schema_dir}"
            )

        if not schema_dir.is_dir():
            raise SchemaDirectoryError(
                f"Schema path is not a directory: {schema_dir}"
            )

    def _load_yaml_file(self, file_path: pathlib.Path) -> dict : 
        try: 
            with file_path.open('r', encoding='utf-8') as file: 
                yaml_data = yaml.safe_load(file)

        except OSError as error: 
            raise SchemaFileError(
                f"Unable to read the file '{file_path.name}': {error}"
            ) from error

        except yaml.YAMLError as error: 
            raise SchemaParseError(
                f"Invalid YAML file '{file_path.name}': {error}"
            ) from error

        if yaml_data is None: 
            raise SchemaStructureError(
                f"Schema file '{file_path.name}' is empty"
            )

        if not isinstance(yaml_data, dict): 
            raise SchemaStructureError(
                f"Root of '{file_path.name}' must be a YAML object"
            )

        return yaml_data

    def _require_key(self, data: dict, key: str, location: str) -> object : 
        if key in data: 
            return data[key]

        raise SchemaStructureError(
            f"Missing required key '{key}' in {location}"
        )

    def _parse_field(self, field_data: object, file_path: pathlib.Path, index: int) -> Field :
        location = f"file path: {file_path.name}, field index: {index}"

        if not isinstance(field_data, dict): 
            raise SchemaStructureError(
                f"Field at {location} must be a YAML object"
            )

        name = self._require_key(field_data, "name", location)
        field_type = self._require_key(field_data, "type", location)

        if not isinstance(name, str):
            raise SchemaStructureError(
                f"'name' at {location} must be a string"
            )

        if not isinstance(field_type, str):
            raise SchemaStructureError(
                f"'type' at {location} must be a string"
            )

        ref = field_data.get("ref")
        values = field_data.get("values", [])
        sensitive = field_data.get("sensitive", False)
        required = field_data.get("required", False)

        if ref is not None and not isinstance(ref, str): 
            raise SchemaStructureError(
                f"'ref' at {location} must be a string"
            )

        if not isinstance(values, list):
            raise SchemaStructureError(
                f"'values' at {location} must be a list"
            )

        for value in values: 
            if not isinstance(value, str): 
                raise SchemaStructureError(
                    f"Every item in 'values' at {location} must be a string"
                )

        if not isinstance(sensitive, bool):
            raise SchemaStructureError(
                f"'sensitive' at {location} must be a boolean"
            )

        if not isinstance(required, bool): 
            raise SchemaStructureError(
                f"'required' at {location} must be a boolean"
            )

        return Field(
            name=name,
            type=field_type,
            ref=ref,
            values=values,
            sensitive=sensitive,
            required=required
        )

    def _parse_object(self, yaml_data: dict, file_path: pathlib.Path) -> Object: 
        location = f"file path: {file_path.name}"

        name = self._require_key(yaml_data, "object", location)
        kind = self._require_key(yaml_data, "kind", location)
        fields_data = self._require_key(yaml_data, "fields", location)

        if not isinstance(name, str):
            raise SchemaStructureError(
                f"'object' in '{file_path.name}' must be a string"
            )

        if not isinstance(kind, str):
            raise SchemaStructureError(
                f"'kind' in '{file_path.name}' must be a string"
            )

        if not isinstance(fields_data, list):
            raise SchemaStructureError(
                f"'fields' in '{file_path.name}' must be a list"
            )

        fields_list: list[Field] = []
        for index, field in enumerate(fields_data): 
            fields_list.append(self._parse_field(field, file_path, index))

        return Object(
            name=name, 
            kind=kind,
            fields=fields_list
        )


    def load(self) -> list[Object]:
        schema_dir = pathlib.Path(self.dir_path)
        self._validate_dir(schema_dir)

        file_paths = sorted(schema_dir.glob("*.yaml"))
        if not file_paths:
            raise SchemaDirectoryError(
                f"No YAML schema files found in: {schema_dir}"
            )
        
        objects: list[Object] = []
        for file_path in file_paths:
            yaml_data = self._load_yaml_file(file_path)
            object_data = self._parse_object(yaml_data, file_path)
            objects.append(object_data)

        return objects