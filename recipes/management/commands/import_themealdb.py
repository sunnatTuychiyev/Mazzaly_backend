from __future__ import annotations

from django.core.management.base import BaseCommand

from recipes.importers.themealdb import TheMealDBImporter


class Command(BaseCommand):
    help = "Import recipes from TheMealDB"

    def add_arguments(self, parser):
        parser.add_argument("--category", required=True, help="Meal category")
        parser.add_argument("--max", type=int, default=None)
        parser.add_argument("--update", action="store_true")

    def handle(self, *args, **options):
        importer = TheMealDBImporter(update=options["update"])
        importer.import_all(category=options["category"], max=options["max"])
