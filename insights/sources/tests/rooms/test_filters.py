from datetime import datetime, timedelta, timezone

import pytest

from insights.sources.rooms.filters import BasicFilterStrategy


@pytest.fixture
def strategy():
    return BasicFilterStrategy()


def test_eq_operation(strategy):
    clause, params = strategy.apply("field", "eq", 123, "t")
    assert clause == "t.field = (%s)"
    assert params == [123]


def test_in_operation(strategy):
    clause, params = strategy.apply("field", "in", [1, 2, 3], "t")
    assert clause == "t.field IN (%s, %s, %s)"
    assert params == [1, 2, 3]


def test_after_operation(strategy):
    time = datetime.now(timezone.utc) - timedelta(hours=1)
    clause, params = strategy.apply("field", "after", time, "t")
    assert clause == "t.field > (%s)"
    assert params == [time]


def test_before_operation(strategy):
    time = datetime.now(timezone.utc) - timedelta(hours=1)
    clause, params = strategy.apply("field", "before", time, "t")
    assert clause == "t.field < (%s)"
    assert params == [time]


def test_unsupported_operation(strategy):
    with pytest.raises(ValueError):
        strategy.apply("field", "unsupported", 123, "t")
