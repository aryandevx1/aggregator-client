import pytest
from generator.naming import snake_to_pascal, pascal_to_snake

@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Job", "job"),
        ("JobListing", "job_listing"),
        ("SalaryRange", "salary_range"),
        ("UserProfile", "user_profile"),
    ],
)
def test_pascal_to_snake(name, expected):
    assert pascal_to_snake(name) == expected

@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("job", "Job"),
        ("job_listing", "JobListing"),
        ("salary_range", "SalaryRange"),
    ],
)
def test_snake_to_pascal(name, expected):
    assert snake_to_pascal(name) == expected