from pathlib import Path
from .model import Object, Field, EnumValue
import json
from .errors import (
    TagLockFileNotFoundError,
    TagLockFileParseError,
    TagLockFileReadError,
    TagLockFileWriteError,
    TagLockFileCorruptError
)

class TagLocker: 
    _lock_file_path: Path

    def __init__(self, lock_file_path: Path):
        self._lock_file_path = lock_file_path

    def _check_corrupt_lock_data(
        self,
        lock_data: dict,
    ) -> None:
        if not isinstance(lock_data, dict):
            raise TagLockFileCorruptError(
                "Tag lock file root must be a JSON object"
            )

        for object_name, object_data in lock_data.items():
            if not isinstance(object_name, str) or not object_name.strip():
                raise TagLockFileCorruptError(
                    "Every object name in the tag lock file "
                    "must be a non-empty string"
                )

            if not isinstance(object_data, dict):
                raise TagLockFileCorruptError(
                    f"Lock data for object '{object_name}' "
                    "must be a JSON object"
                )

            # Object-level next tag
            if "next_tag" not in object_data:
                raise TagLockFileCorruptError(
                    f"Lock data for object '{object_name}' "
                    "must contain 'next_tag'"
                )

            next_tag = object_data["next_tag"]

            if type(next_tag) is not int:
                raise TagLockFileCorruptError(
                    f"'next_tag' for object '{object_name}' "
                    "must be an integer"
                )

            if next_tag <= 0:
                raise TagLockFileCorruptError(
                    f"'next_tag' for object '{object_name}' "
                    "must be greater than zero"
                )

            # Object fields
            if "fields" not in object_data:
                raise TagLockFileCorruptError(
                    f"Lock data for object '{object_name}' "
                    "must contain 'fields'"
                )

            fields = object_data["fields"]

            if not isinstance(fields, dict):
                raise TagLockFileCorruptError(
                    f"'fields' for object '{object_name}' "
                    "must be a JSON object"
                )

            active_field_tags: list[int] = []

            for field_name, field_tag in fields.items():
                if not isinstance(field_name, str) or not field_name.strip():
                    raise TagLockFileCorruptError(
                        f"Every field name for object '{object_name}' "
                        "must be a non-empty string"
                    )

                if type(field_tag) is not int:
                    raise TagLockFileCorruptError(
                        f"Tag for field '{field_name}' in object "
                        f"'{object_name}' must be an integer"
                    )

                if field_tag <= 0:
                    raise TagLockFileCorruptError(
                        f"Tag for field '{field_name}' in object "
                        f"'{object_name}' must be greater than zero"
                    )

                active_field_tags.append(field_tag)

            # Retired object field tags
            if "retired_tags" not in object_data:
                raise TagLockFileCorruptError(
                    f"Lock data for object '{object_name}' "
                    "must contain 'retired_tags'"
                )

            retired_field_tags = object_data["retired_tags"]

            if not isinstance(retired_field_tags, list):
                raise TagLockFileCorruptError(
                    f"'retired_tags' for object '{object_name}' "
                    "must be a JSON array"
                )

            for retired_tag in retired_field_tags:
                if type(retired_tag) is not int:
                    raise TagLockFileCorruptError(
                        f"Every retired tag for object '{object_name}' "
                        "must be an integer"
                    )

                if retired_tag <= 0:
                    raise TagLockFileCorruptError(
                        f"Every retired tag for object '{object_name}' "
                        "must be greater than zero"
                    )

            used_field_tags = (
                active_field_tags + retired_field_tags
            )

            if len(used_field_tags) != len(set(used_field_tags)):
                raise TagLockFileCorruptError(
                    f"Duplicate active or retired field tags found "
                    f"for object '{object_name}'"
                )

            if used_field_tags and next_tag <= max(used_field_tags):
                raise TagLockFileCorruptError(
                    f"'next_tag' for object '{object_name}' is "
                    f"{next_tag}, but it must be greater than every "
                    "active and retired field tag"
                )

            # Enum lock data
            if "enums" not in object_data:
                raise TagLockFileCorruptError(
                    f"Lock data for object '{object_name}' "
                    "must contain 'enums'"
                )

            enums = object_data["enums"]

            if not isinstance(enums, dict):
                raise TagLockFileCorruptError(
                    f"'enums' for object '{object_name}' "
                    "must be a JSON object"
                )

            for enum_field_name, enum_data in enums.items():
                if (
                    not isinstance(enum_field_name, str)
                    or not enum_field_name.strip()
                ):
                    raise TagLockFileCorruptError(
                        f"Every enum field name for object "
                        f"'{object_name}' must be a non-empty string"
                    )

                if enum_field_name not in fields:
                    raise TagLockFileCorruptError(
                        f"Enum lock data exists for unknown field "
                        f"'{enum_field_name}' in object '{object_name}'"
                    )

                if not isinstance(enum_data, dict):
                    raise TagLockFileCorruptError(
                        f"Lock data for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must be a JSON object"
                    )

                # Enum next tag
                if "next_tag" not in enum_data:
                    raise TagLockFileCorruptError(
                        f"Lock data for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must contain "
                        "'next_tag'"
                    )

                next_enum_tag = enum_data["next_tag"]

                if type(next_enum_tag) is not int:
                    raise TagLockFileCorruptError(
                        f"'next_tag' for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must be an integer"
                    )

                if next_enum_tag <= 0:
                    raise TagLockFileCorruptError(
                        f"'next_tag' for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must be greater "
                        "than zero"
                    )

                # Active enum values
                if "values" not in enum_data:
                    raise TagLockFileCorruptError(
                        f"Lock data for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must contain "
                        "'values'"
                    )

                enum_values = enum_data["values"]

                if not isinstance(enum_values, dict):
                    raise TagLockFileCorruptError(
                        f"'values' for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must be a JSON object"
                    )

                active_enum_tags: list[int] = []

                for value_name, value_tag in enum_values.items():
                    if (
                        not isinstance(value_name, str)
                        or not value_name.strip()
                    ):
                        raise TagLockFileCorruptError(
                            f"Every enum value name for field "
                            f"'{enum_field_name}' in object "
                            f"'{object_name}' must be a non-empty string"
                        )

                    if type(value_tag) is not int:
                        raise TagLockFileCorruptError(
                            f"Tag for enum value '{value_name}' in "
                            f"field '{enum_field_name}' of object "
                            f"'{object_name}' must be an integer"
                        )

                    if value_tag <= 0:
                        raise TagLockFileCorruptError(
                            f"Tag for enum value '{value_name}' in "
                            f"field '{enum_field_name}' of object "
                            f"'{object_name}' must be greater than zero"
                        )

                    active_enum_tags.append(value_tag)

                # Retired enum tags
                if "retired_tags" not in enum_data:
                    raise TagLockFileCorruptError(
                        f"Lock data for enum field '{enum_field_name}' "
                        f"in object '{object_name}' must contain "
                        "'retired_tags'"
                    )

                retired_enum_tags = enum_data["retired_tags"]

                if not isinstance(retired_enum_tags, list):
                    raise TagLockFileCorruptError(
                        f"'retired_tags' for enum field "
                        f"'{enum_field_name}' in object '{object_name}' "
                        "must be a JSON array"
                    )

                for retired_tag in retired_enum_tags:
                    if type(retired_tag) is not int:
                        raise TagLockFileCorruptError(
                            f"Every retired tag for enum field "
                            f"'{enum_field_name}' in object "
                            f"'{object_name}' must be an integer"
                        )

                    if retired_tag <= 0:
                        raise TagLockFileCorruptError(
                            f"Every retired tag for enum field "
                            f"'{enum_field_name}' in object "
                            f"'{object_name}' must be greater than zero"
                        )

                used_enum_tags = (
                    active_enum_tags + retired_enum_tags
                )

                if len(used_enum_tags) != len(set(used_enum_tags)):
                    raise TagLockFileCorruptError(
                        f"Duplicate active or retired enum tags found "
                        f"for field '{enum_field_name}' in object "
                        f"'{object_name}'"
                    )

                if (
                    used_enum_tags
                    and next_enum_tag <= max(used_enum_tags)
                ):
                    raise TagLockFileCorruptError(
                        f"'next_tag' for enum field "
                        f"'{enum_field_name}' in object "
                        f"'{object_name}' is {next_enum_tag}, but it "
                        "must be greater than every active and retired "
                        "enum tag"
                    )

    def _check_corrupt_lock_file(self, lock_data: dict) -> None:
        self._check_corrupt_lock_data(lock_data)

    def _safe_load_lock_file(self) -> dict: 
        if not self._lock_file_path.exists(): 
            raise TagLockFileNotFoundError(
                f"File not found: {self._lock_file_path}"
            )

        if not self._lock_file_path.is_file(): 
            raise TagLockFileNotFoundError(
                f"File not found: {self._lock_file_path}"
            )

        try: 
            with self._lock_file_path.open(mode='r', encoding="utf-8") as file: 
                json_data = json.load(file)
                self._check_corrupt_lock_file(json_data)

                return json_data

        except OSError as error:
            raise TagLockFileReadError(
                f"Unable to read the file: {self._lock_file_path}"
            ) from error 

        except json.JSONDecodeError as error: 
            raise TagLockFileParseError(
                f"Invalid json syntax: {self._lock_file_path}"
            ) from error 

    def _get_or_create_object_data(
        self, 
        current_object: Object, 
        lock_data: dict
    ) -> dict: 
        if current_object.name not in lock_data: 
            lock_data[current_object.name] = {
                "next_tag": 1, 
                "fields": {}, 
                "retired_tags": [], 
                "enums": {}
            }

        return lock_data[current_object.name]

    def _retire_deleted_fields(
        self,
        current_object: Object,
        object_data: dict,
    ) -> None:
        current_field_names = {
            field.name
            for field in current_object.fields
        }

        locked_fields = object_data["fields"]

        deleted_field_names = [
            field_name
            for field_name in locked_fields
            if field_name not in current_field_names
        ]

        for field_name in deleted_field_names:
            retired_tag = locked_fields.pop(field_name)
            object_data["retired_tags"].append(retired_tag)

            object_data["enums"].pop(field_name, None)

        object_data["retired_tags"].sort()

    def _get_or_create_enum_data(
        self, 
        field: Field, 
        object_data: dict
    ) -> dict : 
        if field.name not in object_data["enums"]: 
            object_data["enums"][field.name] = {
                "next_tag": 1, 
                "values": {}, 
                "retired_tags": []
            }

        return object_data["enums"][field.name]

    def _assign_enum_tags(
        self, 
        field: Field, 
        enum_data: dict
    ) -> None: 
        locked_enum_values = enum_data["values"]

        for value in field.values: 
            if value.name in locked_enum_values: 
                value.tag = enum_data["values"][value.name]
                continue

            assigned_tag = enum_data["next_tag"]
            value.tag = assigned_tag
            enum_data["values"][value.name] = assigned_tag

            enum_data["next_tag"] += 1

    def _retire_enum_tags(
        self, 
        field: Field, 
        enum_data: dict
    ) -> None: 
        current_enum_values = {
            value.name
            for value in field.values
        }

        locked_enum_values = enum_data["values"]

        deleted_enum_values = [
            value 
            for value in locked_enum_values
            if value not in current_enum_values
        ]

        for value in deleted_enum_values: 
            retired_tag = locked_enum_values.pop(value)
            enum_data["retired_tags"].append(retired_tag)

        enum_data["retired_tags"].sort()

    def _process_enum_field(
        self, 
        field: Field, 
        object_data: dict
    ) -> None: 
        enum_data = self._get_or_create_enum_data(field, object_data)
        self._retire_enum_tags(field, enum_data)
        self._assign_enum_tags(field, enum_data)

    def _assign_current_fields(
        self,
        current_object: Object,
        object_data: dict,
    ) -> None:
        locked_fields = object_data["fields"]

        for field in current_object.fields:
            if field.name in locked_fields:
                field.tag = locked_fields[field.name]
            else:
                assigned_tag = object_data["next_tag"]

                locked_fields[field.name] = assigned_tag
                field.tag = assigned_tag

                object_data["next_tag"] += 1

            if field.type == "enum":
                self._process_enum_field(field, object_data)
            else: 
                object_data["enums"].pop(field.name, None)

    def _assign_object_tags(self, current_object: Object, lock_data: dict) -> None:
        entry = self._get_or_create_object_data(current_object, lock_data)
        self._retire_deleted_fields(current_object, entry)
        self._assign_current_fields(current_object, entry)

    def _write_lock_file(
        self, 
        lock_data: dict
    ) -> None: 
        try: 
            with self._lock_file_path.open(mode='w', encoding="utf-8") as file: 
                json.dump(
                    lock_data, 
                    file, 
                    indent=2,
                    sort_keys=True
                )
                file.write("\n")

        except OSError as error: 
            raise TagLockFileWriteError(
                f"Unable to write lock file: {self._lock_file_path}"
            ) from error 

    def assign(self, objects: list[Object]) -> None: 
        lock_data = self._safe_load_lock_file()

        for obj in objects: 
            self._assign_object_tags(obj, lock_data)

        self._write_lock_file(lock_data)

    