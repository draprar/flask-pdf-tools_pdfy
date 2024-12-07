import os
import logging
import base64
from datetime import datetime
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO
from forms import JoinPDFsForm, SplitPDFForm
from utils import generate_captcha_text, generate_captcha_image, allowed_file

# Load environment variables from a .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Secret key for session management and CSRF protection
app.secret_key = os.getenv('APP_SECRET_KEY')

# Configure logging for better debugging and monitoring
logging.basicConfig(level=logging.INFO)

# Configure Flask-Talisman for enhanced security headers
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'https://cdn.jsdelivr.net', 'https://kit.fontawesome.com'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:'],
    'font-src': ["'self'", 'https://kit.fontawesome.com', 'https://cdn.jsdelivr.net'],
}
Talisman(app, content_security_policy=csp)

# App-specific configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Max upload size: 10 MB
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Inject the current year into all templates
@app.context_processor
def inject_year():
    """Adds the current year to the context for template rendering."""
    return {'year': datetime.now().year}


# Filter to encode data to base64 for use in templates
@app.template_filter('b64encode')
def b64encode_filter(data):
    """Encodes binary data to a base64 string for template use."""
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    raise ValueError("Input data is not bytes.")


# Render the home page
@app.route("/", methods=["GET"])
def home():
    """Renders the home page with CAPTCHA images and forms."""
    # Generate CAPTCHA for the 'Join PDFs' form
    session["join_captcha_text"] = generate_captcha_text()
    join_captcha_image = generate_captcha_image(session["join_captcha_text"])
    join_image_io = BytesIO()
    join_captcha_image.save(join_image_io, "PNG")

    # Generate CAPTCHA for the 'Split PDF' form
    session["split_captcha_text"] = generate_captcha_text()
    split_captcha_image = generate_captcha_image(session["split_captcha_text"])
    split_image_io = BytesIO()
    split_captcha_image.save(split_image_io, "PNG")

    # Render home.html with the forms and CAPTCHA images
    return render_template(
        "home.html",
        form=JoinPDFsForm(),
        split_form=SplitPDFForm(),
        join_captcha_image=join_image_io.getvalue(),
        split_captcha_image=split_image_io.getvalue(),
    )


def save_file(file, folder):
    """Saves an uploaded file securely and avoids overwriting."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(folder, filename)
    counter = 1
    while os.path.exists(file_path):
        filename = f"{os.path.splitext(filename)[0]}_{counter}.pdf"
        file_path = os.path.join(folder, filename)
        counter += 1
    file.save(file_path)
    return file_path


@app.route("/join", methods=["POST"])
def join_pdfs():
    """Merges multiple PDFs into one."""
    form = JoinPDFsForm()
    if form.validate_on_submit():
        # Validate CAPTCHA
        if form.captcha_answer.data != session.get("join_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("home"))

        # Ensure at least two PDFs are uploaded
        files = request.files.getlist("pdf_files")
        if len(files) < 2:
            flash("Upload at least two PDF files.", "error")
            return redirect(url_for("home"))

        try:
            merger = PdfMerger()
            for file in files:
                if allowed_file(file.filename):
                    merger.append(file)
                else:
                    flash(f"Invalid file type: {file.filename}", "error")
                    return redirect(url_for("home"))

            output_path = os.path.join(app.config['UPLOAD_FOLDER'], "merged.pdf")
            merger.write(output_path)
            merger.close()
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            logging.error(f"Error merging PDFs: {e}")
            flash("Failed to merge PDFs.", "error")
    else:
        flash("Form validation failed.", "error")

    return redirect(url_for("home"))


@app.route("/split", methods=["POST"])
def split_pdf():
    """Splits a single PDF into separate pages."""
    form = SplitPDFForm()
    if form.validate_on_submit():
        if form.captcha_answer.data != session.get("split_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("home"))

        file = request.files.get("pdf_file")
        if file and allowed_file(file.filename):
            try:
                reader = PdfReader(file)
                base_name = os.path.splitext(secure_filename(file.filename))[0]
                output_files = []

                for page_number, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_filename = f"{base_name}_page_{page_number}.pdf"
                    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    output_files.append(output_filename)

                flash("PDF split successfully.", "success")
                return render_template("download.html", files=output_files)
            except Exception as e:
                logging.error(f"Error splitting PDF: {e}")
                flash("Failed to split the PDF.", "error")
        else:
            flash("Invalid file type or no file uploaded.", "error")

    flash("Form validation failed.", "error")
    return redirect(url_for("home"))


@app.route("/download/<filename>")
def download_file(filename):
    """Serves a file for download if it exists."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash("File does not exist.", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
