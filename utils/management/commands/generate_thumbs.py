from django.core.management.base import BaseCommand
import os
from django.conf import settings
from PIL import Image
import logging


class Command(BaseCommand):
    help = "Clears all duplicate emails "

    def handle(self, *args, **options):
        images_path = os.path.join(settings.STATIC_ROOT, 'utils/images')
        thumb_path = os.path.join(settings.STATIC_ROOT, 'utils/thumbs')
        print("image path = ", images_path)
        print("thumb_path = ", thumb_path)
        exit()

        for subdir, dirs, files in os.walk(images_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    try:
                        # Create a path for the original file and the thumbnail
                        original_file_path = os.path.join(subdir, file)
                        thumb_subdir = subdir.replace(images_path, thumb_path)
                        if not os.path.exists(thumb_subdir):
                            os.makedirs(thumb_subdir)
                        thumb_file_path = os.path.join(thumb_subdir, file)

                        # Open the image and convert it to a thumbnail
                        with Image.open(original_file_path) as img:
                            img.thumbnail((128, 128))
                            img.save(thumb_file_path)
                        logging.info(f"Thumbnail created for {original_file_path}")
                    except IOError:
                        logging.error(f"Cannot create thumbnail for {original_file_path}")

        # Setup basic logging
        # logging.basicConfig(level=logging.INFO)

        # Assuming the base directory is the current working directory
        # generate_thumbnails('.')