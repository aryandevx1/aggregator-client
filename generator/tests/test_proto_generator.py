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
        ("number", "double"),
        ("timestamp", "google.protobuf.Timestamp"),
        ("enum", "enum"),
        ("composite", "composite"),
        ("reference", "string"),
        ("array", "repeated string"),
    ],
)
def test_valid_type_conversions(
    schema_type: str,
    proto_type: str,
) -> None:
    generator = ProtoGenerator()

    assert generator._get_proto_type(schema_type) == proto_type


@pytest.mark.parametrize(
    "invalid_schema_type",
    [
        "",
        "stringg",
        "float",
    ],
)
def test_invalid_type_conversion(
    invalid_schema_type: str,
) -> None:
    generator = ProtoGenerator()

    with pytest.raises(
        ValueError,
        match="Invalid field type",
    ):
        generator._get_proto_type(invalid_schema_type)


def test_generate_proto_for_object() -> None:
    objects = [
        make_object(
            fields=[
                make_field(name="id", tag=1),
                make_field(name="company", tag=2),
                make_field(name="location", tag=3),
            ]
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  optional string id = 1;\n"
        "  optional string company = 2;\n"
        "  optional string location = 3;\n"
        "}\n"
    )


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

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files == {
        "job.proto": (
            'syntax = "proto3";\n\n'
            "message Job {\n"
            "  optional string id = 1;\n"
            "}\n"
        ),
        "company.proto": (
            'syntax = "proto3";\n\n'
            "message Company {\n"
            "  optional string id = 1;\n"
            "  optional string name = 2;\n"
            "}\n"
        ),
    }


def test_generate_optional_scalar_fields() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    tag=1,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    tag=2,
                ),
                make_field(
                    name="score",
                    type="number",
                    tag=3,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  optional string title = 1;\n"
        "  optional bool active = 2;\n"
        "  optional double score = 3;\n"
        "}\n"
    )


def test_required_flag_does_not_change_scalar_presence() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    tag=1,
                    required=True,
                ),
                make_field(
                    name="description",
                    type="string",
                    tag=2,
                    required=False,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    tag=3,
                    required=True,
                ),
                make_field(
                    name="score",
                    type="number",
                    tag=4,
                    required=False,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  optional string title = 1;\n"
        "  optional string description = 2;\n"
        "  optional bool active = 3;\n"
        "  optional double score = 4;\n"
        "}\n"
    )


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

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  google.protobuf.Timestamp created_at = 1;\n"
        "}\n"
    )


def test_required_flag_does_not_add_optional_to_timestamp() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
                    tag=1,
                    required=True,
                ),
                make_field(
                    name="updated_at",
                    type="timestamp",
                    tag=2,
                    required=False,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  google.protobuf.Timestamp created_at = 1;\n"
        "  google.protobuf.Timestamp updated_at = 2;\n"
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

    generated_files = ProtoGenerator().generate(objects)

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
        "  optional string name = 1;\n"
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

    generated_files = ProtoGenerator().generate(objects)
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


def test_generate_proto_with_enum_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    tag=1,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  enum Status {\n"
        "    STATUS_UNSPECIFIED = 0;\n"
        "    STATUS_OPEN = 1;\n"
        "    STATUS_CLOSED = 2;\n"
        "    STATUS_OTHER = 3;\n"
        "  }\n\n"
        "  Status status = 1;\n"
        "}\n"
    )


def test_enum_field_is_not_optional_regardless_of_required_flag() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="required_status",
                    type="enum",
                    tag=1,
                    required=True,
                    values=[
                        ("open", 1),
                        ("other", 2),
                    ],
                ),
                make_field(
                    name="optional_status",
                    type="enum",
                    tag=2,
                    required=False,
                    values=[
                        ("open", 1),
                        ("other", 2),
                    ],
                ),
            ],
        )
    ]

    generated = ProtoGenerator().generate(objects)["job.proto"]

    assert (
        "  RequiredStatus required_status = 1;"
        in generated
    )
    assert (
        "  OptionalStatus optional_status = 2;"
        in generated
    )

    assert "optional RequiredStatus" not in generated
    assert "optional OptionalStatus" not in generated


