import pytest
import yaml
from pathlib import Path
from generator.errors import SchemaDirectoryError, SchemaStructureError
from generator.loader import Loader
from generator.model import EnumValue

def test_missing_schema_directory(tmp_path: Path) -> None : 
    missing_dir = tmp_path / "missing"
    loader = Loader(missing_dir)

    with pytest.raises(SchemaDirectoryError, match="Schema directory does not exist"): 
        loader.load()

def test_schema_path_is_file(tmp_path: Path) -> None : 
    test_file = tmp_path / "schema.yaml"
    test_file.write_text("", encoding="utf-8")

    loader = Loader(test_file)
    with pytest.raises(SchemaDirectoryError, match="Schema path is not a directory"): 
        loader.load() 

def test_empty_schema_directory(tmp_path: Path) -> None:
    loader = Loader(tmp_path)

    with pytest.raises(
        SchemaDirectoryError,
        match="No YAML schema files found",
    ):
        loader.load()

def test_empty_yaml_file(tmp_path: Path) -> None: 
    schema_file = tmp_path / "user.yaml"
    schema_file.write_text("", encoding="utf-8")

    loader = Loader(tmp_path)
    with pytest.raises(
        SchemaStructureError,
        match="is empty",
    ):
        loader.load()

from generator.errors import SchemaParseError


def test_invalid_yaml_syntax(tmp_path: Path) -> None:
    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        """
object: User
kind: entity
fields: [
""",
        encoding="utf-8",
    )

    loader = Loader(tmp_path)

    with pytest.raises(SchemaParseError):
        loader.load()

def test_yaml_root_must_be_object(tmp_path: Path) -> None:
    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        """
- object: User
- kind: entity
""",
        encoding="utf-8",
    )

    loader = Loader(tmp_path)

    with pytest.raises(
        SchemaStructureError,
        match="must be a YAML object",
    ):
        loader.load()

@pytest.mark.parametrize(
    "missing_key", 
    [
        "name", 
        "type", 
    ]
)
def test_missing_required_field_key(tmp_path, missing_key) -> None: 
    field_data = {
        "name": "email",
        "type": "string"
    }

    del field_data[missing_key]

    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [field_data],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    loader = Loader(tmp_path)

    with pytest.raises(
        SchemaStructureError,
        match=f"Missing required key '{missing_key}'",
    ):
        loader.load()


@pytest.mark.parametrize(
    ("key", "invalid_value"),
    [
        ("ref", 123),
        ("values", "ACTIVE"),
        ("sensitive", "true"),
    ],
)
def test_invalid_optional_field_property_type(
    tmp_path: Path,
    key: str,
    invalid_value: object,
) -> None:
    field_data = {
        "name": "status",
        "type": "enum",
        key: invalid_value,
    }

    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [field_data],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    loader = Loader(tmp_path)

    with pytest.raises(SchemaStructureError):
        loader.load()

def test_enum_values_must_contain_only_strings(
    tmp_path: Path,
) -> None:
    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [
            {
                "name": "status",
                "type": "enum",
                "values": ["ACTIVE", 123],
            }
        ],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    loader = Loader(tmp_path)

    with pytest.raises(
        SchemaStructureError,
        match="must be a string",
    ):
        loader.load()

def test_load_valid_schema(tmp_path: Path) -> None:
    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [
            {
                "name": "email",
                "type": "string",
                "sensitive": True,
            },
            {
                "name": "status",
                "type": "enum",
                "values": ["ACTIVE", "INACTIVE"],
            },
        ],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    loader = Loader(tmp_path)
    objects = loader.load()

    assert len(objects) == 1

    user = objects[0]
    assert user.name == "User"
    assert user.kind == "entity"
    assert len(user.fields) == 2

    assert user.fields[0].name == "email"
    assert user.fields[0].sensitive is True

    assert user.fields[1].values == [
        EnumValue("ACTIVE"),
        EnumValue("INACTIVE")
    ]

def test_field_optional_properties_use_defaults(
    tmp_path: Path,
) -> None:
    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [
            {
                "name": "email",
                "type": "string",
            }
        ],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    field = Loader(tmp_path).load()[0].fields[0]

    assert field.ref is None
    assert field.values == []
    assert field.sensitive is False

def test_value_type_must_be_string(
    tmp_path: Path,
) -> None:
    schema_data = {
        "object": "User",
        "kind": "entity",
        "fields": [
            {
                "name": "emails",
                "type": "array",
                "value_type": 1
            }
        ],
    }

    schema_file = tmp_path / "user.yaml"
    schema_file.write_text(
        yaml.safe_dump(schema_data),
        encoding="utf-8",
    )

    with pytest.raises(
        SchemaStructureError, 
        match="must be a string"
    ): 
        Loader(tmp_path).load()
        