import pytest

from generator.model import Object, Field
from generator.validator import Validator
from generator.errors import (
    DuplicateObjectError,
    DuplicateFieldError,
    KindValidationError,
    TypeValidationError,
    RefValidationError,
    EnumValidationError,
    ValueTypeValidationError,
    ValidatorError
)
from .test_helpers import make_field, make_object

def test_valid_schema_passes() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field("title", "string"),
                make_field("salary", "number"),
                make_field(
                    "status",
                    "enum",
                    values=["OPEN", "CLOSED"],
                ),
            ],
        ),
    ]

    Validator().validate(objects)

def test_valid_reference_and_composite_fields_pass() -> None:
    objects = [
        make_object(
            name="Address",
            kind="composite",
            fields=[
                make_field("city", "string"),
            ],
        ),
        make_object(
            name="Company",
            kind="entity",
            fields=[
                make_field()
            ]
        ),
        make_object(
            name="Job",
            kind="entity",
            fields=[
                make_field(
                    name="company",
                    type="reference",
                    ref="Company",
                ),
                make_field(
                    name="location",
                    type="composite",
                    ref="Address",
                ),
            ],
        ),
    ]

    Validator().validate(objects)

def test_duplicate_object_name_raises_error() -> None:
    objects = [
        make_object(name="Job"),
        make_object(name="Job"),
    ]

    with pytest.raises(
        DuplicateObjectError,
        match="Duplicate object found: Job",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "invalid_kind",
    [
        "model",
        "record",
        "",
        "Entity",
    ],
)
def test_invalid_object_kind_raises_error(
    invalid_kind: str,
) -> None:
    objects = [
        make_object(
            name="Job",
            kind=invalid_kind,
        ),
    ]

    with pytest.raises(
        KindValidationError,
        match="Invalid kind",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "valid_kind",
    ["entity", "composite"],
)
def test_valid_object_kinds_pass(
    valid_kind: str,
) -> None:
    objects = [
        make_object(
            name="Example",
            kind=valid_kind,
            fields=[make_field()]
        ),
    ]

    Validator().validate(objects)

def test_duplicate_field_name_raises_error() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field("title", "string"),
                make_field("title", "number"),
            ],
        ),
    ]

    with pytest.raises(
        DuplicateFieldError,
        match="Duplicate field 'title'",
    ):
        Validator().validate(objects)

def test_same_field_name_in_different_objects_passes() -> None:
    objects = [
        make_object(
            name="Job",
            fields=[make_field("name")],
        ),
        make_object(
            name="Company",
            fields=[make_field("name")],
        ),
    ]

    Validator().validate(objects)

@pytest.mark.parametrize(
    "type",
    [
        "string",
        "boolean",
        "number",
        "timestamp",
    ],
)
def test_supported_simple_types_pass(
    type: str,
) -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="value",
                    type=type,
                ),
            ],
        ),
    ]

    Validator().validate(objects)

@pytest.mark.parametrize(
    "invalid_type",
    [
        "integer",
        "float",
        "text",
        "",
        "String",
    ],
)
def test_invalid_type_raises_error(
    invalid_type: str,
) -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="value",
                    type=invalid_type,
                ),
            ],
        ),
    ]

    with pytest.raises(
        TypeValidationError,
        match="Invalid type",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "type",
    ["reference", "composite"],
)
def test_reference_based_field_without_ref_raises_error(
    type: str,
) -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="target",
                    type=type,
                    ref=None,
                ),
            ],
        ),
    ]

    with pytest.raises(
        RefValidationError,
        match="requires 'ref'",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "type",
    ["reference", "composite"],
)
def test_unknown_reference_target_raises_error(
    type: str,
) -> None:
    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="target",
                    type=type,
                    ref="MissingObject",
                ),
            ],
        ),
    ]

    with pytest.raises(
        RefValidationError,
        match="references unknown object",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "type",
    [
        "string",
        "boolean",
        "number",
        "array",
        "timestamp",
        "enum",
    ],
)
def test_ref_on_unsupported_type_raises_error(
    type: str,
) -> None:
    values = ["ACTIVE"] if type == "enum" else []

    objects = [
        make_object(name="Company", fields=[make_field()]),
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="invalid",
                    type=type,
                    ref="Company",
                    values=values,
                ),
            ],
        ),
    ]

    with pytest.raises(
        RefValidationError,
        match="'ref' is only supported",
    ):
        Validator().validate(objects)

