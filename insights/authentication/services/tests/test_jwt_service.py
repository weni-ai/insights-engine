import uuid

from django.test import TestCase
from cryptography.hazmat.primitives.asymmetric import rsa

from insights.authentication.services.jwt_service import JWTService


def generate_rsa_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return key


class JWTServiceTests(TestCase):
    def test_generate_jwt_token(self):
        jwt_service = JWTService()
        token = jwt_service.generate_jwt_token(
            project_uuid=uuid.uuid4(), key=generate_rsa_key()
        )
        self.assertIsNotNone(token)
