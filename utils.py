import os
import random
import string
from werkzeug.utils import secure_filename


def generate_captcha_text():
    """Generate a secure random string for CAPTCHA."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def generate_captcha_image(text):
    """Generate a CAPTCHA image using PIL."""
    from captcha.image import ImageCaptcha
    image_generator = ImageCaptcha(width=280, height=90)
    return image_generator.generate_image(text)


def allowed_file(filename, allowed_extensions=None):
    """Check if a file has an allowed extension."""
    if not allowed_extensions:
        allowed_extensions = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def cleanup_uploads(upload_folder, cleanup_interval):
    """Remove files older than the cleanup interval."""
    import time
    current_time = time.time()
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > cleanup_interval:
            os.remove(file_path)
