from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy()
db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
	# wipeout
	#db.drop_all()
	#db.session.commit()
	#sql = 'CREATE TABLE Users(user_id int, email varchar(20),password varchar(20),provider boolean,admin boolean, CONSTRAINT PK_Applicants PRIMARY KEY(user_id));'
	#User = db.engine.execute(sql)
	#sql = 'CREATE TABLE Tags(tid int,name varchar(24),CONSTRAINT PK_Tags PRIMARY KEY(TID));'
	#Tag = db.engine.execute(sql)
	#sql = 'CREATE TABLE ApplicantsClasses(UID int,class varchar(20),CONSTRAINT PK_AppClass PRIMARY KEY(UID, class),CONSTRAINT FK_AppClass FOREIGN KEY(UID) REFERENCES Users(user_id));'
	#classes = db.engine.execute(sql)
	#sql = 'CREATE TABLE ApplicantsTags(UID int,TID int,CONSTRAINT PK_AppTags PRIMARY KEY (UID, TID),CONSTRAINT FK_AppTags_App FOREIGN KEY(UID) REFERENCES Users(user_id), CONSTRAINT FK_AppTags_Tag FOREIGN KEY(TID) REFERENCES Tags(tid));'
	#AppTags = db.engine.execute(sql)
	#ql = 'CREATE TABLE Projects(pid int,title varchar(100), background varchar(5000), description varchar(5000), contact varchar(80),CONSTRAINT PK_Projects PRIMARY KEY(pid, title), CONSTRAINT FK_Projects FOREIGN KEY(pid) REFERENCES Users(user_id));'
	#projects = db.engine.execute(sql)
	#sql = 'CREATE TABLE ProjectTags(UID int,p_name varchar(20),tid int,CONSTRAINT PK_ProjectTags PRIMARY KEY(UID, p_name, tid),CONSTRAINT FK_ProjectTags_Proj FOREIGN KEY(UID, p_name) REFERENCES Projects(pid, title),CONSTRAINT FK_ProjectTags_Tags FOREIGN KEY(TID) REFERENCES Tags(tid));'
	#ProjectTags = db.engine.execute(sql)
	# add some default data: the 'owner' account and some sample books

	#db.create_all()
	#db.session.add(User(email="owner@app.com", password='pass', provider=True, admin = True))
	#db.session.commit()

	print('Initialized the database.')

#// new!!!!!!!!!!!!!!!!

class Tag(db.Model):
    __tablename__ = 'tags'

    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    users = db.relationship('User', secondary='applicantstags')
    projects = db.relationship('Project', secondary='projecttags', backref = db.backref('p_tags', lazy='dynamic'), lazy ='dynamic')


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    provider = db.Column(db.Boolean)
    admin = db.Column(db.Boolean)


class Applicantsclass(db.Model):
    __tablename__ = 'applicantsclasses'
    uid = db.Column(db.ForeignKey('users.user_id'), primary_key=True, nullable=False)
    _class = db.Column('class', db.String(20), primary_key=True, nullable=False)
    user = db.relationship('User')


t_applicantstags = db.Table(
    'applicantstags', db.metadata,
   	db.Column('uid', db.ForeignKey('users.user_id'), primary_key=True, nullable=False),
    db.Column('tid', db.ForeignKey('tags.tid'), primary_key=True, nullable=False)
)


#result = db.session.execute('SELECT * FROM my_table WHERE my_column = :val', {'val': 5})

class Project(db.Model):
    __tablename__ = 'projects'
    pid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    background = db.Column(db.String(5000))
    description = db.Column(db.String(5000))
    contact = db.Column(db.String(80))
    user = db.Column(db.Integer, db.ForeignKey('users.user_id'))


t_projecttags = db.Table(
    'projecttags', db.metadata,
    db.Column('p_id', db.Integer, db.ForeignKey('projects.pid'), primary_key = True),
    db.Column('tid', db.ForeignKey('tags.tid'), primary_key = True),
)










# // !!!!!!!!!!!!!!!



	#def __repr__(self):
	#	return '<User {}>'.format(self.username)
