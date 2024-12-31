import os
import logging
from io import BytesIO
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from flask_app.forms import JoinPDFsForm, SplitPDFForm
from flask_app.utils import generate_captcha_text, generate_captcha_image, allowed_file

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def home():
    session["join_captcha_text"] = generate_captcha_text()
    session["split_captcha_text"] = generate_captcha_text()

    return render_template("home.html",
                           form=JoinPDFsForm(),
                           split_form=SplitPDFForm(),
                           join_captcha_image=generate_captcha_image(session["join_captcha_text"]),
                           split_captcha_image=generate_captcha_image(session["split_captcha_text"]))


@main.route("/join", methods=["POST"])
def join_pdfs():
    form = JoinPDFsForm()
    if form.validate_on_submit():
        if form.captcha_answer.data != session.get("join_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("main.home"))

        files = request.files.getlist("pdf_files")
        if len(files) < 2:
            flash("Upload at least two PDF files.", "error")
            return redirect(url_for("main.home"))

        try:
            merger = PdfMerger()
            for file in files:
                if allowed_file(file.filename):
                    merger.append(file)
                else:
                    flash(f"Invalid file type: {file.filename}", "error")
                    return redirect(url_for("main.home"))

            output_path = os.path.join("uploads", "merged.pdf")
            merger.write(output_path)
            merger.close()
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            logging.error(f"Error merging PDFs: {e}")
            flash("Failed to merge PDFs.", "error")

    return redirect(url_for("main.home"))


@main.route("/split", methods=["POST"])
def split_pdf():
    form = SplitPDFForm()
    if form.validate_on_submit():
        if form.captcha_answer.data != session.get("split_captcha_text"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("main.home"))

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
                    output_path = os.path.join("uploads", output_filename)
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    output_files.append(output_filename)

                flash("PDF split successfully.", "success")
                return render_template("download.html", files=output_files)
            except Exception as e:
                logging.error(f"Error splitting PDF: {e}")
                flash("Failed to split the PDF.", "error")

        flash("Invalid file type or no file uploaded.", "error")
    return redirect(url_for("main.home"))


@main.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash("File does not exist.", "error")
    return redirect(url_for("main.home"))