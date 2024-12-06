import os
import time
import secrets
import string
import base64
from datetime import datetime
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO
from captcha.image import ImageCaptcha
from PIL import Image
from forms import JoinPDFsForm, SplitPDFForm
from utils import generate_captcha_text, generate_captcha_image, allowed_file, cleanup_uploads

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')

# Flask Talisman (for security headers like Content-Security-Policy)
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'https://cdn.jsdelivr.net', 'https://kit.fontawesome.com'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:'],
    'font-src': ["'self'", 'https://kit.fontawesome.com', 'https://cdn.jsdelivr.net'],
}
Talisman(app, content_security_policy=csp)

# App Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
app.config['ALLOWED_EXTENSIONS'] = os.getenv('ALLOWED_EXTENSIONS')
app.config['CLEANUP_INTERVAL'] = 3600  # 1 hour

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Template filter for Base64 encoding
@app.template_filter('b64encode')
def b64encode_filter(data):
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    raise ValueError("Input data is not bytes.")


@app.context_processor
def inject_year():
    """Injects the current year into templates."""
    return {'year': datetime.now().year}


@app.route("/", methods=["GET"])
def home():
    if "join_captcha_text" not in session:
        session["join_captcha_text"] = generate_captcha_text()
        session["split_captcha_text"] = generate_captcha_text()

    # Generate CAPTCHA images
    join_captcha_image = generate_captcha_image(session["join_captcha_text"])
    split_captcha_image = generate_captcha_image(session["split_captcha_text"])

    # Convert images to Base64
    join_image_io = BytesIO()
    join_captcha_image.save(join_image_io, "PNG")
    join_image_io.seek(0)

    split_image_io = BytesIO()
    split_captcha_image.save(split_image_io, "PNG")
    split_image_io.seek(0)

    return render_template(
        "home.html",
        form=JoinPDFsForm(),
        split_form=SplitPDFForm(),
        join_captcha_image=join_image_io.read(),
        split_captcha_image=split_image_io.read()
    )



@app.route("/join", methods=["POST"])
def join_pdfs():
    form = JoinPDFsForm()
    if form.validate_on_submit():
        # CAPTCHA validation
        user_input = form.captcha_answer.data
        if user_input != session.get("join_captcha_text"):
            flash("CAPTCHA verification failed for Join PDFs.", "error")
            return redirect(url_for("home"))

        # Handle file upload and merging
        files = request.files.getlist("pdf_files")
        if not files or len(files) < 2:
            flash("Please upload at least two PDF files.", "error")
            return redirect(url_for("home"))

        for file in files:
            if not allowed_file(file.filename):
                flash(f"Invalid file type: {file.filename}", "error")
                return redirect(url_for("home"))

        filenames = [secure_filename(file.filename) for file in files]
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], "merged.pdf")

        try:
            merger = PdfMerger()
            for file in files:
                merger.append(file)
            merger.write(output_path)
            merger.close()
            flash("PDFs merged successfully!", "success")
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            flash(f"Error merging PDFs: {str(e)}", "error")
            return redirect(url_for("home"))

    flash("Form validation failed.", "error")
    return redirect(url_for("home"))


@app.route("/split", methods=["POST"])
def split_pdf():
    form = SplitPDFForm()
    if form.validate_on_submit():
        user_input = form.captcha_answer.data
        if user_input != session.get("split_captcha_text"):
            flash("CAPTCHA verification failed for Split PDF.", "error")
            return redirect(url_for("home"))

        file = request.files.get("pdf_file")
        if not file or not allowed_file(file.filename):
            flash("Please upload a valid PDF file.", "error")
            return redirect(url_for("home"))

        try:
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

            flash("PDF split successfully! Download below.", "success")
            return render_template("download.html", files=split_files)
        except Exception as e:
            flash(f"Error splitting PDF: {str(e)}", "error")
            return redirect(url_for("home"))

    flash("Form validation failed.", "error")
    return redirect(url_for("home"))


@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File does not exist.", "error")
        return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))
