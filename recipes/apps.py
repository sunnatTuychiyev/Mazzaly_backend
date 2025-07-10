from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recipes"

    def ready(self):
        from modeltranslation.translator import autodiscover
        autodiscover()
        import recipes.signals  # noqa: F401
