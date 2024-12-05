from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange


class JoinPDFsForm(FlaskForm):
    pdf_files = FileField("Upload PDFs")  # For the Join PDFs form
    submit = SubmitField("Join PDFs")
    captcha_answer = IntegerField("What is 5 + 3?", validators=[DataRequired(), NumberRange(min=8, max=8)])


class SplitPDFForm(FlaskForm):
    pdf_file = FileField("Upload a PDF")  # For the Split PDF form
    submit = SubmitField("Split PDF")
    captcha_answer = IntegerField("What is 5 + 3?", validators=[DataRequired(), NumberRange(min=8, max=8)])
