import os
import time
import requests
from dotenv import load_dotenv
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.recaptcha import RecaptchaField
from werkzeug.utils import secure_filename
from forms import JoinPDFsForm, SplitPDFForm
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment
from flask import Flask, render_template, request, session, redirect, url_for, flash
import random
import string
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


# Load environment variables from .env file
load_dotenv()

# Flask application configuration
app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')

# Application settings
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder for uploaded files
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Max file size: 10 MB
app.config['ALLOWED_EXTENSIONS'] = os.getenv('ALLOWED_EXTENSIONS')
app.config['CLEANUP_INTERVAL'] = 3600  # Cleanup interval in seconds (1 hour)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.template_filter('b64encode')
def b64encode_filter(data):
    """Encodes binary data to Base64 for embedding in HTML."""
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    raise ValueError("b64encode filter received non-bytes input.")


def generate_captcha_text():
    # Generate a random string of 5 characters
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def generate_captcha_image(text):
    # Create an image with the captcha text
    image = Image.new('RGB', (150, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), text, fill=(0, 0, 0), font=font)
    return image


@app.route("/", methods=["GET", "POST"])
def home():
    # Generate a new CAPTCHA
    captcha_text = generate_captcha_text()
    session["captcha_text"] = captcha_text  # Store it in the session
    captcha_image = generate_captcha_image(captcha_text)

    # Convert the image to bytes and serve it in the template
    image_io = BytesIO()
    captcha_image.save(image_io, "PNG")
    image_io.seek(0)

    return render_template("home.html", captcha_image=image_io.read())



@app.route("/success")
def success():
    return "CAPTCHA verification succeeded!"


def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def cleanup_uploads():
    """
    Remove files older than the cleanup interval from the uploads folder.
    """
    now = time.time()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > app.config['CLEANUP_INTERVAL']:
            os.remove(file_path)


@app.route("/join", methods=["POST"])
def join_pdfs():
    # Validate CAPTCHA
    user_input = request.form.get("captcha_input")
    if user_input != session.get("captcha_text"):
        flash("CAPTCHA verification failed. Try again.", "error")
        return redirect(url_for("home"))

    # Handle PDF joining logic
    files = request.files.getlist("pdf_files")
    if not files or len(files) < 2:
        flash("Please upload at least two PDF files.", "error")
        return redirect(url_for("home"))

    for file in files:
        if not allowed_file(file.filename):
            flash(f"Invalid file type: {file.filename}. Only PDFs are allowed.", "error")
            return redirect(url_for("home"))

    try:
        # Merge PDFs
        merger = PdfMerger()
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], "merged.pdf")
        for file in files:
            merger.append(file)
        merger.write(output_path)
        merger.close()
        flash("PDFs merged successfully!", "success")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f"An error occurred while merging PDFs: {str(e)}", "error")
        return redirect(url_for("home"))



@app.route("/split", methods=["POST"])
def split_pdf():
    # Validate CAPTCHA
    user_input = request.form.get("captcha_input")
    if user_input != session.get("captcha_text"):
        flash("CAPTCHA verification failed. Try again.", "error")
        return redirect(url_for("home"))

    # Handle PDF splitting logic
    file = request.files.get("pdf_file")
    if not file or not allowed_file(file.filename):
        flash("Invalid file. Please upload a valid PDF file.", "error")
        return redirect(url_for("home"))

    try:
        # Split PDF into pages
        reader = PdfReader(file)
        base_filename = os.path.splitext(secure_filename(file.filename))[0]
        split_files = []

        for page_number, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_filename}_page_{page_number}.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            split_files.append(output_path)

        flash("PDF split successfully! Download each page individually below.", "success")
        return render_template("download.html", files=split_files)
    except Exception as e:
        flash(f"An error occurred while splitting the PDF: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/download/<filename>")
def download_file(filename):
    """
    Handle file download requests.
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("The requested file does not exist.", "error")
        return redirect(url_for("home"))


def create_assessment(
    project_id: str, recaptcha_key: str, token: str, recaptcha_action: str
) -> Assessment:
    """Create an assessment to analyze the risk of a UI action.
    Args:
        project_id: Your Google Cloud Project ID.
        recaptcha_key: The reCAPTCHA key associated with the site/app
        token: The generated token obtained from the client.
        recaptcha_action: Action name corresponding to the token.
    """

    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    # Set the properties of the event to be tracked.
    event = recaptchaenterprise_v1.Event()
    event.site_key = recaptcha_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    project_name = f"projects/{project_id}"

    # Build the assessment request.
    request = recaptchaenterprise_v1.CreateAssessmentRequest()
    request.assessment = assessment
    request.parent = project_name

    response = client.create_assessment(request)

    # Check if the token is valid.
    if not response.token_properties.valid:
        print(
            "The CreateAssessment call failed because the token was "
            + "invalid for the following reasons: "
            + str(response.token_properties.invalid_reason)
        )
        return

    # Check if the expected action was executed.
    if response.token_properties.action != recaptcha_action:
        print(
            "The action attribute in your reCAPTCHA tag does"
            + "not match the action you are expecting to score"
        )
        return
    else:
        # Get the risk score and the reason(s).
        # For more information on interpreting the assessment, see:
        # https://cloud.google.com/recaptcha-enterprise/docs/interpret-assessment
        for reason in response.risk_analysis.reasons:
            print(reason)
        print(
            "The reCAPTCHA score for this token is: "
            + str(response.risk_analysis.score)
        )
        # Get the assessment name (id). Use this to annotate the assessment.
        assessment_name = client.parse_assessment_path(response.name).get("assessment")
        print(f"Assessment name: {assessment_name}")
    return response


if __name__ == "__main__":
    app.run(debug=True)
