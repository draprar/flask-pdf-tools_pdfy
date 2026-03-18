import os
import logging
from dotenv import load_dotenv
from flask_app.utils import cleanup_uploads

load_dotenv()

# Read configuration from environment variables
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 3600))

if __name__ == "__main__":
    """
    Cleanup script to remove old files from upload folder.
    
    Run manually: python -m flask_app.cleanup
    Or schedule with cron: 0 * * * * cd /path && python -m flask_app.cleanup
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if os.path.exists(UPLOAD_FOLDER):
        try:
            cleanup_uploads(UPLOAD_FOLDER, CLEANUP_INTERVAL)
            logging.info(f"Cleanup completed for folder: {UPLOAD_FOLDER}")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    else:
        logging.warning(f"Upload folder '{UPLOAD_FOLDER}' does not exist.")
