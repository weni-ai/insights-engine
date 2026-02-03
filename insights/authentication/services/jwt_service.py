from uuid import UUID
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings

from insights.authentication.services.exceptions import InvalidTokenError


class JWTService:
    """
    Service to generate JWT tokens for the project
    """

    def generate_jwt_token(
        self, project_uuid: str | UUID, key: str = settings.JWT_SECRET_KEY
    ) -> str:
        payload = {
            "project_uuid": str(project_uuid),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, key, algorithm="RS256")

        return token

    def decode_jwt_token(self, token: str, key: str = settings.JWT_PUBLIC_KEY) -> dict:
        try:
            return jwt.decode(token, key, algorithms=["RS256"])
        except Exception as e:
            raise InvalidTokenError("Error decoding token") from e
