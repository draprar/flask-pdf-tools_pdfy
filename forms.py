from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, IntegerField, StringField
from wtforms.validators import DataRequired, NumberRange


class JoinPDFsForm(FlaskForm):
    pdf_files = FileField("Upload PDFs", validators=[DataRequired()])
    submit = SubmitField("Join PDFs")
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])


class SplitPDFForm(FlaskForm):
    pdf_file = FileField("Upload a PDF", validators=[DataRequired()])
    submit = SubmitField("Split PDF")
    captcha_answer = StringField("Enter CAPTCHA", validators=[DataRequired()])

