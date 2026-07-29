from .test_helpers import make_object, make_field
from pathlib import Path
from generator.tag_locker import TagLocker
from generator.errors import TagLockFileParseError, TagLockFileNotFoundError
import json 

def create_lock_file(
    tmp_path: Path, 
    data: dict | None = None
) -> Path: 
    file_path = tmp_path / ".tags.lock.json"

    file_path.write_text(
        json.dumps(data or {}), 
        encoding="utf-8"
    )

    return file_path

def read_lock_file(
    file_path: Path
) -> dict : 
    return json.loads(
        file_path.read_text(encoding="utf-8")
    )

def test_tags_assignment_to_new_object(tmp_path: Path) -> None:
    file_path = create_lock_file(tmp_path=tmp_path) 

    objects = [
        make_object(
            fields=[
                make_field(name="id"), 
                make_field(name="title"),
                make_field(name="company")
            ]
        )
    ]

    locker = TagLocker(file_path)
    locker.assign(objects=objects)

    assert [field.tag for field in objects[0].fields] == [1, 2, 3]
    lock_data = read_lock_file(file_path=file_path)

    assert lock_data["Job"] == {
        "next_tag": 4,
        "fields": {
            "id": 1, 
            "title": 2, 
            "company": 3,
        }, 
        "retired_tags": []
    }

def test_reuses_existing_tags(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 4,
                "fields": {
                    "id": 1,
                    "title": 2,
                    "company": 3,
                },
                "retired_tags": [],
            }
        },
    )

    # Different YAML order should not change tags.
    obj = make_object(
        fields=[
            make_field("company"),
            make_field("id"),
            make_field("title"),
        ]
    )

    TagLocker(lock_file).assign([obj])

    assert obj.fields[0].tag == 3
    assert obj.fields[1].tag == 1
    assert obj.fields[2].tag == 2

    lock_data = read_lock_file(lock_file)
    assert lock_data["Job"]["next_tag"] == 4

def test_assigns_next_tag_to_new_field(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "title": 2,
                },
                "retired_tags": [],
            }
        },
    )

    obj = make_object(
        fields=[
            make_field("id"),
            make_field("title"),
            make_field("salary"),
        ]
    )

    TagLocker(lock_file).assign([obj])

    salary = next(
        field for field in obj.fields
        if field.name == "salary"
    )

    assert salary.tag == 3

    lock_data = read_lock_file(lock_file)

    assert lock_data["Job"]["fields"]["salary"] == 3
    assert lock_data["Job"]["next_tag"] == 4

def test_retires_deleted_field(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 4,
                "fields": {
                    "id": 1,
                    "title": 2,
                    "company": 3,
                },
                "retired_tags": [],
            }
        },
    )

    obj = make_object(
        fields=[
            make_field("id"),
            make_field("company"),
        ]
    )

    TagLocker(lock_file).assign([obj])

    lock_data = read_lock_file(lock_file)
    job_data = lock_data["Job"]

    assert "title" not in job_data["fields"]
    assert job_data["retired_tags"] == [2]
    assert job_data["next_tag"] == 4

def test_retired_tag_is_not_reused(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 4,
                "fields": {
                    "id": 1,
                    "company": 3,
                },
                "retired_tags": [2],
            }
        },
    )

    obj = make_object(
        fields=[
            make_field("id"),
            make_field("company"),
            make_field("salary"),
        ]
    )

    TagLocker(lock_file).assign([obj])

    salary = next(
        field for field in obj.fields
        if field.name == "salary"
    )

    assert salary.tag == 4

    lock_data = read_lock_file(lock_file)

    assert lock_data["Job"]["next_tag"] == 5
    assert lock_data["Job"]["retired_tags"] == [2]

def test_field_rename_retires_old_tag_and_assigns_new_tag(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "title": 2,
                },
                "retired_tags": [],
            }
        },
    )

    obj = make_object(
        fields=[
            make_field("id"),
            make_field("name"),
        ]
    )

    TagLocker(lock_file).assign([obj])

    lock_data = read_lock_file(lock_file)
    job_data = lock_data["Job"]

    assert "title" not in job_data["fields"]
    assert job_data["fields"]["name"] == 3
    assert job_data["retired_tags"] == [2]
    assert job_data["next_tag"] == 4

def test_objects_have_independent_tag_sequences(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(tmp_path)

    job = make_object(
        name="Job",
        fields=[
            make_field("id"),
            make_field("title"),
        ],
    )

    company = make_object(
        name="Company",
        fields=[
            make_field("id"),
            make_field("name"),
        ],
    )

    TagLocker(lock_file).assign([job, company])

    assert [field.tag for field in job.fields] == [1, 2]
    assert [field.tag for field in company.fields] == [1, 2]

import pytest


def test_missing_lock_file_raises_error(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / ".tags.lock.json"

    with pytest.raises(
        TagLockFileNotFoundError,
        match="File not found",
    ):
        TagLocker(missing_file).assign([])

def test_invalid_json_raises_error(
    tmp_path: Path,
) -> None:
    lock_file = tmp_path / ".tags.lock.json"
    lock_file.write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    with pytest.raises(
        TagLockFileParseError,
        match="Invalid json syntax",
    ):
        TagLocker(lock_file).assign([])