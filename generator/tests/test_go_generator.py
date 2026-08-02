import pytest

from generator.generators.base import Generator
from generator.generators.go import GoGenerator

from .test_helpers import make_field, make_object


def test_go_generator_can_be_instantiated() -> None:
    generator = GoGenerator()

    assert isinstance(generator, Generator)


@pytest.mark.parametrize(
    ("field_type", "expected_go_type"),
    [
        ("string", "string"),
        ("boolean", "bool"),
        ("number", "float64"),
        ("timestamp", "time.Time"),
        ("reference", "string"),
        ("array", "[]string"),
    ],
)
def test_get_go_type_for_supported_fields(
    field_type: str,
    expected_go_type: str,
) -> None:
    field = make_field(
        name="value",
        type=field_type,
        value_type="string" if field_type == "array" else None,
    )

    generator = GoGenerator()

    assert generator._get_go_type(field, "") == expected_go_type


def test_get_go_type_for_composite_field() -> None:
    field = make_field(
        name="location",
        type="composite",
        ref="Location",
    )

    generator = GoGenerator()

    assert generator._get_go_type(field, "") == "Location"


@pytest.mark.parametrize(
    ("field_type", "required", "base_type", "expected_type"),
    [
        ("string", True, "string", "string"),
        ("string", False, "string", "*string"),
        ("boolean", True, "bool", "bool"),
        ("boolean", False, "bool", "*bool"),
        ("number", True, "float64", "float64"),
        ("number", False, "float64", "*float64"),
        ("timestamp", True, "time.Time", "time.Time"),
        ("timestamp", False, "time.Time", "*time.Time"),
        ("reference", True, "string", "string"),
        ("reference", False, "string", "*string"),
        ("composite", True, "Location", "Location"),
        ("composite", False, "Location", "*Location"),
        ("array", True, "[]string", "[]string"),
        ("array", False, "[]string", "[]string"),
    ],
)
def test_apply_required_to_go_type(
    field_type: str,
    required: bool,
    base_type: str,
    expected_type: str,
) -> None:
    field = make_field(
        name="value",
        type=field_type,
        required=required,
        ref="Location" if field_type == "composite" else None,
        value_type="string" if field_type == "array" else None,
    )

    generator = GoGenerator()

    actual_type = generator._apply_required(
        field=field,
        go_type=base_type,
    )

    assert actual_type == expected_type


def test_generate_json_tag_for_required_field() -> None:
    field = make_field(
        name="source_url",
        type="string",
        required=True,
    )

    generator = GoGenerator()

    assert (
        generator._generate_json_tag(field)
        == '`json:"source_url"`'
    )


def test_generate_json_tag_for_optional_field() -> None:
    field = make_field(
        name="source_url",
        type="string",
        required=False,
    )

    generator = GoGenerator()

    assert (
        generator._generate_json_tag(field)
        == '`json:"source_url,omitempty"`'
    )


def test_generate_required_and_optional_scalar_fields() -> None:
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
                make_field(
                    name="active",
                    type="boolean",
                    required=True,
                ),
                make_field(
                    name="score",
                    type="number",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type Job struct {\n"
        '\tTitle string `json:"title"`\n'
        '\tDescription *string '
        '`json:"description,omitempty"`\n'
        '\tActive bool `json:"active"`\n'
        '\tScore *float64 `json:"score,omitempty"`\n'
        "}\n"
    )


def test_generate_timestamp_fields_and_import() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
                    required=True,
                ),
                make_field(
                    name="posted_at",
                    type="timestamp",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        'import "time"\n\n'
        "type Job struct {\n"
        '\tCreatedAt time.Time `json:"created_at"`\n'
        '\tPostedAt *time.Time '
        '`json:"posted_at,omitempty"`\n'
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
                    required=True,
                ),
                make_field(
                    name="updated_at",
                    type="timestamp",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)
    content = generated_files["job.go"]

    assert content.count('import "time"') == 1


def test_generate_composite_fields() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    required=True,
                ),
                make_field(
                    name="salary_range",
                    type="composite",
                    ref="SalaryRange",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job_listing.go"] == (
        "package domain\n\n"
        "type JobListing struct {\n"
        '\tLocation Location `json:"location"`\n'
        '\tSalaryRange *SalaryRange '
        '`json:"salary_range,omitempty"`\n'
        "}\n"
    )


