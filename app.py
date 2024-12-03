import os
from flask import Flask, request, render_template, send_file
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/join", methods=["POST"])
def join_pdfs():
    files = request.files.getlist("pdf_files")
    if not files or len(files) < 2:
        return "Please upload at least two PDF files."

    merger = PdfMerger()
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], "merged.pdf")

    for file in files:
        merger.append(file)

    merger.write(output_path)
    merger.close()
    return send_file(output_path, as_attachment=True)


@app.route("/split", methods=["POST"])
def split_pdf():
    file = request.files.get("pdf_file")
    if not file:
        return "Please upload a PDF file."

    reader = PdfReader(file)
    upload_folder = app.config['UPLOAD_FOLDER']
    base_filename = os.path.splitext(file.filename)[0]

    for page_number, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        output_path = os.path.join(upload_folder, f"{base_filename}_page_{page_number}.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

    return f"Splitting complete. Files saved in {upload_folder}."


if __name__ == "__main__":
    app.run(debug=True)
