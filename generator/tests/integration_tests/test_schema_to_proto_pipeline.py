import json
import shutil
import subprocess
from pathlib import Path

import pytest

from generator.id_injector import EntityIdInjector
from generator.loader import Loader
from generator.tag_locker import TagLocker
from generator.validator import Validator
from generator.generators.proto import ProtoGenerator

def _write_schema(
    schema_dir: Path,
    filename: str,
    content: str,
) -> None:
    """
    Write one YAML schema file into the temporary schema directory.
    """

    (schema_dir / filename).write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

def _write_generated_files(
    output_dir: Path,
    generated_files: dict[str, str],
) -> None:
    """
    Write generated proto content to the temporary output directory.
    """

    for filename, content in generated_files.items():
        output_path = output_dir / filename

        output_path.write_text(
            content,
            encoding="utf-8",
        )

def _find_protobuf_include_dir(
    protoc_path: str,
) -> Path | None:
    """
    Try to find the directory containing Google's well-known proto files.

    A normal manual Windows installation commonly has this structure:

        protoc/
        ├── bin/protoc.exe
        └── include/google/protobuf/timestamp.proto
    """

    protoc_file = Path(protoc_path).resolve()

    possible_include_dirs = [
        protoc_file.parent.parent / "include",
        protoc_file.parent / "include",
    ]

    for include_dir in possible_include_dirs:
        timestamp_proto = (
            include_dir
            / "google"
            / "protobuf"
            / "timestamp.proto"
        )

        if timestamp_proto.exists():
            return include_dir

    return None

def _compile_proto_files(
    output_dir: Path,
    generated_files: dict[str, str],
) -> Path:
    """
    Compile all generated .proto files into one descriptor file.

    This verifies syntax, imports, field declarations, enum declarations,
    optional fields and cross-file composite references without requiring
    protoc-gen-go.
    """

    protoc_path = shutil.which("protoc")

    if protoc_path is None:
        pytest.skip("protoc is not installed or is not available on PATH")

    descriptor_path = output_dir / "schema.pb"

    command = [
        protoc_path,
        f"--proto_path={output_dir}",
    ]

    protobuf_include_dir = _find_protobuf_include_dir(protoc_path)

    if protobuf_include_dir is not None:
        command.append(
            f"--proto_path={protobuf_include_dir}"
        )

    command.append(
        f"--descriptor_set_out={descriptor_path}"
    )

    command.extend(
        str(output_dir / filename)
        for filename in sorted(generated_files)
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Generated proto files failed to compile.\n\n"
        f"Command:\n{' '.join(command)}\n\n"
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )

    assert descriptor_path.exists()
    assert descriptor_path.stat().st_size > 0

    return descriptor_path

def _run_pipeline(
    schema_dir: Path,
    lock_file: Path,
) -> tuple[list, dict[str, str]]:
    """
    Run the complete schema-to-proto pipeline.

    The returned objects are already validated, ID-injected and tagged.
    """

    loader = Loader(schema_dir)
    objects = loader.load()

    validator = Validator()
    validator.validate(objects)

    id_injector = EntityIdInjector()
    id_injector.inject(objects)

    tag_locker = TagLocker(lock_file)
    tag_locker.assign(objects)

    proto_generator = ProtoGenerator()
    generated_files = proto_generator.generate(objects)

    return objects, generated_files


