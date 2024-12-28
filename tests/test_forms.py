import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage, MultiDict, CombinedMultiDict
from flask_app.forms import JoinPDFsForm, SplitPDFForm
import tempfile


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing purposes
    app.secret_key = "test_secret_key"
    return app


def create_temp_pdf():
    """Helper function to create a temporary PDF file."""
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf.write(b"%PDF-1.4\n%Fake PDF Content\n%%EOF")
    temp_pdf.seek(0)
    return temp_pdf


def test_join_pdfs_form_valid(app):
    """Test the JoinPDFsForm with valid data."""
    with app.test_request_context():
        temp_pdf = create_temp_pdf()
        try:
            data = MultiDict({"captcha_answer": "1234"})
            files = MultiDict(
                {
                    "pdf_files": FileStorage(
                        stream=open(temp_pdf.name, "rb"), filename="sample.pdf"
                    )
                }
            )
            form = JoinPDFsForm(formdata=CombinedMultiDict([data, files]))
            assert form.validate(), f"Form errors: {form.errors}"
        finally:
            temp_pdf.close()


def test_split_pdf_form_valid(app):
    """Test the SplitPDFForm with valid data."""
    with app.test_request_context():
        temp_pdf = create_temp_pdf()
        try:
            data = MultiDict({"captcha_answer": "1234"})
            files = MultiDict(
                {
                    "pdf_file": FileStorage(
                        stream=open(temp_pdf.name, "rb"), filename="sample.pdf"
                    )
                }
            )
            form = SplitPDFForm(formdata=CombinedMultiDict([data, files]))
            assert form.validate(), f"Form errors: {form.errors}"
        finally:
            temp_pdf.close()
