import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer, ChatImageSerializer
from .services import (
    hf_generate_reply,
    hf_analyze_image,
    suggest_recipes_from_message,
    find_recipe_in_message,
    format_recipe_instructions,
)

logger = logging.getLogger(__name__)


class ChatMessageView(APIView):
    """Handle text messages for the chatbot."""

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        message = serializer.validated_data['message']
        suggested = suggest_recipes_from_message(message)

        recipe = find_recipe_in_message(message)
        if recipe:
            reply_text = format_recipe_instructions(recipe)
            reply = f"Here's how to make {recipe.name}:\n{reply_text}"
        else:
            reply = hf_generate_reply(message)
        return Response({
            'reply': reply,
            'suggested_recipes': suggested,
        })


class ChatImageView(APIView):
    """Handle food images for dish recognition and calorie estimation."""

    def post(self, request):
        serializer = ChatImageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        image = serializer.validated_data['image']
        predicted, kcal = hf_analyze_image(image)
        return Response({
            'predicted_food': predicted,
            'estimated_kcal': kcal,
        })
