from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    """Validate an incoming chat message."""

    message = serializers.CharField()

    def validate_message(self, value):
        """Coerce non-string values to a single string."""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value)
        return str(value)


class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ImageResponseSerializer(serializers.Serializer):
    food_name = serializers.CharField()
    calories = serializers.FloatField()