def test_generate_reference_fields() -> None:
    objects = [
        make_object(
            name="Notification",
            fields=[
                make_field(
                    name="user",
                    type="reference",
                    ref="User",
                    required=True,
                ),
                make_field(
                    name="related_job",
                    type="reference",
                    ref="JobListing",
                    required=False,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["notification.go"] == (
        "package domain\n\n"
        "type Notification struct {\n"
        '\tUser string `json:"user"`\n'
        '\tRelatedJob *string '
        '`json:"related_job,omitempty"`\n'
        "}\n"
    )


def test_generate_optional_array_field() -> None:
    objects = [
        make_object(
            name="SavedFilter",
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

    generated_files = GoGenerator().generate(objects)

    assert generated_files["saved_filter.go"] == (
        "package domain\n\n"
        "type SavedFilter struct {\n"
        '\tKeywords []string '
        '`json:"keywords,omitempty"`\n'
        "}\n"
    )


def test_generate_required_array_field() -> None:
    objects = [
        make_object(
            name="SavedFilter",
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

    generated_files = GoGenerator().generate(objects)

    assert generated_files["saved_filter.go"] == (
        "package domain\n\n"
        "type SavedFilter struct {\n"
        '\tKeywords []string `json:"keywords"`\n'
        "}\n"
    )


def test_generate_go_field_names_using_initialisms() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="source_url",
                    type="string",
                    required=True,
                ),
                make_field(
                    name="api_key",
                    type="string",
                    required=False,
                ),
                make_field(
                    name="user_id",
                    type="string",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type Job struct {\n"
        '\tID string `json:"id"`\n'
        '\tSourceURL string `json:"source_url"`\n'
        '\tAPIKey *string `json:"api_key,omitempty"`\n'
        '\tUserID string `json:"user_id"`\n'
        "}\n"
    )


def test_generate_multiple_go_files() -> None:
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
                    required=True,
                ),
            ],
        ),
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files == {
        "job.go": (
            "package domain\n\n"
            "type Job struct {\n"
            '\tTitle string `json:"title"`\n'
            "}\n"
        ),
        "company.go": (
            "package domain\n\n"
            "type Company struct {\n"
            '\tName string `json:"name"`\n'
            "}\n"
        ),
    }


def test_imports_do_not_leak_between_generated_files() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="created_at",
                    type="timestamp",
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
                    required=True,
                ),
            ],
        ),
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        'import "time"\n\n'
        "type Job struct {\n"
        '\tCreatedAt time.Time `json:"created_at"`\n'
        "}\n"
    )

    assert generated_files["company.go"] == (
        "package domain\n\n"
        "type Company struct {\n"
        '\tName string `json:"name"`\n'
        "}\n"
    )

def test_generate_required_enum_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=True,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type JobStatus string\n\n"
        "const (\n"
        '\tJobStatusOpen JobStatus = "open"\n'
        '\tJobStatusClosed JobStatus = "closed"\n'
        '\tJobStatusOther JobStatus = "other"\n'
        ")\n\n"
        "type Job struct {\n"
        '\tStatus JobStatus `json:"status"`\n'
        "}\n"
    )


def test_generate_optional_enum_field() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=False,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type JobStatus string\n\n"
        "const (\n"
        '\tJobStatusOpen JobStatus = "open"\n'
        '\tJobStatusClosed JobStatus = "closed"\n'
        '\tJobStatusOther JobStatus = "other"\n'
        ")\n\n"
        "type Job struct {\n"
        '\tStatus *JobStatus `json:"status,omitempty"`\n'
        "}\n"
    )


