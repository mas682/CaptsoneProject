from flask_wtf import Form
from wtforms import StringField, SubmitField, validators, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Required, DataRequired, InputRequired, Email
from wtforms.widgets import PasswordInput

class ProjectForm(Form):
    title = StringField("Title:",  validators=[InputRequired(message="You must enter a title")])
    background = TextAreaField("Background:", validators=[InputRequired(message="You must enter background information")])
    description = TextAreaField("Description:", validators=[InputRequired(message="You must enter a description")])
    email = EmailField("Contact Email:", validators=[InputRequired(message="You must enter a contact email"), Email()])
    submit = SubmitField('Next')

class TagForm(Form):
    tags = StringField("Tags:", validators=[InputRequired(message="You must enter text into the textbox to add a tag")])
    submit2 = SubmitField('Add tag')

class ApplicantForm(Form):
    email = StringField('Email')
    password = StringField('Password', widget=PasswordInput(hide_value=False))
    password2 = StringField('Password', widget=PasswordInput(hide_value=False))
    password3 = StringField('Password', widget=PasswordInput(hide_value=False))


class SearchForm(Form):
    class Meta:
        csrf = False

    search=StringField("Seach by tags:", validators=[InputRequired(message="You must enter a tag")])
    index=StringField("")
    type=StringField()
