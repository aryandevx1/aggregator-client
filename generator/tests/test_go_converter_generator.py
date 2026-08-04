from generator.generators.base import Generator
from generator.generators.go_converter import (
    GoConverterGenerator,
)

from .test_helpers import make_field, make_object


DOMAIN_IMPORT_PATH = "example.com/generated/domain"
PROTO_IMPORT_PATH = "example.com/generated/proto"
EXPECTED_HELPERS_FILE = (
    "package mapper\n\n"
    "func clone[T any](\n"
    "\tvalue *T,\n"
    ") *T {\n"
    "\tif value == nil {\n"
    "\t\treturn nil\n"
    "\t}\n\n"
    "\tcopied := *value\n"
    "\treturn &copied\n"
    "}\n\n"
    "func cloneSlice[T any](\n"
    "\tvalue []T,\n"
    ") []T {\n"
    "\tif value == nil {\n"
    "\t\treturn nil\n"
    "\t}\n\n"
    "\tcopied := make([]T, len(value))\n"
    "\tcopy(copied, value)\n"
    "\treturn copied\n"
    "}\n"
)

def make_generator() -> GoConverterGenerator:
    return GoConverterGenerator(
        domain_import_path=DOMAIN_IMPORT_PATH,
        proto_import_path=PROTO_IMPORT_PATH,
    )


def test_go_converter_generator_can_be_instantiated() -> None:
    generator = GoConverterGenerator("", "")

    assert isinstance(generator, Generator)


def test_generate_shared_helpers_file() -> None:
    generated_files = make_generator().generate([])

    assert generated_files == {
        "helpers.go": EXPECTED_HELPERS_FILE,
    }


def test_generate_converter_for_required_string_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files == {
        "helpers.go": EXPECTED_HELPERS_FILE,
        "job_converter.go": (
            "package mapper\n\n"
            "import (\n"
            '\t"errors"\n\n'
            f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
            f'\tpb "{PROTO_IMPORT_PATH}"\n'
            ")\n\n"
            "func JobFromProto(\n"
            "\tvalue *pb.Job,\n"
            ") (*domain.Job, error) {\n\n"
            "\tif value == nil {\n"
            "\t\treturn nil, nil\n"
            "\t}\n\n"
            "\tif value.Title == nil {\n"
            '\t\treturn nil, errors.New("job.title is required")\n'
            "\t}\n\n"
            "\treturn &domain.Job{\n"
            "\t\tTitle: *value.Title,\n"
            "\t}, nil\n"
            "}\n"
        ),
    }


def test_generate_converter_for_optional_string_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="description",
                    type="string",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tDescription: clone(value.Description),\n"
        "\t}, nil\n"
        "}\n"
    )

    assert "helpers.go" in generated_files
    assert '"errors"' not in generated_files["job_converter.go"]


def test_generate_converter_for_required_and_optional_strings() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="description",
                    type="string",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        '\t"errors"\n\n'
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\tif value.Title == nil {\n"
        '\t\treturn nil, errors.New("job.title is required")\n'
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tTitle: *value.Title,\n"
        "\t\tDescription: clone(value.Description),\n"
        "\t}, nil\n"
        "}\n"
    )


def test_generate_converter_for_required_scalar_fields() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    required=True,
                ),
                make_field(
                    name="score",
                    type="number",
                    required=True,
                ),
                make_field(
                    name="company_id",
                    type="reference",
                    ref="Company",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        '\t"errors"\n\n'
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\tif value.Title == nil {\n"
        '\t\treturn nil, errors.New("job.title is required")\n'
        "\t}\n\n"
        "\tif value.Active == nil {\n"
        '\t\treturn nil, errors.New("job.active is required")\n'
        "\t}\n\n"
        "\tif value.Score == nil {\n"
        '\t\treturn nil, errors.New("job.score is required")\n'
        "\t}\n\n"
        "\tif value.CompanyID == nil {\n"
        '\t\treturn nil, errors.New("job.company_id is required")\n'
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tTitle: *value.Title,\n"
        "\t\tActive: *value.Active,\n"
        "\t\tScore: *value.Score,\n"
        "\t\tCompanyID: *value.CompanyID,\n"
        "\t}, nil\n"
        "}\n"
    )


def test_generate_converter_for_optional_scalar_fields() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="description",
                    type="string",
                    required=False,
                ),
                make_field(
                    name="active",
                    type="boolean",
                    required=False,
                ),
                make_field(
                    name="score",
                    type="number",
                    required=False,
                ),
                make_field(
                    name="company_id",
                    type="reference",
                    ref="Company",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tDescription: clone(value.Description),\n"
        "\t\tActive: clone(value.Active),\n"
        "\t\tScore: clone(value.Score),\n"
        "\t\tCompanyID: clone(value.CompanyID),\n"
        "\t}, nil\n"
        "}\n"
    )

    assert '"errors"' not in generated_files["job_converter.go"]


