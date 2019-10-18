from flask_wtf import Form
from wtforms import StringField, SubmitField, validators
from wtforms.validators import Required, DataRequired, InputRequired

class ProjectForm(Form):
    title = StringField("Title:",  validators=[InputRequired(message="You must enter a title")])
    background = StringField("Background:", validators=[InputRequired(message="You must enter background information")])
    description = StringField("Description:", validators=[InputRequired(message="You must enter a description")])
    email = StringField("Contact Email:", validators=[InputRequired(message="You must enter a contact email")])
    submit = SubmitField('Next')
    remove = StringField("Enter project name to remove:")

class TagForm(Form):
    tags = StringField("Tags:", validators=[InputRequired(message="You must enter text into the textbox to add a tag")])
    submit2 = SubmitField('Add tag')
