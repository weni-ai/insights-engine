from rest_framework import serializers

from insights.metrics.meta.choices import (
    WhatsAppMessageTemplatesCategories,
    WhatsAppMessageTemplatesLanguages,
)


class MessageTemplatesQueryParamsSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False, default=10)
    after = serializers.CharField(required=False)
    before = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    category = serializers.ChoiceField(
        choices=WhatsAppMessageTemplatesCategories, required=False
    )
    language = serializers.ChoiceField(
        choices=WhatsAppMessageTemplatesLanguages, required=False
    )

    def validate_limit(self, value):
        max_limit = 20

        if value > max_limit:
            raise serializers.ValidationError(
                f"Limit must be less than {max_limit}", code="limit_too_large"
            )

        return value

    def validate(self, attrs):
        data = super().validate(attrs)

        if "search" in attrs:
            data["name"] = attrs.pop("search")

        return data


class MessageTemplatesCategorySerializer(serializers.Serializer):
    value = serializers.CharField()
    name = serializers.CharField()


class MessageTemplatesCategoriesSerializer(serializers.Serializer):
    categories = MessageTemplatesCategorySerializer(many=True)


class MessageTemplatesLanguageSerializer(serializers.Serializer):
    value = serializers.CharField()
    name = serializers.CharField()


class MessageTemplatesLanguagesSerializer(serializers.Serializer):
    languages = MessageTemplatesLanguageSerializer(many=True)
