import shutil
import subprocess
from pathlib import Path

import pytest

from generator.generators.go import GoGenerator
from generator.tests.test_helpers import make_field, make_object


def test_generated_go_domain_files_compile(
    tmp_path: Path,
) -> None:
    if shutil.which("go") is None:
        pytest.skip("Go is not installed or not available on PATH")

    domain_dir = tmp_path / "domain"
    domain_dir.mkdir()

    objects = [
        make_object(
            name="Location",
            kind="composite",
            fields=[
                make_field(
                    name="city",
                    type="string",
                    required=True,
                ),
            ],
        ),
        make_object(
            name="JobListing",
            fields=[
                make_field(
                    name="id",
                    type="string",
                    required=True,
                ),
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
                make_field(
                    name="created_at",
                    type="timestamp",
                    required=True,
                ),
                make_field(
                    name="location",
                    type="composite",
                    ref="Location",
                    required=True,
                ),
                make_field(
                    name="company",
                    type="reference",
                    ref="Company",
                    required=True,
                ),
                make_field(
                    name="keywords",
                    type="array",
                    value_type="string",
                    required=False,
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
            ],
        ),
    ]

    generated_files = GoGenerator().generate(objects)

    for filename, content in generated_files.items():
        (domain_dir / filename).write_text(
            content,
            encoding="utf-8",
        )

    (tmp_path / "go.mod").write_text(
        "module example.com/generated\n\ngo 1.23\n",
        encoding="utf-8",
    )

    format_result = subprocess.run(
        [
            "gofmt",
            "-w",
            *[
                str(domain_dir / filename)
                for filename in sorted(generated_files)
            ],
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert format_result.returncode == 0, format_result.stderr

    build_result = subprocess.run(
        ["go", "test", "./..."],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert build_result.returncode == 0, (
        f"Generated Go code failed to compile.\n"
        f"stdout:\n{build_result.stdout}\n"
        f"stderr:\n{build_result.stderr}"
    )