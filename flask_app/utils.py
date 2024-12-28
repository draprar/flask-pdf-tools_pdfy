import os
import random
import string
from werkzeug.utils import secure_filename


def generate_captcha_text(length=5):
    """
    Generate a secure random string for CAPTCHA.

    Parameters:
        length (int): Length of the generated CAPTCHA string. Default is 5.

    Returns:
        str: A random string containing uppercase letters and digits.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_captcha_image(text):
    """
    Generate a CAPTCHA image using the PIL-based library.

    Parameters:
        text (str): The CAPTCHA text to be embedded in the image.

    Returns:
        PIL.Image.Image: Generated CAPTCHA image.
    """
    from captcha.image import (
        ImageCaptcha,
    )  # Imported here to minimize dependencies for unused cases

    image_generator = ImageCaptcha(
        width=280, height=90
    )  # Customize image dimensions if needed
    return image_generator.generate_image(text)


def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.

    Parameters:
        filename (str): The name of the file being validated.
        allowed_extensions (set): Set of allowed extensions. Default is {'pdf'}.

    Returns:
        bool: True if the file has a valid extension, False otherwise.
    """
    if not allowed_extensions:
        allowed_extensions = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def cleanup_uploads(upload_folder, cleanup_interval):
    """
    Remove files older than a specified interval from the upload folder.

    Parameters:
        upload_folder (str): Path to the folder containing uploaded files.
        cleanup_interval (float): Time in seconds; files older than this are removed.

    Returns:
        None
    """
    import time

    current_time = time.time()
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if (
            os.path.isfile(file_path)
            and current_time - os.path.getmtime(file_path) > cleanup_interval
        ):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log removal errors but don't crash the application
                print(f"Error removing file {file_path}: {e}")
