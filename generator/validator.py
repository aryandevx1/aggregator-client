from .model import Object, Field
from .errors import (
    ValidatorError,
    DuplicateObjectError, 
    DuplicateFieldError, 
    KindValidationError, 
    TypeValidationError, 
    RefValidationError, 
    EnumValidationError
)

class Validator:
    _ALLOWED_FIELD_TYPES = frozenset({
        "string",
        "boolean",
        "number",
        "array",
        "timestamp",
        "composite",
        "enum",
        "reference",
    })

    _ALLOWED_OBJECT_KINDS = frozenset({
        "entity",
        "composite",
    })

    def __init__(self) -> None:
        self._objects_by_name: dict[str, Object] = {}

    def _validate_object_names(
        self,
        objects: list[Object],
    ) -> None:
        for obj in objects:
            if obj.name in self._objects_by_name:
                raise DuplicateObjectError(
                    f"Duplicate object found: {obj.name}"
                )

            self._objects_by_name[obj.name] = obj

    def _validate_object_kind(self) -> None:
        for obj in self._objects_by_name.values():
            if obj.kind not in self._ALLOWED_OBJECT_KINDS:
                raise KindValidationError(
                    f"Invalid kind '{obj.kind}' for object '{obj.name}'"
                )

    def _validate_field_names(
        self,
        fields: list[Field],
        object_name: str,
    ) -> None:
        unique_field_names: set[str] = set()

        for field in fields:
            if field.name in unique_field_names:
                raise DuplicateFieldError(
                    f"Duplicate field '{field.name}' "
                    f"in object '{object_name}'"
                )

            unique_field_names.add(field.name)

    def _validate_field_type(
        self, 
        field: Field, 
        object_name: str
    ) -> None:
        if field.type not in self._ALLOWED_FIELD_TYPES:
            raise TypeValidationError(
                f"Invalid type '{field.type}' for field "
                f"'{field.name}' in object '{object_name}'"
            )

    def _validate_field_ref(
        self, 
        field: Field, 
        object_name: str
    ) -> None:
        if field.type in {"composite", "reference"}:
            if field.ref is None:
                raise RefValidationError(
                    f"Field '{field.name}' in object "
                    f"'{object_name}' requires 'ref'"
                )

            if field.ref not in self._objects_by_name:
                raise RefValidationError(
                    f"Field '{field.name}' in object "
                    f"'{object_name}' references unknown object "
                    f"'{field.ref}'"
                )   

            referenced_object = self._objects_by_name[field.ref]
            if field.type == "composite" and referenced_object.kind != "composite":
                raise RefValidationError(
                    f"Composite field '{field.name}' in object '{object_name}' "
                    f"must reference a composite object, but '{field.ref}' "
                    f"has kind '{referenced_object.kind}'"
                )

            if field.type == "reference" and referenced_object.kind != "entity": 
                raise RefValidationError(
                    f"Reference field '{field.name}' in object '{object_name}' "
                    f"must reference an entity object, but '{field.ref}' "
                    f"has kind '{referenced_object.kind}'"
                )
            
        elif field.ref is not None:
            raise RefValidationError(
                f"'ref' is only supported for composite/reference "
                f"fields; found on '{field.name}' in "
                f"object '{object_name}'"
            )

    def _validate_field_enum(
        self, 
        field: Field, 
        object_name: str
    ) -> None:
        if field.values and field.type != "enum":
            raise EnumValidationError(
                f"'values' is only supported for enum fields; "
                f"found on '{field.name}' in object '{object_name}'"
            )

        if field.type == "enum" and not field.values:
            raise EnumValidationError(
                f"Enum field '{field.name}' in object "
                f"'{object_name}' must define values"
            )

        if field.type == "enum" and len(field.values) != len(set(field.values)):
            raise EnumValidationError(
                f"Enum field '{field.name}' in object '{object_name}' "
                f"contains duplicate values"
            )

    def _validate_fields(
        self,
        fields: list[Field],
        object_name: str,
    ) -> None:
        for field in fields:
            self._validate_field_type(field, object_name)
            self._validate_field_ref(field, object_name)
            self._validate_field_enum(field, object_name)


    def _validate_field_list(
        self,
        fields: list[Field],
        object_name: str,
    ) -> None:
        if not fields: 
            raise ValidatorError("Object must contain at least one field")

        self._validate_field_names(fields, object_name)
        self._validate_fields(fields, object_name)

    def _validate_object_list(
        self,
        objects: list[Object],
    ) -> None:
        if not objects: 
            raise ValidatorError("Schema must contain at least one object")
        
        self._validate_object_names(objects)
        self._validate_object_kind()

        for obj in self._objects_by_name.values():
            self._validate_field_list(
                obj.fields,
                obj.name,
            )

    def validate(self, objects: list[Object]) -> None:
        self._objects_by_name.clear()
        self._validate_object_list(objects)