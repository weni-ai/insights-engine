from django.db.models import TextChoices


class Channel(TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    WHATSAPP = "whatsapp", "WhatsApp"
    TEAMS = "teams", "Teams"
    EMAIL = "email", "Email"
    SHOPPING_ASSISTANT = "shopping_assistant", "Shopping assistant"
    OTHERS = "others", "Others"

    @classmethod
    def urn_case_sql(cls, column: str = "r.urn") -> str:
        return f"""
            CASE
                WHEN {column} LIKE 'instagram:%%' THEN '{cls.INSTAGRAM}'
                WHEN {column} LIKE 'facebook:%%' THEN '{cls.FACEBOOK}'
                WHEN {column} LIKE 'whatsapp:%%' THEN '{cls.WHATSAPP}'
                WHEN {column} LIKE 'teams:%%' THEN '{cls.TEAMS}'
                WHEN {column} LIKE 'msteams:%%' THEN '{cls.TEAMS}'
                WHEN {column} LIKE 'email:%%' THEN '{cls.EMAIL}'
                WHEN {column} LIKE 'mailto:%%' THEN '{cls.EMAIL}'
                WHEN {column} LIKE 'ext:%%' THEN '{cls.SHOPPING_ASSISTANT}'
                WHEN {column} LIKE 'shopping_assistant:%%' THEN '{cls.SHOPPING_ASSISTANT}'
                ELSE '{cls.OTHERS}'
            END
        """
