import os
import tempfile
import time
from flask_app.utils import (
    generate_captcha_text,
    generate_captcha_image,
    allowed_file,
    cleanup_uploads,
)
from PIL import Image


def test_generate_captcha_text():
    """Test the generate_captcha_text function."""
    captcha = generate_captcha_text()
    assert isinstance(captcha, str), "Captcha should be a string"
    assert len(captcha) == 5, "Default CAPTCHA length should be 5"
    assert captcha.isalnum(), "Captcha should only contain alphanumeric characters"

    custom_length = 10
    captcha = generate_captcha_text(length=custom_length)
    assert len(captcha) == custom_length, f"CAPTCHA length should be {custom_length}"


def test_generate_captcha_image():
    """Test the generate_captcha_image function."""
    text = "ABCDE"
    image = generate_captcha_image(text)
    assert isinstance(image, Image.Image), "Output should be a PIL Image"
    assert image.size == (
        280,
        90,
    ), "Image dimensions should match the generator's default size"


def test_allowed_file():
    """Test the allowed_file function."""
    assert allowed_file("document.pdf"), "Valid PDF file should be allowed"
    assert not allowed_file(
        "document.exe"
    ), "Invalid file extension should not be allowed"
    assert not allowed_file("document"), "File without extension should not be allowed"
    assert allowed_file(
        "document.PDF"
    ), "Case-insensitive file extension should be allowed"

    # Custom allowed extensions
    assert allowed_file(
        "image.jpg", allowed_extensions={"jpg", "png"}
    ), "Valid custom extension should be allowed"
    assert not allowed_file(
        "image.pdf", allowed_extensions={"jpg", "png"}
    ), "Invalid custom extension should not be allowed"


def test_cleanup_uploads():
    """Test the cleanup_uploads function."""
    with tempfile.TemporaryDirectory() as upload_folder:
        # Create temporary files
        old_file = tempfile.NamedTemporaryFile(dir=upload_folder, delete=False)
        recent_file = tempfile.NamedTemporaryFile(dir=upload_folder, delete=False)

        try:
            # Close the files to allow deletion on Windows
            old_file.close()
            recent_file.close()

            # Modify file times to simulate old and new files
            old_time = time.time() - 3600  # 1 hour ago
            os.utime(old_file.name, (old_time, old_time))

            cleanup_interval = 1800  # 30 minutes
            cleanup_uploads(upload_folder, cleanup_interval)

            # Assert that old files are deleted and recent ones remain
            assert not os.path.exists(old_file.name), "Old files should be deleted"
            assert os.path.exists(
                recent_file.name
            ), "Recent files should not be deleted"
        finally:
            # Clean up any remaining files
            if os.path.exists(old_file.name):
                os.remove(old_file.name)
            if os.path.exists(recent_file.name):
                os.remove(recent_file.name)
