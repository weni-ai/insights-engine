_sentinel = object()


def get_nested_attr(obj, attr, default=_sentinel):
    """
    Get a nested attribute from an object.

    Args:
        obj: The object to get the attribute from.
        attr: The attribute to get.
        default: The default value to return if the attribute is not found.

    Returns:
        The value of the attribute.
    """
    try:
        for part in attr.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        if default is _sentinel:
            raise
        return default
