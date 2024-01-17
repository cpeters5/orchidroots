import os
import time
from PIL import Image
Image.MAX_IMAGE_PIXELS = 933120000
import logging

start_time = time.time()

def generate_thumbnails(base_path):
    images_path = os.path.join(base_path, 'images/')
    thumb_path = os.path.join(base_path, 'thumbs/')
    i = 0
    flag = False
    for subdir, dirs, files in os.walk(images_path):
        # print(i, subdir)
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                try:
                    # Create a path for the original file and the thumbnail
                    original_file_path = os.path.join(subdir, file)
                    thumb_subdir = subdir.replace(images_path, thumb_path)
                    if not os.path.exists(thumb_subdir):
                        os.makedirs(thumb_subdir)
                    thumb_file_path = os.path.join(thumb_subdir, file)

                    # Check if thumbnail already exists
                    if not os.path.exists(thumb_file_path):
                        # Open the image and convert it to a thumbnail
                        with Image.open(original_file_path) as img:
                            img.thumbnail((128, 128))
                            img.save(thumb_file_path)
                        logging.info(f"Thumbnail created for {original_file_path}")
                    else:
                        # logging.info(f"Thumbnail already exists for {original_file_path}")
                        continue
                except IOError:
                    i += 1
                    # logging.error(f"{i} - Cannot create thumbnail for {original_file_path}")
        #             if i == 2000:
        #                 flag = True
        # if flag:
        #     break
    return i

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Assuming the base directory is the current working directory
i = generate_thumbnails('/mnt/static/utils/')
end_time = time.time()
duration = end_time - start_time

print(f"Fail to create thumbnails for {i} images. The process took {duration} seconds.")