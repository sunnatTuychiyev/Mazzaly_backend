from __future__ import annotations

from django.core.management.base import BaseCommand

from recipes.importers.spoonacular import SpoonacularImporter


class Command(BaseCommand):
    help = "Import recipes from Spoonacular"

    def add_arguments(self, parser):
        parser.add_argument("--query", required=True, help="Search query")
        parser.add_argument("--max", type=int, default=50)
        parser.add_argument("--update", action="store_true")

    def handle(self, *args, **options):
        importer = SpoonacularImporter(update=options["update"])
        importer.import_all(query=options["query"], max=options["max"])
