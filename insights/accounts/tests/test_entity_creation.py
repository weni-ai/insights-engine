"""
Test creating user with wrong email format
Test passing blank values on the names
"""

import pytest

from ..entities import User
from ..exceptions import UserValidationException


def test_create_user_with_valid_email():
    # Arrange
    valid_email = "valid@email.com"
    uuid = "uuid1"
    first_name = "pericles"
    last_name = "da silva"
    created_at = "11111"
    updated_at = "11111"

    # Act
    user = User(uuid, valid_email, first_name, last_name, created_at, updated_at)

    # Assert
    assert user.email == valid_email


def test_create_user_with_invalid_email_raises_error():
    # Arrange
    invalid_email = "invalid_email"
    uuid = "uuid2"
    first_name = "pericles"
    last_name = "da silva"
    created_at = "11111"
    updated_at = "11111"

    # Assert (using pytest context manager)
    with pytest.raises(
        UserValidationException,
        match="ERROR: {'field': 'email', 'detail': 'Invalid email, please inform an valid email.'}",
    ):
        User(uuid, invalid_email, first_name, last_name, created_at, updated_at)
