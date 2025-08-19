from rest_framework import generics, permissions
from .models import UserRecipe
from .serializers import UserRecipeSerializer


class MyRecipeListView(generics.ListAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return UserRecipe.objects.none()
        user = self.request.user
        if not user.is_authenticated:
            return UserRecipe.objects.none()
        return UserRecipe.objects.filter(owner=user).order_by("-created_at")


class RecipeSubmitView(generics.CreateAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        telegram_id = None
        try:
            telegram_id = int(user.telegram_id) if user.telegram_id else None
        except (TypeError, ValueError):
            telegram_id = None
        serializer.save(owner=user, telegram_user_id=telegram_id)


class MyRecipeDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return UserRecipe.objects.none()
        user = self.request.user
        if not user.is_authenticated:
            return UserRecipe.objects.none()
        return UserRecipe.objects.filter(owner=user)
