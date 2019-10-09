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

class Tags(db.Model):
	__tablename__ = 'tags'
	tid = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(24), primary_key = True)
	projects = relaionship('projects', secondary = 'link')

class Applicants(db.Model):
	__tablename__ = 'applicants'
	email = db.Column(db.String(30), primary_key = True)
	password = db.Column(db.String(20), nullable = False)
	major = db.Column(db.String(20))

class Link(db.Model):
	__tablename__ = 'link'
	tid = db.Column(db.String(24), ForeignKey('tags.name'), primary_key = True)
	pid = db.Column(db.Integer, ForeignKey('projects.pid'), primary_key = True)


class Providers(db.Model):
	__tablename__ = 'providers'
	prov_id = db.Column(db.Integer, primary_key = True)
	email = db.Column(db.String(30), primary_key = True)
	password = db.Column(db.String(20), nullable = False)
	company = db.Column(db.String(40))

class Projects(db.Model):
	__tablename__ = 'projects'
	pid = db.Column(db.Integer, primary_key = True)
	P_name = db.Column(db.String(100), nullable = False)
	description = db.Column(db.String(400), nullable = False)
	provider = relationship("Provider", backref="projects")
	p_tags = relationship('tags', secondary = 'link')


class User(db.Model):
	__tablename__ = 'users'
	user_id   = db.Column(db.Integer,    primary_key = True)
	username  = db.Column(db.String(24), nullable = False)
	email     = db.Column(db.String(80), nullable = False)
	password  = db.Column(db.String(64), nullable = False)
	applicant = db.Column(db.Boolean,    nullable = False)


	def __repr__(self):
		return '<User {}>'.format(self.username)
