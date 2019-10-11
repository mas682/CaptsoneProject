from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from app import *
from models import db, User, Projects, Tags
from ProjectForm import ProjectForm


#########################################################################################
# Utilities
#########################################################################################

# Given a username, gives
def get_user_id(username):
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None

# This decorator will cause this function to run at the beginning of each request,
# before any of the route functions run. We're using this to check if the user is
# logged in, so that we don't have to do that on every page.
@app.before_request
def before_request():
	# 'g' is a general-purpose global variable thing that Flask gives you.
	# it's a "magic global" like session, request etc. so it's useful
	# for storing globals that you only want to exist for one request.
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()

#########################################################################################
# User account management page routes
#########################################################################################

# This stuff is taken pretty much directly from the "minitwit" example.
# It's pretty standard stuff, so... I'm not gonna make you reimplement it.

@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	if g.user:
		return redirect(url_for('home'))
	error = None
	if request.method == 'POST':
		user = User.query.filter_by(email=request.form['username']).first()
		if user is None:
			error = 'Invalid username'
		elif user.password != request.form['password']:
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user.user_id
			return redirect(url_for('home'))

	return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers the user."""
	if g.user:
		return redirect(url_for('home'))

	error = None
	if request.method == 'POST':
		if not request.form['email'] or '@' not in request.form['email']:
			error = 'You have to enter a valid email address'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['email']) is not None:
			error = 'The username is already taken'
		elif not request.form.get('applicant') and not request.form.get('provider'):
			error = "You did not pick applicant or project proivder"
		else:
			db.session.add(User(
				username = request.form['email'],
				email = request.form['email'],
				password = request.form['password'],
				applicant = True))
			db.session.commit()
			flash('You were successfully registered! Please log in.')
			return redirect(url_for('login'))

	return render_template('register.html', error=error)

@app.route('/logout')
def logout():
	"""Logs the user out."""
	flash('You were logged out. Thanks!')
	session.pop('user_id', None)
	return redirect(url_for('home'))


@app.route('/projects')
def projects():
	return render_template('projects.html')


@app.route('/create_project', methods=['Get', 'Post'])
def create_project():
	form = ProjectForm(request.form)
	if not g.user.provider:
		return redirect(url_for('home'))
	if request.method =='POST':
		if form.validate_on_submit():
			db.session.add(Projects(
				title = form.title.data,
				background = form.background.data,
				description = form.description.data,
				prov_id = g.user.user_id))
			db.session.commit()
			flash(form.title.data)
			return redirect(url_for('home'))
	return render_template('create_project.html', form=form)

@app.route('/myaccount')
def account():
	if not g.user:
		flash("You are not logged in")
		return redirect(url_for('home'))
	else:
		return render_template('my_account.html')
#########################################################################################
# Other page routes
#########################################################################################


# The home page.
@app.route('/', methods=['GET', 'POST'])
def home():
	"""Logs the user in."""
	error = None
	if request.method == 'POST':
		if g.user:
			return redirect(url_for('home'))
		# if the user hits create new account, redirect
		if request.form["submit_button"] == "Create new account":
			return redirect(url_for('register'))
		user = User.query.filter_by(email=request.form['username']).first()
		if user is None:
			error = 'Invalid username'
		elif user.password != request.form['password']:
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user.user_id
			return redirect(url_for('home'))
		return redirect(url_for('home'))
	else:
		if g.user:
			error = "You are logged in"
			# for testing...
			#db.session.add(Tags(name = "Senior"))
			tag = Tags.query.filter_by(name = "Senior").first()
			db.session.commit()
			projects = Projects.query.filter_by(prov_id = g.user.user_id).all()
			for project in projects:
				print(str(project.pid))
				print(str(project.title))
				print(str(project.p_tags.first().name))
			proj = Tags.query.filter_by(name = "Senior").first().projects
			for project in proj:
				print(str(project.title))
			flash(error)
		else:
			error = "You are not logged in"
			flash(error)
		return render_template('home.html')