def test_generate_proto_with_enum_and_primitive_fields() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    tag=1,
                ),
                make_field(
                    name="status",
                    type="enum",
                    tag=2,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
                make_field(
                    name="active",
                    type="boolean",
                    tag=3,
                ),
                make_field(
                    name="score",
                    type="number",
                    tag=4,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  enum Status {\n"
        "    STATUS_UNSPECIFIED = 0;\n"
        "    STATUS_OPEN = 1;\n"
        "    STATUS_CLOSED = 2;\n"
        "    STATUS_OTHER = 3;\n"
        "  }\n\n"
        "  optional string id = 1;\n"
        "  Status status = 2;\n"
        "  optional bool active = 3;\n"
        "  optional double score = 4;\n"
        "}\n"
    )


def test_enum_field_name_is_converted_to_pascal_case() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="work_model",
                    type="enum",
                    tag=1,
                    values=[
                        ("remote", 1),
                        ("hybrid", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  enum WorkModel {\n"
        "    WORK_MODEL_UNSPECIFIED = 0;\n"
        "    WORK_MODEL_REMOTE = 1;\n"
        "    WORK_MODEL_HYBRID = 2;\n"
        "    WORK_MODEL_OTHER = 3;\n"
        "  }\n\n"
        "  WorkModel work_model = 1;\n"
        "}\n"
    )


def test_generate_multiple_enums_in_same_proto_file() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    tag=1,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
                make_field(
                    name="work_model",
                    type="enum",
                    tag=2,
                    values=[
                        ("remote", 1),
                        ("hybrid", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  enum Status {\n"
        "    STATUS_UNSPECIFIED = 0;\n"
        "    STATUS_OPEN = 1;\n"
        "    STATUS_CLOSED = 2;\n"
        "    STATUS_OTHER = 3;\n"
        "  }\n\n"
        "  enum WorkModel {\n"
        "    WORK_MODEL_UNSPECIFIED = 0;\n"
        "    WORK_MODEL_REMOTE = 1;\n"
        "    WORK_MODEL_HYBRID = 2;\n"
        "    WORK_MODEL_OTHER = 3;\n"
        "  }\n\n"
        "  Status status = 1;\n"
        "  WorkModel work_model = 2;\n"
        "}\n"
    )


def test_enums_do_not_leak_between_generated_files() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    tag=1,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
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

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        "message Job {\n"
        "  enum Status {\n"
        "    STATUS_UNSPECIFIED = 0;\n"
        "    STATUS_OPEN = 1;\n"
        "    STATUS_CLOSED = 2;\n"
        "    STATUS_OTHER = 3;\n"
        "  }\n\n"
        "  Status status = 1;\n"
        "}\n"
    )

    assert generated_files["company.proto"] == (
        'syntax = "proto3";\n\n'
        "message Company {\n"
        "  optional string name = 1;\n"
        "}\n"
    )


def test_generate_proto_with_enum_and_timestamp_import() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    tag=1,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
                make_field(
                    name="created_at",
                    type="timestamp",
                    tag=2,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job.proto"] == (
        'syntax = "proto3";\n\n'
        'import "google/protobuf/timestamp.proto";\n\n'
        "message Job {\n"
        "  enum Status {\n"
        "    STATUS_UNSPECIFIED = 0;\n"
        "    STATUS_OPEN = 1;\n"
        "    STATUS_CLOSED = 2;\n"
        "    STATUS_OTHER = 3;\n"
        "  }\n\n"
        "  Status status = 1;\n"
        "  google.protobuf.Timestamp created_at = 2;\n"
        "}\n"
    )


def test_generate_proto_with_composite_field() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    tag=1,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  Location location = 1;\n"
        "}\n"
    )


def test_required_flag_does_not_add_optional_to_composite() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="primary_location",
                    type="composite",
                    ref="Location",
                    tag=1,
                    required=True,
                ),
                make_field(
                    name="secondary_location",
                    type="composite",
                    ref="Location",
                    tag=2,
                    required=False,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  Location primary_location = 1;\n"
        "  Location secondary_location = 2;\n"
        "}\n"
    )


def test_generate_proto_with_composite_and_primitive_fields() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    tag=1,
                ),
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    tag=2,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    tag=3,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  optional string id = 1;\n"
        "  Location location = 2;\n"
        "  optional bool active = 3;\n"
        "}\n"
    )


def test_composite_import_is_not_duplicated() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="primary_location",
                    type="composite",
                    ref="Location",
                    tag=1,
                ),
                make_field(
                    name="secondary_location",
                    type="composite",
                    ref="Location",
                    tag=2,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)
    content = generated_files["job_listing.proto"]

    assert content.count('import "location.proto";') == 1

    assert content == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  Location primary_location = 1;\n"
        "  Location secondary_location = 2;\n"
        "}\n"
    )


