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
	print(str(request.headers))
#########################################################################################
# User account management page routes
#########################################################################################


@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	if g.user:
		return redirect(url_for('home'))
	if 'edit' in session:
		session.pop('edit', None)
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
	if 'edit' in session:
		session.pop('edit', None)

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
				provider = False,
				admin = False))
			db.session.commit()
			flash('You were successfully registered! Please log in.')
			return redirect(url_for('login'))

	return render_template('register.html', error=error)

@app.route('/register_provider', methods=['GET', 'POST'])
def registerProvider():
	"""Registers a project provider."""
	if not g.user.admin:
		return redirect(url_for('home'))
	if 'edit' in session:
		session.pop('edit', None)
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
			flash('New provider successfully registered!')
			return redirect(url_for('home'))

	return render_template('register_provider.html', error=error)

@app.route('/logout')
def logout():
	if 'edit' in session:
		session.pop('edit', None)
	"""Logs the user out."""
	flash('You were logged out. Thanks!')
	session.pop('user_id', None)
	return redirect(url_for('home'))


@app.route('/projects', methods=['GET', 'POST'])
@app.route('/projects/<project_id>', methods=['GET', 'POST'])
#def books(book_id=None):
def projects(project_id = None):
	form2 = ProjectForm(request.form)
	tag_form = TagForm(request.form)
	print(str(request.method))
	if project_id is not None:
		project = Projects.query.filter_by(pid=project_id).first()
		if project is None:
			abort(404)
	if request.method == 'POST' and project_id is not None:
		# this case would be if the provider is updating the project
		list = []
		if 'edit' not in session:
			list = []
		else:
			list = session['edit']
		print(str(request.form))
		print("55. " + str(list))
		if 'edit_title' in request.form:
			if 'edit_title' not in list:
				list.append('edit_title')
			session['edit'] = list
		elif 'update_title' in request.form:
			if 'edit_title' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form)
			else:
				list.remove('edit_title')
				session['edit'] = list
				project.title = form2.title.data
				db.session.commit()
		elif 'edit_background' in request.form:
			if 'edit_background' not in list:
				list.append('edit_background')
			session['edit']=list
		elif 'update_background' in request.form:
			if 'edit_background' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form)
			else:
				list.remove('edit_background')
				session['edit'] = list
				project.background = form2.background.data
				db.session.commit()
		elif 'edit_description' in request.form:
			if 'edit_description' not in list:
				list.append('edit_description')
			session['edit']=list
		elif 'update_description' in request.form:
			if 'edit_description' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form)
			else:
				list.remove('edit_description')
				session['edit'] = list
				project.description = form2.description.data
				db.session.commit()
		elif 'edit_contact' in request.form:
			if 'edit_contact' not in list:
				list.append('edit_contact')
			session['edit']=list
		elif 'update_contact' in request.form:
			if 'edit_contact' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form)
			else:
				list.remove('edit_contact')
				session['edit'] = list
				print(form2.email.data)
				project.contact = form2.email.data
				db.session.commit()
		elif 'edit_tags' in request.form:
			if 'edit_tags' not in list:
				list.append('edit_tags')
			session['edit']=list
			session['tags'] = []
			session['removed_tags'] = []
			for tag in project.p_tags:
				session['tags'].append(tag.name)
			return render_template('project.html', project=project, edit=session['edit'], form=ProjectForm(
					background=project.background, description=project.description, title=project.title),tag_form = tag_form, tags=session['tags'])
		elif 'add_tag' in request.form:
			temp_tags = session['tags']
			if tag_form.tags.data and tag_form.validate_on_submit():
				if tag_form.tags.data not in temp_tags:
					temp_tags.append(tag_form.tags.data)
					session['tags'] = temp_tags
				return render_template('project.html', project=project, edit=session['edit'], form=ProjectForm(
						background=project.background, description=project.description, title=project.title),tag_form = tag_form, tags=temp_tags)
		elif 'submit' in request.form:
			temp_tags = session['tags']
			session['removed_tags'].append(request.form['submit'])
			temp_tags.remove(request.form['submit'])
			session['tags'] = temp_tags
			return render_template('project.html', project=project, edit=session['edit'], form=ProjectForm(
					background=project.background, description=project.description, title=project.title),tag_form = tag_form, tags=temp_tags)
		elif 'update_tags' in request.form:
			# if there are tags in the dict...returns false if empty
			list.remove('edit_tags')
			session['edit'] = list
			temp_tags = session['tags']
			removed_tags = session['removed_tags']
			if temp_tags:
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
			if removed_tags:
				for tag in removed_tags:
					db_tag = Tags.query.filter_by(name=tag).first()
					project.p_tags.remove(db_tag)
					db.session.commit()
		elif 'remove_project' in request.form:
			if 'remove_project' not in list:
				list.append('remove_project')
			session['edit']=list
		elif 'remove_project_final' in request.form:
			if 'remove_project' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form)
			else:
				list.remove('remove_project')
				title = request.form['remove_project_title']
				if title == project.title:
					db.session.delete(project)
					db.session.commit()
					return redirect(url_for('home'))
				else:
					print(str(title) + " does not match the project title")
		return render_template('project.html', project=project, edit=session['edit'], form=ProjectForm(
			background=project.background, description=project.description, title=project.title),tag_form = tag_form)
	elif project_id is None:
		if 'edit' in session:
			session.pop('edit', None)
		# just a error check for now
		# will eventually want to show a list of all projects
		return render_template('projects.html')
	else:
		if 'edit' in session:
			session.pop('edit', None)
		project = Projects.query.filter_by(pid = project_id).first()
		if project is None:
			abort(404)
		else:
			return render_template('project.html', project = project, form=form2, edit=[])


@app.route('/create_project', methods=['Get', 'Post'])
def create_project():
	session.pop('form1', None)
	form = ProjectForm(request.form)
	if not g.user.provider:
		return redirect(url_for('home'))
	if request.method =='POST':
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
