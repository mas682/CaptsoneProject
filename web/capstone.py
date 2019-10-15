from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from app import *
from models import db, User, Projects, Tags
from ProjectForm import ProjectForm, TagForm


#########################################################################################
# Utilities
#########################################################################################

# Given a username, gives
def get_user_id(username):
	rv = User.query.filter_by(email=username).first()
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
				email = request.form['email'],
				password = request.form['password'],
				provider = True,
				admin = False))
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
	session.pop('form1', None)
	form = ProjectForm(request.form)
	tag_form = TagForm(request.form)
	if not g.user.provider:
		return redirect(url_for('home'))
	if request.method =='POST':
		print(tag_form.validate_on_submit())
		if form.submit.data and form.validate_on_submit():
			print("here1" + str(form.submit.data))
			session['form1'] = {"title":form.title.data,
								"background":form.background.data,
								"description": form.description.data,
								"contact": form.email.data,
								"tags": []}
			session['tags'] = []
			flash(form.title.data)
			return redirect(url_for('create_tags'))
	return render_template('create_project.html', form=form)

@app.route('/create_project/create_tags', methods=['Get', 'Post'])
def create_tags():
	form = TagForm(request.form)
	if not g.user.provider:
		return redirect(url_for('home'))
	if not 'form1' in session:
		return redirect(url_for('home'))
	my_dict = session['form1']
	temp_tags = my_dict['tags']
	if request.method =='POST':
		print("5. " + str(request.form))
		if form.submit2.data and form.validate_on_submit():
			temp_tags.append(form.tags.data)
			session['form1']['tags'] = temp_tags
			flash(form.tags.data)
			return render_template('create_tags.html', form=form, tags=temp_tags)
		elif 'submit' in request.form:
			print("4. " + str(request.form))
			temp_tags.remove(request.form['submit'])
			session['form1']['tags'] = temp_tags
			flash(form.tags.data)
			return render_template('create_tags.html', form=form, tags=temp_tags)
		elif 'submit3' in request.form:
			db.session.add(Projects(
				title = my_dict['title'],
				background = my_dict['background'],
				description = my_dict['description'],
				contact = my_dict['contact'],
				prov_id = g.user.user_id))
			db.session.commit()
		# if there are tags in the dict...returns false if empty
		if temp_tags:
# this line could cause issues if two projects have the same title....
			project = Projects.query.filter_by(title = my_dict['title']).first()
			# get each tag in the dict
			for tag in temp_tags:
				# see if the tag already exists in the database
				tag_list=Tags.query.filter_by(name = tag)
				# if the tag exists, simply associate this project with it
				if tag_list.first():
					if tag == tag_list.first().name:
						print("The tag " + str(tag) + " already existed.")
						temp_tag = tag_list.first()
						project.p_tags.append(temp_tag)
						# otherwise, need to create the tag in the database and
						# add the project to it
					else:
						db.session.add(Tags(name=tag))
						db.session.commit()
						temp_tag=Tags.query.filter_by(name=tag).first()
						project.p_tags.append(temp_tag)
				else:
					db.session.add(Tags(name=tag))
					db.session.commit()
					temp_tag=Tags.query.filter_by(name=tag).first()
					project.p_tags.append(temp_tag)
				db.session.commit()
			# upon adding a project, return to the home page of the user
			return redirect(url_for('home'))
	return render_template('create_tags.html', form=form, tags=temp_tags)

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
			projects = Projects.query.filter_by(prov_id = g.user.user_id).all()
			for project in projects:
				print(str(project.pid))
				print(str(project.title))
				print(str(project.background))
				print(str(project.description))
				for Tag in project.p_tags:
					print("tag: " + str(Tag.name))
			flash(error)
			return render_template('home.html', my_projects=projects)
		else:
			error = "You are not logged in"
			flash(error)
		return render_template('home.html')
