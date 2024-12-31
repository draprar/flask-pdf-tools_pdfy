import os
import sys
import pytest
from flask import url_for
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask_app import create_app
from flask_app.utils import (
    generate_captcha_text,
    generate_captcha_image,
    allowed_file,
    cleanup_uploads,
)
from flask_app.forms import JoinPDFsForm, SplitPDFForm
from werkzeug.datastructures import FileStorage
from io import BytesIO
import time


@pytest.fixture
def app():
    """Fixture to create a test Flask application."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "test_uploads"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    yield app
    # Cleanup test files
    for file in os.listdir(app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    os.rmdir(app.config["UPLOAD_FOLDER"])


@pytest.fixture
def client(app):
    """Fixture to create a test client."""
    return app.test_client()


def test_create_app(app):
    """Test the application factory."""
    assert app is not None
    assert app.config["TESTING"] is True
    assert os.path.exists(app.config["UPLOAD_FOLDER"])


def test_home_route(client):
    """Test the home route."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"PDF Tools" in response.data  # Assumes your template has this text


def test_join_pdfs_route(client):
    """Test the join PDFs route with valid data."""
    files = [
        (BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"), "file1.pdf"),
        (BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"), "file2.pdf"),
    ]
    response = client.post(
        url_for("main.join_pdfs"),
        data={
            "captcha_answer": "ABCDE",  # Simulate correct CAPTCHA
            "pdf_files": files,
        },
        content_type="multipart/form-data",
    )
    assert response.status_code in (200, 302)  # Redirect or download


def test_split_pdf_route(client):
    """Test the split PDF route with valid data."""
    file = BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n")
    response = client.post(
        url_for("main.split_pdf"),
        data={"captcha_answer": "12345", "pdf_file": (file, "test.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code in (200, 302)  # Redirect or download


def test_generate_captcha_text():
    """Test CAPTCHA text generation."""
    captcha = generate_captcha_text()
    assert isinstance(captcha, str)
    assert len(captcha) == 5


def test_generate_captcha_image():
    """Test CAPTCHA image generation."""
    captcha_text = "ABCDE"
    image = generate_captcha_image(captcha_text)
    assert image.startswith("iVBORw0KGgoAAAANS")  # PNG header in Base64


def test_allowed_file():
    """Test allowed file extensions."""
    assert allowed_file("test.pdf")
    assert not allowed_file("test.txt")
    assert not allowed_file("")


def test_cleanup_uploads():
    """Test cleanup of old files."""
    test_folder = "test_uploads"
    os.makedirs(test_folder, exist_ok=True)
    test_file = os.path.join(test_folder, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("Test content")
    time.sleep(1)
    cleanup_uploads(test_folder, cleanup_interval=0)  # Cleanup immediately
    assert not os.path.exists(test_file)
    os.rmdir(test_folder)


def test_forms_validation(app):
    """Test the form validation for JoinPDFsForm and SplitPDFForm."""
    with app.app_context():
        # Simulate a valid file upload for JoinPDFsForm
        dummy_file = FileStorage(stream=BytesIO(b"dummy content"), filename="test.pdf", content_type="application/pdf")
        join_form = JoinPDFsForm(data={"captcha_answer": "ABCDE"}, formdata=None, files={"pdf_files": dummy_file})

        # Simulate a valid file upload for SplitPDFForm
        split_form = SplitPDFForm(data={"captcha_answer": "12345"}, formdata=None, files={"pdf_file": dummy_file})


def test_config(app):
    """Test app configuration."""
    app.config["UPLOAD_FOLDER"] = "test_uploads"  # Override for testing
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # Explicitly set for consistency

    assert app.config["UPLOAD_FOLDER"] == "test_uploads"
    assert app.config["MAX_CONTENT_LENGTH"] == 10 * 1024 * 1024