def test_generate_sorted_composite_imports() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="salary_range",
                    type="composite",
                    ref="SalaryRange",
                    tag=1,
                ),
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    tag=2,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n'
        'import "salary_range.proto";\n\n'
        "message JobListing {\n"
        "  SalaryRange salary_range = 1;\n"
        "  Location location = 2;\n"
        "}\n"
    )


def test_composite_imports_do_not_leak_between_generated_files() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
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

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  Location location = 1;\n"
        "}\n"
    )

    assert generated_files["company.proto"] == (
        'syntax = "proto3";\n\n'
        "message Company {\n"
        "  optional string name = 1;\n"
        "}\n"
    )


def test_generate_proto_with_reference_field() -> None:
    objects = [
        make_object(
            name="Notification",
            fields=[
                make_field(
                    name="user",
                    type="reference",
                    ref="User",
                    tag=1,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["notification.proto"] == (
        'syntax = "proto3";\n\n'
        "message Notification {\n"
        "  optional string user = 1;\n"
        "}\n"
    )


def test_reference_is_optional_regardless_of_required_flag() -> None:
    objects = [
        make_object(
            name="Notification",
            fields=[
                make_field(
                    name="user",
                    type="reference",
                    ref="User",
                    tag=1,
                    required=True,
                ),
                make_field(
                    name="related_user",
                    type="reference",
                    ref="User",
                    tag=2,
                    required=False,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["notification.proto"] == (
        'syntax = "proto3";\n\n'
        "message Notification {\n"
        "  optional string user = 1;\n"
        "  optional string related_user = 2;\n"
        "}\n"
    )


def test_generate_proto_with_composite_and_reference_fields() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    tag=1,
                ),
                make_field(
                    name="company",
                    type="reference",
                    ref="Company",
                    tag=2,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["job_listing.proto"] == (
        'syntax = "proto3";\n\n'
        'import "location.proto";\n\n'
        "message JobListing {\n"
        "  Location location = 1;\n"
        "  optional string company = 2;\n"
        "}\n"
    )


def test_generate_proto_with_string_array_field() -> None:
    objects = [
        make_object(
            name="SavedFilter",
            fields=[
                make_field(
                    name="keywords",
                    type="array",
                    value_type="string",
                    tag=1,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["saved_filter.proto"] == (
        'syntax = "proto3";\n\n'
        "message SavedFilter {\n"
        "  repeated string keywords = 1;\n"
        "}\n"
    )


def test_required_flag_does_not_add_optional_to_array() -> None:
    objects = [
        make_object(
            name="SavedFilter",
            fields=[
                make_field(
                    name="required_keywords",
                    type="array",
                    value_type="string",
                    tag=1,
                    required=True,
                ),
                make_field(
                    name="optional_keywords",
                    type="array",
                    value_type="string",
                    tag=2,
                    required=False,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["saved_filter.proto"] == (
        'syntax = "proto3";\n\n'
        "message SavedFilter {\n"
        "  repeated string required_keywords = 1;\n"
        "  repeated string optional_keywords = 2;\n"
        "}\n"
    )


def test_generate_proto_with_array_and_primitive_fields() -> None:
    objects = [
        make_object(
            name="SavedFilter",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    tag=1,
                ),
                make_field(
                    name="keywords",
                    type="array",
                    value_type="string",
                    tag=2,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    tag=3,
                ),
            ],
        )
    ]

    generated_files = ProtoGenerator().generate(objects)

    assert generated_files["saved_filter.proto"] == (
        'syntax = "proto3";\n\n'
        "message SavedFilter {\n"
        "  optional string id = 1;\n"
        "  repeated string keywords = 2;\n"
        "  optional bool active = 3;\n"
        "}\n"
    )