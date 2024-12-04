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


# Load environment variables from .env file
load_dotenv()

# Flask application configuration
app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')

# Application settings
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder for uploaded files
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Max file size: 10 MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}  # Allowed file extensions
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')
app.config['CLEANUP_INTERVAL'] = 3600  # Cleanup interval in seconds (1 hour)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Form class with reCAPTCHA
class PDFToolForm(FlaskForm):
    recaptcha = RecaptchaField()
    submit = SubmitField("Verify")


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Render the homepage and handle form submission with reCAPTCHA.
    """
    join_form = JoinPDFsForm()
    split_form = SplitPDFForm()
    cleanup_uploads()  # Clean old files

    if join_form.validate_on_submit() and "pdf_files" in request.form:
        flash("CAPTCHA verified successfully for Join PDFs!", "success")
        return redirect(url_for("join_pdfs"))

    if split_form.validate_on_submit() and "pdf_file" in request.form:
        flash("CAPTCHA verified successfully for Split PDF!", "success")
        return redirect(url_for("split_pdf"))

    return render_template("home.html", join_form=join_form, split_form=split_form)


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
    """
    Handle the functionality to merge multiple PDFs into one.
    """
    recaptcha_token = request.form.get('g-recaptcha-response')
    if not recaptcha_token:
        flash("Missing reCAPTCHA token. Please complete the reCAPTCHA.", "error")
        return redirect(url_for("home"))

    if not verify_recaptcha(recaptcha_token):
        flash("Invalid reCAPTCHA. Please try again.", "error")
        return redirect(url_for("home"))  # Stop further processing

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
    """
    Handle the functionality to split a PDF into individual pages.
    """
    recaptcha_token = request.form.get('g-recaptcha-response')
    if not recaptcha_token:
        flash("Missing reCAPTCHA token. Please complete the reCAPTCHA.", "error")
        return redirect(url_for("home"))

    if not verify_recaptcha(recaptcha_token):
        flash("Invalid reCAPTCHA. Please try again.", "error")
        return redirect(url_for("home"))  # Stop further processing

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


def verify_recaptcha(token):
    """
    Verify the reCAPTCHA token with Google's API.
    """
    secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {'secret': secret_key, 'response': token}
    response = requests.post(url, data=payload)
    result = response.json()

    # Debugging information to confirm verification
    print(f"reCAPTCHA verification result: {result}")

    return result.get("success", False)



if __name__ == "__main__":
    app.run(debug=True)
