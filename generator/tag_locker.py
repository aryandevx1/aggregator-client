from pathlib import Path
from .model import Object
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

    def _check_corrupt_object(
        self,
        object_name: str,
        object_data: dict,
    ) -> None:
        active_tags = list(object_data["fields"].values())
        retired_tags = object_data["retired_tags"]
        used_tags = active_tags + retired_tags

        if len(used_tags) != len(set(used_tags)):
            raise TagLockFileCorruptError(
                f"Duplicate tags found for object: {object_name}"
            )

        if not used_tags:
            return

        next_tag = object_data["next_tag"]
        highest_used_tag = max(used_tags)

        if next_tag <= highest_used_tag:
            raise TagLockFileCorruptError(
                f"'next_tag': {next_tag} conflicts with an existing "
                f"or retired tag for object: {object_name}"
            )

    def _check_corrupt_lock_file(self, lock_data: dict) -> None:
        for object_name, object_data in lock_data.items():
            self._check_corrupt_object(
                object_name,
                object_data,
            )

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
                "retired_tags": []
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

        object_data["retired_tags"].sort()

    def _assign_current_fields(
        self,
        current_object: Object,
        object_data: dict,
    ) -> None:
        locked_fields = object_data["fields"]

        for field in current_object.fields:
            if field.name in locked_fields:
                field.tag = locked_fields[field.name]
                continue

            assigned_tag = object_data["next_tag"]

            locked_fields[field.name] = assigned_tag
            field.tag = assigned_tag

            object_data["next_tag"] += 1

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

    