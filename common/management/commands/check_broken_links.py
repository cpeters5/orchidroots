from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
import os, sys

# app = sys.argv[2]
# print(app)
SpcImages = apps.get_model('animalia', 'SpcImages')

class Command(BaseCommand):
    help = "Read image_file from SpcImages in an application and print out if the file does not exist in the file system. "

    def handle(self, *args, **options):
        image_list = SpcImages.objects.all().order_by('family')
        i = 0

        for rec in image_list:
            if rec.image_file:
                img_path = os.path.join(settings.STATIC_ROOT, rec.image_dir() + rec.image_file)
                if not os.path.isfile(img_path):
                    i += 1
                    print(i, rec.family, rec.pid_id, rec.id, img_path)
            else:
                i += 1
                print(i, "Image_file does not exist", rec.pid_id, rec.id)