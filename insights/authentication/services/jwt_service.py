from uuid import UUID
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


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
