import os
import random
import string
from werkzeug.utils import secure_filename
from captcha.image import ImageCaptcha


def generate_captcha_text(length=5):
    """Generate a secure random string for CAPTCHA."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_captcha_image(text):
    """Generate a CAPTCHA image using the PIL-based library."""
    image_generator = ImageCaptcha(width=280, height=90)
    return image_generator.generate_image(text)


def allowed_file(filename, allowed_extensions=None):
    """Check if a file has an allowed extension."""
    if not allowed_extensions:
        allowed_extensions = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def cleanup_uploads(upload_folder, cleanup_interval):
    """Remove files older than a specified interval from the upload folder."""
    import time
    current_time = time.time()
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > cleanup_interval:
            try:
                os.remove(file_path)
            except OSError as e:
                logging.error(f"Error removing file {file_path}: {e}")