def test_schema_to_proto_pipeline_end_to_end(
    tmp_path: Path,
) -> None:
    schema_dir = tmp_path / "objects"
    output_dir = tmp_path / "generated" / "proto"
    lock_file = tmp_path / ".tags.lock.json"

    schema_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    # TagLocker expects the lock file to already exist.
    lock_file.write_text(
        "{}\n",
        encoding="utf-8",
    )

    # Composite object. The ID injector should not add an ID to composites.
    _write_schema(
        schema_dir,
        "location.yaml",
        """
object: Location
kind: composite
fields:
  - name: city
    type: string
    required: true

  - name: country
    type: string
    required: true
""",
    )

    # Entity used as the target of a reference field.
    _write_schema(
        schema_dir,
        "company.yaml",
        """
object: Company
kind: entity
fields:
  - name: name
    type: string
    required: true

  - name: website
    type: string
    required: false
""",
    )

    # Main entity containing every currently supported important field type.
    _write_schema(
        schema_dir,
        "job_listing.yaml",
        """
object: JobListing
kind: entity
fields:
  - name: title
    type: string
    required: true

  - name: active
    type: boolean
    required: true

  - name: score
    type: number
    required: false

  - name: created_at
    type: timestamp
    required: true

  - name: status
    type: enum
    required: true
    values:
      - open
      - closed
      - other

  - name: location
    type: composite
    ref: Location
    required: true

  - name: company
    type: reference
    ref: Company
    required: true

  - name: keywords
    type: array
    value_type: string
    required: false
""",
    )

    # ------------------------------------------------------------------
    # First pipeline run
    # ------------------------------------------------------------------

    first_objects, first_generated_files = _run_pipeline(
        schema_dir=schema_dir,
        lock_file=lock_file,
    )

    assert len(first_objects) == 3

    assert set(first_generated_files) == {
        "company.proto",
        "job_listing.proto",
        "location.proto",
    }

    # Write the generated proto files to disk.
    _write_generated_files(
        output_dir=output_dir,
        generated_files=first_generated_files,
    )

    # ------------------------------------------------------------------
    # Verify the generated composite proto
    # ------------------------------------------------------------------

    location_proto = first_generated_files["location.proto"]

    assert location_proto == (
        'syntax = "proto3";\n\n'
        "message Location {\n"
        "  optional string city = 1;\n"
        "  optional string country = 2;\n"
        "}\n"
    )

    # ------------------------------------------------------------------
    # Verify ID injection and scalar presence for Company
    # ------------------------------------------------------------------

    company_proto = first_generated_files["company.proto"]

    assert "message Company {" in company_proto

    # Entity ID should be injected before user-defined fields.
    assert "  optional string id = 1;" in company_proto
    assert "  optional string name = 2;" in company_proto
    assert "  optional string website = 3;" in company_proto

    # ------------------------------------------------------------------
    # Verify all field categories in JobListing
    # ------------------------------------------------------------------

    job_proto = first_generated_files["job_listing.proto"]

    # ID injection.
    assert "  optional string id = 1;" in job_proto

    # Scalar fields preserve presence using proto optional.
    assert "optional string title" in job_proto
    assert "optional bool active" in job_proto
    assert "optional double score" in job_proto

    # Timestamp is a message and already has presence.
    assert (
        "google.protobuf.Timestamp created_at"
        in job_proto
    )
    assert (
        "optional google.protobuf.Timestamp created_at"
        not in job_proto
    )

    # Enum has a generated UNSPECIFIED zero value and OTHER remains valid.
    assert "enum Status {" in job_proto
    assert "STATUS_UNSPECIFIED = 0;" in job_proto
    assert "STATUS_OPEN = 1;" in job_proto
    assert "STATUS_CLOSED = 2;" in job_proto
    assert "STATUS_OTHER = 3;" in job_proto

    # Enum field itself is not proto optional.
    assert "Status status" in job_proto
    assert "optional Status status" not in job_proto

    # Composite has a cross-file import and no optional keyword.
    assert 'import "location.proto";' in job_proto
    assert "Location location" in job_proto
    assert "optional Location location" not in job_proto

    # Reference is represented as an optional string ID.
    assert "optional string company" in job_proto

    # Arrays use repeated, never optional.
    assert "repeated string keywords" in job_proto
    assert "optional repeated string keywords" not in job_proto

    # Timestamp import should be present exactly once.
    assert (
        job_proto.count(
            'import "google/protobuf/timestamp.proto";'
        )
        == 1
    )

    # ------------------------------------------------------------------
    # Verify lock-file contents
    # ------------------------------------------------------------------

    assert lock_file.exists()

    first_lock_text = lock_file.read_text(
        encoding="utf-8",
    )

    first_lock_data = json.loads(first_lock_text)

    assert set(first_lock_data) == {
        "Company",
        "JobListing",
        "Location",
    }

    location_lock = first_lock_data["Location"]

    assert location_lock["fields"] == {
        "city": 1,
        "country": 2,
    }
    assert location_lock["next_tag"] == 3
    assert location_lock["retired_tags"] == []
    assert location_lock["enums"] == {}

    company_lock = first_lock_data["Company"]

    assert company_lock["fields"] == {
        "id": 1,
        "name": 2,
        "website": 3,
    }
    assert company_lock["next_tag"] == 4
    assert company_lock["retired_tags"] == []
    assert company_lock["enums"] == {}

    job_lock = first_lock_data["JobListing"]

    assert job_lock["fields"] == {
        "id": 1,
        "title": 2,
        "active": 3,
        "score": 4,
        "created_at": 5,
        "status": 6,
        "location": 7,
        "company": 8,
        "keywords": 9,
    }

    assert job_lock["next_tag"] == 10
    assert job_lock["retired_tags"] == []

    assert job_lock["enums"]["status"] == {
        "next_tag": 4,
        "values": {
            "open": 1,
            "closed": 2,
            "other": 3,
        },
        "retired_tags": [],
    }

    # ------------------------------------------------------------------
    # Compile all generated proto files together
    # ------------------------------------------------------------------

    descriptor_path = _compile_proto_files(
        output_dir=output_dir,
        generated_files=first_generated_files,
    )

    assert descriptor_path.exists()

    # ------------------------------------------------------------------
    # Second pipeline run: verify determinism and idempotency
    # ------------------------------------------------------------------

    second_objects, second_generated_files = _run_pipeline(
        schema_dir=schema_dir,
        lock_file=lock_file,
    )

    assert len(second_objects) == 3

    second_lock_text = lock_file.read_text(
        encoding="utf-8",
    )

    # Same schemas and same lock file must produce identical code.
    assert second_generated_files == first_generated_files

    # Running TagLocker again must not assign new tags or rewrite content
    # differently.
    assert second_lock_text == first_lock_text

    # Compile the second output too, proving repeat generation stays valid.
    _write_generated_files(
        output_dir=output_dir,
        generated_files=second_generated_files,
    )

    second_descriptor_path = _compile_proto_files(
        output_dir=output_dir,
        generated_files=second_generated_files,
    )

    assert second_descriptor_path.exists()