"""
Test creating user with wrong email format
Test passing blank values on the names
"""

import pytest

from datetime import datetime
from ..domain.entities import User
from ..domain.exceptions import UserValidationException


def test_create_user_with_valid_email():
    # Arrange
    valid_email = "valid@email.com"
    user_id = 1
    first_name = "pericles"
    last_name = "da silva"

    # Act
    user = User(
        user_id,
        valid_email,
        first_name,
        last_name,
    )

    # Assert
    assert user.email == valid_email


def test_create_user_with_invalid_email_raises_error():
    # Arrange
    user_id = 1
    invalid_email = "invalid_email"
    first_name = "pericles"
    last_name = "da silva"

    # Assert (using pytest context manager)
    with pytest.raises(
        UserValidationException,
        match="ERROR: {'field': 'email', 'detail': 'Invalid email, please inform a valid email.'}",
    ):
        User(
            user_id,
            invalid_email,
            first_name,
            last_name,
        )


def test_should_set_created_at():
    # Arrange
    user_id = 1
    valid_email = "valid@email.com"
    first_name = "pericles"
    last_name = "da silva"

    # Act
    user = User(
        user_id,
        valid_email,
        first_name,
        last_name,
    )

    # Assert
    assert user.created_at is not None
    assert type(user.created_at) is datetime
