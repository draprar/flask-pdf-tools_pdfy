from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired


# Form for joining multiple PDFs
class JoinPDFsForm(FlaskForm):
    """
    Form for uploading multiple PDF files to merge into a single document.
    Includes CAPTCHA for bot protection.
    """

    pdf_files = FileField(
        "Upload PDFs", validators=[DataRequired()]
    )  # Input field for multiple PDF uploads
    submit = SubmitField("Join PDFs")  # Submit button for the form
    captcha_answer = StringField(
        "Enter CAPTCHA", validators=[DataRequired()]
    )  # CAPTCHA verification field


# Form for splitting a single PDF into multiple files
class SplitPDFForm(FlaskForm):
    """
    Form for uploading a single PDF file to split into separate pages.
    Includes CAPTCHA for bot protection.
    """

    pdf_file = FileField(
        "Upload a PDF", validators=[DataRequired()]
    )  # Input field for a single PDF upload
    submit = SubmitField("Split PDF")  # Submit button for the form
    captcha_answer = StringField(
        "Enter CAPTCHA", validators=[DataRequired()]
    )  # CAPTCHA verification field