def test_generate_multiple_converter_files_with_one_helpers_file() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    required=True,
                ),
            ],
        ),
        make_object(
            name="Company",
            fields=[
                make_field(
                    name="name",
                    type="string",
                    required=False,
                ),
            ],
        ),
    ]

    generated_files = make_generator().generate(objects)

    assert set(generated_files) == {
        "helpers.go",
        "job_converter.go",
        "company_converter.go",
    }

    assert generated_files["helpers.go"].count(
        "func clone[T any]"
    ) == 1

    assert "clone(" not in generated_files["job_converter.go"]
    assert (
        "Name: clone(value.Name),"
        in generated_files["company_converter.go"]
    )

    assert '"errors"' in generated_files["job_converter.go"]
    assert '"errors"' not in generated_files["company_converter.go"]


def test_converter_uses_go_initialisms_for_field_names() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="source_url",
                    type="string",
                    required=False,
                ),
                make_field(
                    name="company_id",
                    type="reference",
                    ref="Company",
                    required=True,
                ),
            ],
        )
    ]

    generated = make_generator().generate(objects)[
        "job_listing_converter.go"
    ]

    assert "if value.ID == nil {" in generated
    assert "ID: *value.ID," in generated
    assert "SourceURL: clone(value.SourceURL)," in generated
    assert "if value.CompanyID == nil {" in generated
    assert "CompanyID: *value.CompanyID," in generated

    assert (
        'errors.New("job_listing.company_id is required")'
        in generated
    )

def test_generate_optional_array_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="keywords",
                    type="array",
                    value_type="string",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tKeywords: cloneSlice(value.Keywords),\n"
        "\t}, nil\n"
        "}\n"
    )

    assert '"errors"' not in generated_files["job_converter.go"]


def test_generate_required_array_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="keywords",
                    type="array",
                    value_type="string",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        '\t"errors"\n\n'
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobFromProto(\n"
        "\tvalue *pb.Job,\n"
        ") (*domain.Job, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\tif len(value.Keywords) == 0 {\n"
        '\t\treturn nil, errors.New("job.keywords must contain at least one item")\n'
        "\t}\n\n"
        "\treturn &domain.Job{\n"
        "\t\tKeywords: cloneSlice(value.Keywords),\n"
        "\t}, nil\n"
        "}\n"
    )


def test_generate_array_and_scalar_fields_together() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="title",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="description",
                    type="string",
                    required=False,
                ),
                make_field(
                    name="skills",
                    type="array",
                    value_type="string",
                    required=True,
                ),
                make_field(
                    name="tags",
                    type="array",
                    value_type="string",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = make_generator().generate(objects)

    assert generated_files["job_listing_converter.go"] == (
        "package mapper\n\n"
        "import (\n"
        '\t"errors"\n\n'
        f'\tdomain "{DOMAIN_IMPORT_PATH}"\n'
        f'\tpb "{PROTO_IMPORT_PATH}"\n'
        ")\n\n"
        "func JobListingFromProto(\n"
        "\tvalue *pb.JobListing,\n"
        ") (*domain.JobListing, error) {\n\n"
        "\tif value == nil {\n"
        "\t\treturn nil, nil\n"
        "\t}\n\n"
        "\tif value.Title == nil {\n"
        '\t\treturn nil, errors.New("job_listing.title is required")\n'
        "\t}\n\n"
        "\tif len(value.Skills) == 0 {\n"
        '\t\treturn nil, errors.New("job_listing.skills must contain at least one item")\n'
        "\t}\n\n"
        "\treturn &domain.JobListing{\n"
        "\t\tTitle: *value.Title,\n"
        "\t\tDescription: clone(value.Description),\n"
        "\t\tSkills: cloneSlice(value.Skills),\n"
        "\t\tTags: cloneSlice(value.Tags),\n"
        "\t}, nil\n"
        "}\n"
    )


def test_helpers_file_contains_clone_slice() -> None:
    generated_files = make_generator().generate([])

    assert generated_files["helpers.go"] == (
        "package mapper\n\n"
        "func clone[T any](\n"
        "\tvalue *T,\n"
        ") *T {\n"
        "\tif value == nil {\n"
        "\t\treturn nil\n"
        "\t}\n\n"
        "\tcopied := *value\n"
        "\treturn &copied\n"
        "}\n\n"
        "func cloneSlice[T any](\n"
        "\tvalue []T,\n"
        ") []T {\n"
        "\tif value == nil {\n"
        "\t\treturn nil\n"
        "\t}\n\n"
        "\tcopied := make([]T, len(value))\n"
        "\tcopy(copied, value)\n"
        "\treturn copied\n"
        "}\n"
    )


def test_array_field_uses_go_initialism_name() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="api_urls",
                    type="array",
                    value_type="string",
                    required=False,
                ),
            ],
        )
    ]

    generated = make_generator().generate(objects)[
        "job_converter.go"
    ]

    assert "APIURLs: cloneSlice(value.APIURLs)," in generated