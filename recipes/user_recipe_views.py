from rest_framework import generics, permissions
from .models import UserRecipe
from .serializers import UserRecipeSerializer


class MyRecipeListView(generics.ListAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserRecipe.objects.filter(owner=self.request.user).order_by('-created_at')


class RecipeSubmitView(generics.CreateAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user, telegram_user_id=user.telegram_id)


class MyRecipeDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserRecipe.objects.filter(owner=self.request.user)
