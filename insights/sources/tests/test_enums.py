import pytest

from insights.sources.enums import Source


def test_source_members():
    """
    Test that all expected members are present in the Source enum.
    """
    expected_members = {"ROOMS", "AGENTS", "FLOWS", "RUNS", "RESULTS"}
    assert set(member.name for member in Source) == expected_members


@pytest.mark.parametrize(
    "source_name, expected_value",
    [
        ("ROOMS", "rooms"),
        ("AGENTS", "agents"),
        ("FLOWS", "flows"),
        ("RUNS", "runs"),
        ("RESULTS", "results"),
    ],
)
def test_source_values(source_name, expected_value):
    """
    Test that each member of the Source enum has the expected value.
    """
    assert Source[source_name].value == expected_value


def test_source_invalid_member():
    """
    Test that accessing an invalid member raises a ValueError.
    """
    with pytest.raises(ValueError):
        Source.INVALID_MEMBER
