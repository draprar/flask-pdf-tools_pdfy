from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_wtf.recaptcha import RecaptchaField
from wtforms import SubmitField


class JoinPDFsForm(FlaskForm):
    pdf_files = FileField("Upload PDFs")  # For the Join PDFs form
    recaptcha = RecaptchaField()
    submit = SubmitField("Join PDFs")


class SplitPDFForm(FlaskForm):
    pdf_file = FileField("Upload a PDF")  # For the Split PDF form
    recaptcha = RecaptchaField()
    submit = SubmitField("Split PDF")
