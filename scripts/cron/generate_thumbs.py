import os
import time
import shutil  # For copying files
from PIL import Image
Image.MAX_IMAGE_PIXELS = 933120000
import logging

start_time = time.time()

def generate_thumbnails(base_path):
    images_path = os.path.join(base_path, 'images/')
    thumb_path = os.path.join(base_path, 'thumbs/')
    thumb_size = 300
    i = 0
    j = 0
    flag = False
    for subdir, dirs, files in os.walk(images_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                # Create a path for the original file and the thumbnail
                original_file_path = os.path.join(subdir, file)
                thumb_subdir = subdir.replace(images_path, thumb_path)
                if not os.path.exists(thumb_subdir):
                    os.makedirs(thumb_subdir)
                thumb_file_path = os.path.join(thumb_subdir, file)

                # Check if thumbnail already exists
                if not os.path.exists(thumb_file_path):
                    # Open the image and convert it to a thumbnail
                    try:
                        img = Image.open(original_file_path)
                        try:
                            img.thumbnail((thumb_size, thumb_size))
                            img.save(thumb_file_path, 'JPEG')
                        except:
                            # If file corrupted, use original
                            img.save(thumb_file_path)
                            logging.info(f"Cant create Thumbnail. Use original {original_file_path}")
                        if j%100 == 0:
                            logging.info(f"{j} - Thumbnail created for {original_file_path}")
                        j += 1
                    except IOError:
                        shutil.copy(original_file_path, thumb_file_path)
                        logging.info(f"{i} - Unable to identify {original_file_path}")
                        i += 1
                        if i == 2000:
                            flag = True

                else:
                    # logging.info(f"Thumbnail already exists for {original_file_path}")
                    pass
        if flag:
            break
    return i, j

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Assuming the base directory is the current working directory
i, j = generate_thumbnails('/mnt/static/utils/')
end_time = time.time()
duration = end_time - start_time

print(f"\nCreated {j} thumbnailes. Fail to create {i}. The process took {duration} seconds.")