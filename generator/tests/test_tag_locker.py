from .test_helpers import make_object, make_field
from pathlib import Path
from generator.tag_locker import TagLocker
from generator.errors import TagLockFileParseError, TagLockFileNotFoundError, TagLockFileCorruptError
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
        "retired_tags": [], 
        "enums": {}
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
                "enums": {}
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
                "enums": {}
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
                "enums": {}
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
                "enums": {}
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
                "enums": {}
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

def test_empty_retired_tags_is_not_corrupt(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "title": 2,
                },
                "retired_tags": [],
                "enums": {}
            }
        },
    )

    objects = [
        make_object(
            fields=[
                make_field(name="id"),
                make_field(name="title"),
            ]
        )
    ]

    TagLocker(file_path).assign(objects)

    assert [field.tag for field in objects[0].fields] == [1, 2]

def test_next_tag_conflicting_with_active_tag_raises_error(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "id": 1,
                    "title": 2,
                },
                "retired_tags": [],
                "enums": {}
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="'next_tag' for object 'Job' is 2",
    ):
        TagLocker(file_path).assign([])

def test_next_tag_conflicting_with_retired_tag_raises_error(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "id": 1,
                },
                "retired_tags": [2],
                "enums": {}
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="'next_tag' for object 'Job' is 2",
    ):
        TagLocker(file_path).assign([])

def test_duplicate_active_tags_raise_error(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "title": 1,
                },
                "retired_tags": [],
                "enums": {}
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="Duplicate active or retired field tags found",
    ):
        TagLocker(file_path).assign([])

def test_active_tag_also_present_in_retired_tags_raises_error(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "title": 2,
                },
                "retired_tags": [2],
                "enums": {}
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="Duplicate active or retired field tags found",
    ):
        TagLocker(file_path).assign([])

def test_duplicate_retired_tags_raise_error(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 4,
                "fields": {
                    "id": 1,
                },
                "retired_tags": [2, 2],
                "enums": {}
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="Duplicate active or retired field tags found ",
    ):
        TagLocker(file_path).assign([])

def test_empty_object_entry_is_not_corrupt(
    tmp_path: Path,
) -> None:
    file_path = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 1,
                "fields": {},
                "retired_tags": [],
                "enums": {}
            }
        },
    )

    TagLocker(file_path).assign([])

    lock_data = read_lock_file(file_path)

    assert lock_data["Job"] == {
        "next_tag": 1,
        "fields": {},
        "retired_tags": [],
        "enums": {}
    }

def test_assigns_tags_to_new_enum_values(tmp_path: Path) -> None:
    lock_file = create_lock_file(tmp_path)

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["open", "closed"],
                    tag=1,
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    values = objects[0].fields[0].values

    assert [value.tag for value in values] == [1, 2]

    lock_data = read_lock_file(lock_file)

    assert lock_data["Job"]["enums"]["status"] == {
        "next_tag": 3,
        "values": {
            "open": 1,
            "closed": 2,
        },
        "retired_tags": [],
    }

def test_reuses_existing_enum_tags(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["closed", "open"],
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    values = objects[0].fields[0].values

    assert values[0].name == "closed"
    assert values[0].tag == 2
    assert values[1].name == "open"
    assert values[1].tag == 1

def test_assigns_next_tag_to_new_enum_value(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["open", "closed", "archived"],
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    lock_data = read_lock_file(lock_file)
    enum_data = lock_data["Job"]["enums"]["status"]

    assert enum_data["values"]["archived"] == 3
    assert enum_data["next_tag"] == 4

def test_retires_deleted_enum_value(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["open"],
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    enum_data = read_lock_file(lock_file)["Job"]["enums"]["status"]

    assert enum_data == {
        "next_tag": 3,
        "values": {
            "open": 1,
        },
        "retired_tags": [2],
    }

def test_does_not_reuse_retired_enum_tag(tmp_path: Path) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                        },
                        "retired_tags": [2],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["open", "archived"],
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    enum_data = read_lock_file(lock_file)["Job"]["enums"]["status"]

    assert enum_data["values"]["archived"] == 3
    assert enum_data["next_tag"] == 4
    assert enum_data["retired_tags"] == [2]

def test_enum_fields_have_independent_tag_sequences(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(tmp_path)

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="enum",
                    values=["open", "closed"],
                ),
                make_field(
                    name="work_model",
                    type="enum",
                    values=["remote", "hybrid"],
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    status_values = objects[0].fields[0].values
    work_model_values = objects[0].fields[1].values

    assert [value.tag for value in status_values] == [1, 2]
    assert [value.tag for value in work_model_values] == [1, 2]

def test_deleting_enum_field_removes_enum_lock_data(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 3,
                "fields": {
                    "id": 1,
                    "status": 2,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(name="id"),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    job_data = read_lock_file(lock_file)["Job"]

    assert "status" not in job_data["fields"]
    assert "status" not in job_data["enums"]
    assert job_data["retired_tags"] == [2]

def test_changing_enum_type_removes_enum_lock_data(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    objects = [
        make_object(
            name="Job",
            fields=[
                make_field(
                    name="status",
                    type="string",
                ),
            ],
        )
    ]

    TagLocker(lock_file).assign(objects)

    job_data = read_lock_file(lock_file)["Job"]

    assert job_data["fields"]["status"] == 1
    assert "status" not in job_data["enums"]

def test_missing_enums_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "id": 1,
                },
                "retired_tags": [],
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="must contain 'enums'",
    ):
        TagLocker(lock_file).assign([])

def test_invalid_enums_type_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "id": 1,
                },
                "retired_tags": [],
                "enums": [],
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="'enums'.*must be a JSON object",
    ):
        TagLocker(lock_file).assign([])

def test_enum_data_for_unknown_field_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "id": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 2,
                        "values": {
                            "open": 1,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="unknown field 'status'",
    ):
        TagLocker(lock_file).assign([])

def test_missing_enum_next_tag_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "values": {
                            "open": 1,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="must contain 'next_tag'",
    ):
        TagLocker(lock_file).assign([])

def test_duplicate_active_enum_tags_raise_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                            "closed": 1,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="Duplicate active or retired enum tags",
    ):
        TagLocker(lock_file).assign([])

def test_active_enum_tag_in_retired_tags_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 3,
                        "values": {
                            "open": 1,
                        },
                        "retired_tags": [1],
                    }
                },
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="Duplicate active or retired enum tags",
    ):
        TagLocker(lock_file).assign([])

def test_enum_next_tag_conflict_raises_corrupt_error(
    tmp_path: Path,
) -> None:
    lock_file = create_lock_file(
        tmp_path,
        {
            "Job": {
                "next_tag": 2,
                "fields": {
                    "status": 1,
                },
                "retired_tags": [],
                "enums": {
                    "status": {
                        "next_tag": 2,
                        "values": {
                            "open": 1,
                            "closed": 2,
                        },
                        "retired_tags": [],
                    }
                },
            }
        },
    )

    with pytest.raises(
        TagLockFileCorruptError,
        match="'next_tag'.*must be greater",
    ):
        TagLocker(lock_file).assign([])