import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, session, current_app
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError

from flask_app.forms import JoinPDFsForm, SplitPDFForm
from flask_app.utils import generate_captcha_text, generate_captcha_image, allowed_file

main = Blueprint("main", __name__)

# Configuration constants
MAX_FILES_TO_MERGE = 20
MAX_FILENAME_LENGTH = 100


@main.route("/", methods=["GET"])
def home():
    """Render home page with CAPTCHA challenges."""
    session["join_captcha_text"] = generate_captcha_text()
    session["split_captcha_text"] = generate_captcha_text()

    return render_template(
        "home.html",
        form=JoinPDFsForm(),
        split_form=SplitPDFForm(),
        join_captcha_image=generate_captcha_image(session["join_captcha_text"]),
        split_captcha_image=generate_captcha_image(session["split_captcha_text"]),
    )


@main.route("/join", methods=["POST"])
def join_pdfs():
    """Merge multiple PDF files into a single document."""
    form = JoinPDFsForm()
    if form.validate_on_submit():
        # Verify CAPTCHA
        if form.captcha_answer.data != session.get("join_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("main.home"))

        files = request.files.getlist("pdf_files")
        
        # Validate file count
        if len(files) < 2:
            flash("Upload at least two PDF files.", "error")
            return redirect(url_for("main.home"))
        
        if len(files) > MAX_FILES_TO_MERGE:
            flash(f"Maximum {MAX_FILES_TO_MERGE} files allowed.", "error")
            return redirect(url_for("main.home"))

        # Validate each file
        for file in files:
            if not file or not allowed_file(file.filename):
                flash(f"Invalid file type: {file.filename}", "error")
                return redirect(url_for("main.home"))

        merger = None
        try:
            merger = PdfMerger()
            
            # Merge all files
            for file in files:
                try:
                    merger.append(file)
                except PdfReadError as e:
                    logging.error(
                        f"Invalid PDF file '{file.filename}': {str(e)}",
                        extra={"user_ip": request.remote_addr}
                    )
                    flash(f"Invalid PDF: {file.filename}", "error")
                    return redirect(url_for("main.home"))
                except Exception as e:
                    logging.error(
                        f"Error reading PDF '{file.filename}': {str(e)}",
                        extra={"user_ip": request.remote_addr}
                    )
                    flash(f"Error reading PDF: {file.filename}", "error")
                    return redirect(url_for("main.home"))

            # Generate unique output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_filename = f"merged_{timestamp}_{unique_id}.pdf"
            output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], output_filename)

            # Write merged PDF
            merger.write(output_path)
            
            logging.info(
                f"Successfully merged {len(files)} PDFs: {output_filename}",
                extra={"user_ip": request.remote_addr}
            )
            
            return send_file(output_path, as_attachment=True)
            
        except Exception as e:
            logging.error(
                f"Error merging PDFs: {str(e)}",
                extra={"user_ip": request.remote_addr}
            )
            flash("Failed to merge PDFs.", "error")
            return redirect(url_for("main.home"))
        finally:
            # Ensure merger is closed
            if merger:
                try:
                    merger.close()
                except Exception as e:
                    logging.warning(f"Error closing merger: {str(e)}")

    return redirect(url_for("main.home"))


@main.route("/split", methods=["POST"])
def split_pdf():
    """Split a PDF file into individual pages."""
    form = SplitPDFForm()
    if form.validate_on_submit():
        # Verify CAPTCHA
        if form.captcha_answer.data != session.get("split_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("main.home"))

        file = request.files.get("pdf_file")
        if not file or not allowed_file(file.filename):
            flash("Invalid file type or no file uploaded.", "error")
            return redirect(url_for("main.home"))

        try:
            reader = PdfReader(file)
            
            # Validate PDF has pages
            if not reader.pages:
                flash("PDF has no pages.", "error")
                return redirect(url_for("main.home"))

            # Generate unique session ID for this split operation
            session_id = str(uuid.uuid4())[:12]
            base_name = os.path.splitext(secure_filename(file.filename))[0]
            # Truncate base_name to prevent overly long filenames
            base_name = base_name[:MAX_FILENAME_LENGTH]
            
            output_files = []

            # Split pages
            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    writer = PdfWriter()
                    writer.add_page(page)
                    
                    # Use session ID to ensure uniqueness
                    output_filename = f"{session_id}_{base_name}_page_{page_number}.pdf"
                    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], output_filename)
                    
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_filename)
                    
                except Exception as e:
                    logging.error(
                        f"Error writing page {page_number}: {str(e)}",
                        extra={"user_ip": request.remote_addr}
                    )
                    flash(f"Error splitting page {page_number}.", "error")
                    return redirect(url_for("main.home"))

            logging.info(
                f"Successfully split PDF into {len(output_files)} pages: {file.filename}",
                extra={"user_ip": request.remote_addr}
            )
            
            flash("PDF split successfully.", "success")
            return render_template("download.html", files=output_files)
            
        except PdfReadError as e:
            logging.error(
                f"Invalid PDF file: {str(e)}",
                extra={"user_ip": request.remote_addr}
            )
            flash("The file is not a valid PDF.", "error")
        except Exception as e:
            logging.error(
                f"Error splitting PDF: {str(e)}",
                extra={"user_ip": request.remote_addr}
            )
            flash("Failed to split the PDF.", "error")

    return redirect(url_for("main.home"))


@main.route("/download/<filename>")
def download_file(filename):
    """Safely download a file with path traversal protection."""
    # Security: Prevent path traversal attacks
    if "/" in filename or "\\" in filename or filename.startswith("."):
        logging.warning(
            f"Attempted path traversal in download: {filename}",
            extra={"user_ip": request.remote_addr}
        )
        flash("Invalid filename.", "error")
        return redirect(url_for("main.home"))

    # Prevent directory traversal by using absolute paths
    file_path = os.path.abspath(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])

    # Ensure resolved path is still within upload folder
    if not file_path.startswith(upload_folder):
        logging.warning(
            f"Attempted path traversal (normalized): {filename}",
            extra={"user_ip": request.remote_addr}
        )
        flash("Invalid file path.", "error")
        return redirect(url_for("main.home"))

    # Verify file exists and is a file (not directory)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        logging.info(
            f"File downloaded: {filename}",
            extra={"user_ip": request.remote_addr}
        )
        return send_file(file_path, as_attachment=True)

    logging.warning(
        f"File not found: {filename}",
        extra={"user_ip": request.remote_addr}
    )
    flash("File does not exist.", "error")
    return redirect(url_for("main.home"))