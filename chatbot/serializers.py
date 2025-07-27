from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ImageResponseSerializer(serializers.Serializer):
    food_name = serializers.CharField()
    calories = serializers.FloatField()
