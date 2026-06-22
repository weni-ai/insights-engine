import pytest

from insights.core.accessors import get_nested_attr


class Leaf:
    value = 42


class Branch:
    leaf = Leaf()


class Root:
    branch = Branch()
    name = "root"


class TestGetNestedAttr:
    def test_single_level_attribute(self):
        obj = Root()
        assert get_nested_attr(obj, "name") == "root"

    def test_two_level_nested_attribute(self):
        obj = Root()
        assert get_nested_attr(obj, "branch.leaf") is obj.branch.leaf

    def test_three_level_nested_attribute(self):
        obj = Root()
        assert get_nested_attr(obj, "branch.leaf.value") == 42

    def test_missing_attribute_raises_attribute_error(self):
        obj = Root()
        with pytest.raises(AttributeError):
            get_nested_attr(obj, "nonexistent")

    def test_missing_nested_attribute_raises_attribute_error(self):
        obj = Root()
        with pytest.raises(AttributeError):
            get_nested_attr(obj, "branch.nonexistent")

    def test_missing_attribute_returns_default(self):
        obj = Root()
        assert get_nested_attr(obj, "nonexistent", "fallback") == "fallback"

    def test_missing_nested_attribute_returns_default(self):
        obj = Root()
        assert get_nested_attr(obj, "branch.nonexistent", None) is None

    def test_default_none_is_returned(self):
        obj = Root()
        assert get_nested_attr(obj, "missing", None) is None

    def test_default_false_is_returned(self):
        obj = Root()
        assert get_nested_attr(obj, "missing", False) is False

    def test_deeply_missing_intermediate_returns_default(self):
        obj = Root()
        assert get_nested_attr(obj, "x.y.z", "default") == "default"
