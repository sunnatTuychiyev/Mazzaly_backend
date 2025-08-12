from __future__ import annotations

from django.core.management.base import BaseCommand

from recipes.importers.chatgpt_json import ChatGPTJSONImporter


class Command(BaseCommand):
    help = "Import recipes from ChatGPT-generated JSON"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to JSON file")
        parser.add_argument("--max", type=int, default=None)
        parser.add_argument("--update", action="store_true")

    def handle(self, *args, **options):
        importer = ChatGPTJSONImporter(update=options["update"])
        importer.import_all(file=options["file"], max=options["max"])
