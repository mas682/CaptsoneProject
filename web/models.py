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
	db.session.add(User(email="owner@app.com", password='pass', provider=True, admin = True))
#	db.session.add(Providers(prov_id = 1,email='owner@app.com', password='pass'))
	db.session.commit()

	print('Initialized the database.')

class Tags(db.Model):
	__tablename__ = 'tags'
	tid = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(24), unique = True)

class Applicants(db.Model):
	__tablename__ = 'applicants'
	email = db.Column(db.String(30), primary_key = True)
	password = db.Column(db.String(20), nullable = False)
	major = db.Column(db.String(20), nullable = True)

tag_links = db.Table('tag_links',
	db.Column('tag_id', db.Integer, db.ForeignKey('tags.tid')),
	db.Column('proj_id', db.Integer, db.ForeignKey('projects.pid'))
)


#class Providers(db.Model):
#	__tablename__ = 'providers'
#	prov_id = db.Column(db.Integer, primary_key = True)
#	email = db.Column(db.String(30), unique = True)
#	password = db.Column(db.String(20), nullable = False)
#	projects = db.relationship("Projects", backref="provider")

class Projects(db.Model):
	__tablename__ = 'projects'
	pid = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String(100))
	background = db.Column(db.String(400))
	description = db.Column(db.String(400))
	prov_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
	p_tags = db.relationship('Tags', secondary=tag_links,
							 backref=db.backref('projects', lazy='dynamic'),
							 lazy='dynamic')


class User(db.Model):
	__tablename__ = 'users'
	user_id   = db.Column(db.Integer,    primary_key = True)
	email     = db.Column(db.String(80), nullable = False)
	password  = db.Column(db.String(64), nullable = False)
	provider = db.Column(db.Boolean,    nullable = False)
	admin = db.Column(db.Boolean, nullable = False)
	projects = db.relationship("Projects", backref="provider")


	#def __repr__(self):
	#	return '<User {}>'.format(self.username)
