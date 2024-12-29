from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired


class JoinPDFsForm(FlaskForm):
    pdf_files = FileField("Upload PDFs", validators=[DataRequired()])
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])
    submit = SubmitField("Join PDFs")


class SplitPDFForm(FlaskForm):
    pdf_file = FileField("Upload a PDF", validators=[DataRequired()])
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])
    submit = SubmitField("Split PDF")