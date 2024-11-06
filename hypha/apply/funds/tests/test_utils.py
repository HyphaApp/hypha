import pytest
from freezegun import freeze_time

from hypha.apply.funds.utils import get_copied_form_name

date = "2024-10-16 15:05:13.721861"

form_name_dataset = [
    ("Test Form", "Test Form (Copied on 2024-10-16 15:05:13.72)"),
    (
        "A Copied Form! (Copied on 2022-09-25 16:30:26.04)",
        "A Copied Form! (Copied on 2024-10-16 15:05:13.72)",
    ),
    (
        "(Copied on 2020-10-30 18:13:26.04) Out of place timestamp",
        "(Copied on 2020-10-30 18:13:26.04) Out of place timestamp (Copied on 2024-10-16 15:05:13.72)",
    ),
]


@freeze_time(date)
@pytest.mark.parametrize("original_name,expected", form_name_dataset)
def test_get_copied_form_name(original_name, expected):
    assert get_copied_form_name(original_name) == expected
