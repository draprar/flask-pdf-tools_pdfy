import os
from flask_app.utils import cleanup_uploads

UPLOAD_FOLDER = "uploads"  # Update as needed
CLEANUP_INTERVAL = 3600  # Remove files older than 1 hour

if __name__ == "__main__":
    if os.path.exists(UPLOAD_FOLDER):
        cleanup_uploads(UPLOAD_FOLDER, CLEANUP_INTERVAL)
    else:
        print(f"Upload folder '{UPLOAD_FOLDER}' does not exist.")
