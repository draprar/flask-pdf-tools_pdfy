import flask_app
import pytest
from io import BytesIO
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def client():
    """Pytest fixture to create a test client and setup environment."""
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing forms
    flask_app.secret_key = "test_secret_key"  # Ensure consistent secret key for testing
    flask_app.config["UPLOAD_FOLDER"] = "test_uploads"
    os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["join_captcha_text"] = "ABCDE"
            sess["split_captcha_text"] = "12345"
        yield client
    # Cleanup test files
    for file in os.listdir(flask_app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(flask_app.config["UPLOAD_FOLDER"], file))
    os.rmdir(flask_app.config["UPLOAD_FOLDER"])


def test_home_page(client):
    """Test the home page loads successfully."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"PDF Tools" in response.data


def test_join_pdfs(client):
    """Test joining PDFs."""
    data = {
        "captcha_answer": "ABCDE",
        "pdf_files": [
            (
                BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
                "file1.pdf",
            ),
            (
                BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
                "file2.pdf",
            ),
        ],
    }
    response = client.post("/join", data=data, content_type="multipart/form-data")
    assert (
        response.status_code == 200 or response.status_code == 302
    )  # Ensure valid response


def test_join_pdfs_invalid_captcha(client):
    """Test joining PDFs with invalid CAPTCHA."""
    data = {
        "captcha_answer": "WRONG",  # Wrong CAPTCHA
        "pdf_files": [
            (
                BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
                "file1.pdf",
            ),
            (
                BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
                "file2.pdf",
            ),
        ],
    }
    response = client.post("/join", data=data, content_type="multipart/form-data")
    assert b"Redirecting..." in response.data


def test_join_pdfs_insufficient_files(client):
    """Test joining PDFs with insufficient files."""
    data = {
        "captcha_answer": "ABCDE",
        "pdf_files": [
            (
                BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
                "file1.pdf",
            ),
        ],
    }
    response = client.post("/join", data=data, content_type="multipart/form-data")
    assert b"Redirecting..." in response.data


def test_split_pdf(client):
    """Test splitting a valid PDF."""
    data = {
        "captcha_answer": "12345",
        "pdf_file": (
            BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"),
            "file.pdf",
        ),
    }
    response = client.post("/split", data=data, content_type="multipart/form-data")
    assert response.status_code == 200 or response.status_code == 302


def test_split_pdf_invalid_file(client):
    """Test splitting an invalid PDF."""
    data = {
        "captcha_answer": "12345",
        "pdf_file": (BytesIO(b"Not a PDF"), "file.txt"),
    }
    response = client.post("/split", data=data, content_type="multipart/form-data")
    assert b"Redirecting..." in response.data


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_large_file_upload(client):
    """Test uploading a large file."""
    large_file_content = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n" * 1024 * 1024
    )
    data = {
        "captcha_answer": "ABCDE",
        "pdf_files": [(BytesIO(large_file_content), "large_file.pdf")],
    }
    response = client.post("/join", data=data, content_type="multipart/form-data")
    assert b"Redirecting..." in response.data