def test_generate_enum_with_multiword_field_and_values() -> None:
    objects = [
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="work_model",
                    type="enum",
                    required=True,
                    values=[
                        ("fully_remote", 1),
                        ("on_site", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job_listing.go"] == (
        "package domain\n\n"
        "type JobListingWorkModel string\n\n"
        "const (\n"
        '\tJobListingWorkModelFullyRemote '
        'JobListingWorkModel = "fully_remote"\n'
        '\tJobListingWorkModelOnSite '
        'JobListingWorkModel = "on_site"\n'
        '\tJobListingWorkModelOther '
        'JobListingWorkModel = "other"\n'
        ")\n\n"
        "type JobListing struct {\n"
        '\tWorkModel JobListingWorkModel '
        '`json:"work_model"`\n'
        "}\n"
    )


def test_generate_multiple_enums_in_same_go_file() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=True,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
                make_field(
                    name="work_model",
                    type="enum",
                    required=False,
                    values=[
                        ("remote", 1),
                        ("hybrid", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type JobStatus string\n\n"
        "const (\n"
        '\tJobStatusOpen JobStatus = "open"\n'
        '\tJobStatusClosed JobStatus = "closed"\n'
        '\tJobStatusOther JobStatus = "other"\n'
        ")\n\n"
        "type JobWorkModel string\n\n"
        "const (\n"
        '\tJobWorkModelRemote JobWorkModel = "remote"\n'
        '\tJobWorkModelHybrid JobWorkModel = "hybrid"\n'
        '\tJobWorkModelOther JobWorkModel = "other"\n'
        ")\n\n"
        "type Job struct {\n"
        '\tStatus JobStatus `json:"status"`\n'
        '\tWorkModel *JobWorkModel '
        '`json:"work_model,omitempty"`\n'
        "}\n"
    )


def test_enum_type_names_are_scoped_by_object_name() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=True,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                    ],
                ),
            ],
        ),
        make_object(
            name="Application",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=True,
                    values=[
                        ("pending", 1),
                        ("approved", 2),
                    ],
                ),
            ],
        ),
    ]

    generated_files = GoGenerator().generate(objects)

    assert "type JobStatus string" in generated_files["job.go"]
    assert "type ApplicationStatus string" in (
        generated_files["application.go"]
    )

    assert "type Status string" not in generated_files["job.go"]
    assert "type Status string" not in (
        generated_files["application.go"]
    )


def test_enums_do_not_leak_between_generated_files() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    required=True,
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
                    required=True,
                ),
            ],
        ),
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        "type JobStatus string\n\n"
        "const (\n"
        '\tJobStatusOpen JobStatus = "open"\n'
        '\tJobStatusClosed JobStatus = "closed"\n'
        '\tJobStatusOther JobStatus = "other"\n'
        ")\n\n"
        "type Job struct {\n"
        '\tStatus JobStatus `json:"status"`\n'
        "}\n"
    )

    assert generated_files["company.go"] == (
        "package domain\n\n"
        "type Company struct {\n"
        '\tName string `json:"name"`\n'
        "}\n"
    )

    assert "JobStatus" not in generated_files["company.go"]


def test_generate_enum_alongside_timestamp_and_scalar_fields() -> None:
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
                    name="status",
                    type="enum",
                    required=True,
                    values=[
                        ("open", 1),
                        ("closed", 2),
                        ("other", 3),
                    ],
                ),
                make_field(
                    name="created_at",
                    type="timestamp",
                    required=True,
                ),
            ],
        )
    ]

    generated_files = GoGenerator().generate(objects)

    assert generated_files["job.go"] == (
        "package domain\n\n"
        'import "time"\n\n'
        "type JobStatus string\n\n"
        "const (\n"
        '\tJobStatusOpen JobStatus = "open"\n'
        '\tJobStatusClosed JobStatus = "closed"\n'
        '\tJobStatusOther JobStatus = "other"\n'
        ")\n\n"
        "type Job struct {\n"
        '\tTitle string `json:"title"`\n'
        '\tStatus JobStatus `json:"status"`\n'
        '\tCreatedAt time.Time `json:"created_at"`\n'
        "}\n"
    )


def test_enum_values_preserve_schema_string_values() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="job_type",
                    type="enum",
                    required=True,
                    values=[
                        ("full_time", 1),
                        ("part_time", 2),
                        ("other", 3),
                    ],
                ),
            ],
        )
    ]

    generated = GoGenerator().generate(objects)["job.go"]

    assert (
        'JobJobTypeFullTime JobJobType = "full_time"'
        in generated
    )
    assert (
        'JobJobTypePartTime JobJobType = "part_time"'
        in generated
    )
    assert (
        'JobJobTypeOther JobJobType = "other"'
        in generated
    )