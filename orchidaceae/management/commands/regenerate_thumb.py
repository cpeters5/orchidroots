# Delete thumb image: python manage.py delete_thumb <image id> <type>
# Regnerate thumb: python3 scripts/cron/generate_thumb.py

import os
import shutil
from PIL import Image, ExifTags

Image.MAX_IMAGE_PIXELS = 933120000


from django.core.management.base import BaseCommand, CommandError
from orchidaceae.models import SpcImages, HybImages


def correct_image_orientation(img):
    """Correct image orientation based on EXIF data."""
    try:
        # Get the image's EXIF tags
        exif = dict(img._getexif().items()) if img._getexif() else {}

        # Find the orientation tag
        orientation_key = None
        for key in ExifTags.TAGS.keys():
            if ExifTags.TAGS[key] == 'Orientation':
                orientation_key = key
                break

        if orientation_key and orientation_key in exif:
            orientation = exif[orientation_key]

            # Apply the appropriate transformation
            if orientation == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img = img.transpose(Image.ROTATE_180)
            elif orientation == 4:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
            elif orientation == 6:
                img = img.transpose(Image.ROTATE_270)
            elif orientation == 7:
                img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
            elif orientation == 8:
                img = img.transpose(Image.ROTATE_90)
    except (AttributeError, KeyError, IndexError, TypeError):
        # Cases when there's no EXIF data or other issues
        pass

    return img


class Command(BaseCommand):
    help = "Delete image file for a given ID and type (species or hybrid)"

    def add_arguments(self, parser):
        parser.add_argument("id", type=int, help="ID of the image record")
        parser.add_argument("type", choices=["species", "hybrid"], help="Type of the image (species or hybrid)")


    def handle(self, *args, **options):
        img_id = options["id"]
        img_type = options["type"]
        thumb_size = 300

        Model = SpcImages if img_type == "species" else HybImages

        try:
            obj = Model.objects.get(id=img_id)
        except Model.DoesNotExist:
            raise CommandError(f"No record found for id={img_id} in {img_type} images.")

        image_file = obj.image_file
        if not image_file:
            self.stdout.write(self.style.WARNING("No image_file value found."))
            return

        thumb_file_path = f"/mnt/static/utils/thumbs/{img_type}/{image_file}"
        if os.path.isfile(thumb_file_path):
            os.remove(thumb_file_path)
            self.stdout.write(self.style.SUCCESS(f"Deleted file: {thumb_file_path}"))
        else:
            self.stdout.write(self.style.WARNING(f"File not found: {thumb_file_path}"))

        original_file_path = f"/mnt/static/utils/images/{img_type}/{image_file}"
        try:
            img = Image.open(original_file_path)
            try:
                # Correct orientation before creating thumbnail
                img = correct_image_orientation(img)
                img.thumbnail((thumb_size, thumb_size))
                # Convert to RGB if necessary (handles RGBA images)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                img.save(thumb_file_path, 'JPEG', quality=85)
            except Exception as e:
                # If thumbnail creation fails, use original
                shutil.copy(original_file_path, thumb_file_path)
                print(f"Can't create Thumbnail. Using original {original_file_path}. Error: {str(e)}")
            print(f"Thumbnail created for {original_file_path}")
        except IOError as e:
            shutil.copy(original_file_path, thumb_file_path)
            print(f"Unable to identify {original_file_path}. Error: {str(e)}")

