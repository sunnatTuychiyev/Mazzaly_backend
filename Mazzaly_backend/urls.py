from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Recipe API",
        default_version='v1',
        description="Cookbook API: Recipes, Ingredients, Meal Plan, Shopping List, Auth (JWT/Google), etc.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="your@email.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('account.urls')),     # Auth, user, Google OAuth va h.k.
    path('api/', include('recipes.urls')),     # Recipes, ingredients, meal plan va h.k.
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('social/', include('social_django.urls', namespace='social')),  # Google Auth
]

# Media uchun:
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
