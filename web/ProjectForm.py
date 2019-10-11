from flask_wtf import Form
from wtforms import StringField, SubmitField, validators
from wtforms.validators import Required, DataRequired, InputRequired

class ProjectForm(Form):
    title = StringField("Title:",  validators=[InputRequired(message="You must enter a title")])
    background = StringField("Background:", validators=[InputRequired(message="You must enter background information")])
    description = StringField("Description:", validators=[InputRequired(message="You must enter a description")])
    email = StringField("Contact Email:", validators=[InputRequired(message="You must enter a contact email")])
    tags = StringField("Tags:")
    submit = SubmitField('Submit')
