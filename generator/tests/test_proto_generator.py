from generator.generators.proto import ProtoGenerator
from generator.generators.base import Generator
from .test_helpers import make_field, make_object
import pytest 

def test_proto_generator_can_be_instantiated() -> None: 
    generator = ProtoGenerator()

    assert isinstance(generator, Generator)

@pytest.mark.parametrize(
    ("schema_type", "proto_type"), 
    [
        ("string", "string"),
        ("boolean", "bool"),
        ("number", "double")
    ]
)
def test_valid_type_conversions(schema_type: str, proto_type: str) -> None: 
    generator = ProtoGenerator()
    assert generator._get_proto_type(schema_type) == proto_type

def test_proto_generator_for_object() -> None: 
    objects = [
        make_object(
            fields=[
                make_field(name="id", tag=1),
                make_field(name="company", tag=2), 
                make_field(name="location", tag=3)
            ]
        )
    ]

    generator = ProtoGenerator()
    proto_text = generator.generate(objects=objects)

    assert proto_text['job.proto'] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  string id = 1;\n"
        "  string company = 2;\n"
        "  string location = 3;\n"
        "}\n"
    )

@pytest.mark.parametrize(
    "invalid_schema_type", 
    [
        "",
        "stringg", 
        "float"
    ]
)
def test_valid_type_conversions(invalid_schema_type: str) -> None: 
    generator = ProtoGenerator()
    with pytest.raises(
        ValueError, 
        match="Invalid field type"
    ): 
        generator._get_proto_type(invalid_schema_type)

def test_generate_proto_for_multiple_objects() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(name="id", tag=1),
            ],
        ),
        make_object(
            name="Company",
            fields=[
                make_field(name="id", tag=1),
                make_field(name="name", tag=2),
            ],
        ),
    ]

    generator = ProtoGenerator()

    generated_files = generator.generate(objects)

    assert generated_files == {
        "job.proto": (
            'syntax = "proto3";\n\n'
            "message Job {\n"
            "  string id = 1;\n"
            "}\n"
        ),
        "company.proto": (
            'syntax = "proto3";\n\n'
            "message Company {\n"
            "  string id = 1;\n"
            "  string name = 2;\n"
            "}\n"
        ),
    }

def test_generate_timestamp_field_with_required_import() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
                    tag=1,
                ),
            ],
        )
    ]

    generator = ProtoGenerator()

    generated_files = generator.generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  google.protobuf.Timestamp created_at = 1;\n"
        "}\n"
    )

def test_imports_do_not_leak_between_generated_files() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
                    tag=1,
                ),
            ],
        ),
        make_object(
            name="Company",
            fields=[
                make_field(
                    name="name",
                    type="string",
                    tag=1,
                ),
            ],
        ),
    ]

    generator = ProtoGenerator()

    generated_files = generator.generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  google.protobuf.Timestamp created_at = 1;\n"
        "}\n"
    )

    assert generated_files["company.proto"] == (
        'syntax = "proto3";\n\n'
        "message Company {\n"
        "  string name = 1;\n"
        "}\n"
    )

def test_timestamp_import_is_not_duplicated() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
                    tag=1,
                ),
                make_field(
                    name="updated_at",
                    type="timestamp",
                    tag=2,
                ),
            ],
        )
    ]

    generator = ProtoGenerator()

    generated_files = generator.generate(objects)
    content = generated_files["job.proto"]

    assert content.count(
        'import "google/protobuf/timestamp.proto";'
    ) == 1

    assert content == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  google.protobuf.Timestamp created_at = 1;\n"
        "  google.protobuf.Timestamp updated_at = 2;\n"
        "}\n"
    )