def test_object_can_reference_itself() -> None:
    objects = [
        make_object(
            name="Category",
            fields=[
                make_field(
                    name="parent",
                    type="reference",
                    ref="Category",
                ),
            ],
        ),
    ]

    Validator().validate(objects)

def test_valid_enum_field_passes() -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["OPEN", "CLOSED"],
                ),
            ],
        ),
    ]

    Validator().validate(objects)

def test_enum_without_values_raises_error() -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=[],
                ),
            ],
        ),
    ]

    with pytest.raises(
        EnumValidationError,
        match="must define values",
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "type",
    [
        "string",
        "boolean",
        "number",
        "array",
        "timestamp",
        "reference",
        "composite",
    ],
)
def test_values_on_non_enum_field_raises_error(
    type: str,
) -> None:
    referenced_objects = []
    ref = None

    if type == "reference":
        ref = "Target"
        referenced_objects.append(
            make_object(
                name="Target",
                kind="entity",
                fields=[make_field()]
            ),
        )

    elif type == "composite":
        ref = "Target"
        referenced_objects.append(
            make_object(
                name="Target",
                kind="composite",
                fields=[make_field()]
            ),
        )
    objects = referenced_objects + [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="invalid",
                    type=type,
                    ref=ref,
                    values=["A", "B"],
                ),
            ],
        ),
    ]

    with pytest.raises(
        EnumValidationError,
        match="'values' is only supported",
    ):
        Validator().validate(objects)

def test_duplicate_enum_values_raise_error() -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["OPEN", "CLOSED", "OPEN"],
                ),
            ],
        ),
    ]

    with pytest.raises(
        EnumValidationError,
        match="duplicate",
    ):
        Validator().validate(objects)

def test_validator_can_be_reused() -> None:
    validator = Validator()

    validator.validate([
        make_object(name="Job", fields=[make_field()]),
    ])

    validator.validate([
        make_object(name="Company", fields=[make_field()]),
    ])

def test_same_schema_can_be_validated_twice() -> None:
    validator = Validator()

    objects = [
        make_object(name="Job", fields=[make_field()]),
    ]

    validator.validate(objects)
    validator.validate(objects)

def test_empty_object_list() -> None:
    with pytest.raises(
        ValidatorError, 
        match="Schema must contain at least one object"
    ): 
        Validator().validate([])

def test_empty_field_list() -> None: 
    with pytest.raises(
        ValidatorError,
        match="Object must contain at least one field"
    ): 
        Validator().validate([make_object()])

def test_value_type_none_for_field_type_array() -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="status",
                    type="array",
                ),
            ],
        ),
    ]

    with pytest.raises(
        ValueTypeValidationError,
        match=(
            f"Array field 'status' in object "
            f"'Job' must define 'value_type'"
        ),
    ):
        Validator().validate(objects)

@pytest.mark.parametrize(
    "field_type", 
    [
        "string",
        "boolean",
        "number",
        "timestamp",
    ]
)
def test_value_type_string_for_field_type_not_array(field_type: str) -> None:
    objects = [
        make_object(
            fields=[
                make_field(
                    name="status",
                    type=field_type,
                    value_type="string"
                ),
            ],
        ),
    ]

    with pytest.raises(
        ValueTypeValidationError,
        match="'value_type' is only supported for array fields;",
    ):
        Validator().validate(objects)