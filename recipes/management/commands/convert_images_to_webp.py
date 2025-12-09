"""
Management command to convert existing images to WebP format.
Usage: python manage.py convert_images_to_webp
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from recipes.models import Recipe, RecipeSubmissionImage
from utils.image_utils import convert_to_webp
import os


class Command(BaseCommand):
    help = 'Convert existing recipe images to WebP format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without actually converting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force conversion even if image is already WebP',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Converting existing images to WebP format'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Convert Recipe images
        self.stdout.write(self.style.HTTP_INFO('\n📸 Processing Recipe images...'))
        recipe_count = self.convert_recipe_images(dry_run, force)
        
        # Convert RecipeSubmissionImage images
        self.stdout.write(self.style.HTTP_INFO('\n📸 Processing RecipeSubmission images...'))
        submission_count = self.convert_submission_images(dry_run, force)
        
        # Summary
        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS(f'✓ Recipe images converted: {recipe_count}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Submission images converted: {submission_count}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total images converted: {recipe_count + submission_count}'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('\n💡 Run without --dry-run to actually convert images'))

    def convert_recipe_images(self, dry_run=False, force=False):
        """Convert Recipe model images to WebP."""
        converted = 0
        recipes = Recipe.objects.exclude(image='')
        total = recipes.count()
        
        self.stdout.write(f'Found {total} recipes with images')
        
        for idx, recipe in enumerate(recipes, 1):
            # Skip if already WebP and not forcing
            if recipe.image.name.endswith('.webp') and not force:
                self.stdout.write(
                    self.style.WARNING(f'[{idx}/{total}] ⏭️  Skipped (already WebP): {recipe.name}')
                )
                continue
            
            try:
                if dry_run:
                    self.stdout.write(
                        self.style.NOTICE(f'[{idx}/{total}] 🔍 Would convert: {recipe.name} ({recipe.image.name})')
                    )
                    converted += 1
                else:
                    # Get the original image
                    original_path = recipe.image.path
                    original_name = recipe.image.name
                    
                    # Open and convert
                    with open(original_path, 'rb') as f:
                        webp_image = convert_to_webp(f)
                        
                        if webp_image:
                            # Save the WebP version
                            recipe.image.save(webp_image.name, webp_image, save=False)
                            recipe.save(update_fields=['image'])
                            
                            # Delete old file if it's not WebP
                            if not original_name.endswith('.webp') and os.path.exists(original_path):
                                try:
                                    os.remove(original_path)
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.WARNING(f'  ⚠️  Could not delete old file: {e}')
                                    )
                            
                            converted += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'[{idx}/{total}] ✓ Converted: {recipe.name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'[{idx}/{total}] ✗ Failed: {recipe.name} - Conversion returned None')
                            )
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'[{idx}/{total}] ✗ Failed: {recipe.name} - {str(e)}')
                )
        
        return converted

    def convert_submission_images(self, dry_run=False, force=False):
        """Convert RecipeSubmissionImage model images to WebP."""
        converted = 0
        images = RecipeSubmissionImage.objects.exclude(image='')
        total = images.count()
        
        self.stdout.write(f'Found {total} submission images')
        
        for idx, img_obj in enumerate(images, 1):
            # Skip if already WebP and not forcing
            if img_obj.image.name.endswith('.webp') and not force:
                self.stdout.write(
                    self.style.WARNING(f'[{idx}/{total}] ⏭️  Skipped (already WebP): Submission #{img_obj.submission_id}')
                )
                continue
            
            try:
                if dry_run:
                    self.stdout.write(
                        self.style.NOTICE(f'[{idx}/{total}] 🔍 Would convert: Submission #{img_obj.submission_id} ({img_obj.image.name})')
                    )
                    converted += 1
                else:
                    # Get the original image
                    original_path = img_obj.image.path
                    original_name = img_obj.image.name
                    
                    # Open and convert
                    with open(original_path, 'rb') as f:
                        webp_image = convert_to_webp(f)
                        
                        if webp_image:
                            # Save the WebP version
                            img_obj.image.save(webp_image.name, webp_image, save=False)
                            img_obj.save(update_fields=['image'])
                            
                            # Delete old file if it's not WebP
                            if not original_name.endswith('.webp') and os.path.exists(original_path):
                                try:
                                    os.remove(original_path)
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.WARNING(f'  ⚠️  Could not delete old file: {e}')
                                    )
                            
                            converted += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'[{idx}/{total}] ✓ Converted: Submission #{img_obj.submission_id}')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'[{idx}/{total}] ✗ Failed: Submission #{img_obj.submission_id} - Conversion returned None')
                            )
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'[{idx}/{total}] ✗ Failed: Submission #{img_obj.submission_id} - {str(e)}')
                )
        
        return converted
