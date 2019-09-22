from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy()
db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
	# wipeout
	db.drop_all()
	db.create_all()

	# add some default data: the 'owner' account and some sample books
	db.session.add(User(username='owner', email="a@b.com", password='pass', applicant=True))

	db.session.commit()

	print('Initialized the database.')


class User(db.Model):
	user_id   = db.Column(db.Integer,    primary_key = True)
	username  = db.Column(db.String(24), nullable = False)
	email     = db.Column(db.String(80), nullable = False)
	password  = db.Column(db.String(64), nullable = False)
	applicant = db.Column(db.Boolean,    nullable = False)


	def __repr__(self):
		return '<User {}>'.format(self.username)
