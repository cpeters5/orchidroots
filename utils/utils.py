from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str

# Create your views here.
from PIL import Image, ExifTags

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__proxy__'):
            return force_str(obj)
        return super().default(obj)


def rotate_image(filepath):
  try:
    image = Image.open(filepath)
    for orientation in ExifTags.TAGS.keys():
      if ExifTags.TAGS[orientation] == 'Orientation':
            break
    exif = dict(image._getexif().items())

    if exif[orientation] == 3:
        image = image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image = image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image = image.rotate(90, expand=True)
    image.save(filepath)
    image.close()
  except (AttributeError, KeyError, IndexError):
    # cases: image don't have getexif
    pass