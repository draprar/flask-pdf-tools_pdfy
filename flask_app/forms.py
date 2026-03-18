from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, ValidationError


def validate_pdf_files(form, field):
    """Validate that uploaded files are PDFs."""
    if not field.data:
        return
    for file in field.data:
        # Skip validation if file doesn't have filename attribute (e.g., in some test scenarios)
        if not hasattr(file, 'filename'):
            continue
        if file.filename and not file.filename.lower().endswith('.pdf'):
            raise ValidationError(f"Invalid file type: {file.filename}. Only PDF files are allowed.")


def validate_pdf_file(form, field):
    """Validate that a single uploaded file is a PDF."""
    # Skip validation if file doesn't have filename attribute (e.g., in some test scenarios)
    if not field.data or not hasattr(field.data, 'filename'):
        return
    if field.data.filename and not field.data.filename.lower().endswith('.pdf'):
        raise ValidationError(f"Invalid file type: {field.data.filename}. Only PDF files are allowed.")


class JoinPDFsForm(FlaskForm):
    """Form for joining multiple PDF files."""
    pdf_files = FileField("Upload PDFs", validators=[DataRequired(), validate_pdf_files])
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])
    submit = SubmitField("Join PDFs")


class SplitPDFForm(FlaskForm):
    """Form for splitting a PDF file."""
    pdf_file = FileField("Upload a PDF", validators=[DataRequired(), validate_pdf_file])
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])
    submit = SubmitField("Split PDF")