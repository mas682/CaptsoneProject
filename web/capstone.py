from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from sqlalchemy.exc import IntegrityError
from app import *
from models import db, Tag, User, Project, Applicantsclass, t_projecttags
from ProjectForm import ProjectForm, TagForm, SearchForm


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
		if not request.form['email'] or not request.form['email'].endswith("@pitt.edu"):
			error = 'You have to enter a valid email address that belongs to the pitt.edu domain'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif not request.form.get('applicant') and not request.form.get('provider'):
			error = "You did not pick applicant or project proivder"
		else:
			try:
				db.session.add(User(
					email = request.form['email'],
					password = request.form['password'],
					provider = False,
					admin = False))
				db.session.commit()
			# error check if this email is already associated with some account
# need to make it so that error occurs like project form errors
			except IntegrityError:
				db.session.rollback()
				error = 'The username is already taken'
				return render_template('register.html', error=error)
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
		elif not request.form.get('applicant') and not request.form.get('provider'):
			error = "You did not pick applicant or project proivder"
		else:
			try:
				db.session.add(User(
					email = request.form['email'],
					password = request.form['password'],
					provider = True,
					admin = False))
				db.session.commit()
			except IntegrityError:
				db.session.rollback()
				error = 'The username is already taken'
				return render_template('register_provider.html', error=error)
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
	print(str(request.method))
	project = None
	if project_id is not None:
		project = Project.query.filter_by(pid=project_id).first()
		if project is None:
			abort(404)
	if request.method == 'POST' and project_id is not None:
		form2 = ProjectForm(request.form, background=project.background, description=project.description,
					email=project.contact, title=project.title)
		tag_form = TagForm(request.form)
		project_removal_error = False
		# this case would be if the provider is updating the project
		list = []
		if 'edit' not in session:
			list = []
		else:
			list = session['edit']
		print(str(request.form))
		if 'edit_title' in request.form:
			if 'edit_title' not in list:
				list.append('edit_title')
			session['edit'] = list
		elif 'update_title' in request.form:
			if not form2.validate_on_submit():
				if form2.title.errors:
					return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			if 'edit_title' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
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
			if not form2.validate_on_submit():
				if form2.background.errors:
					return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			if 'edit_background' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
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
			if not form2.validate_on_submit():
				if form2.description.errors:
					return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			if 'edit_description' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
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
			if not form2.validate_on_submit():
				if form2.email.errors:
					return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			if 'edit_contact' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
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
			return render_template('project.html', project=project, edit=session['edit'], form=form2,tag_form = tag_form, tags=session['tags'], remove_err = project_removal_error)
		elif 'add_tag' in request.form:
			temp_tags = session['tags']
			if tag_form.tags.data and tag_form.validate_on_submit():
				if tag_form.tags.data not in temp_tags:
					temp_tags.append(tag_form.tags.data)
					session['tags'] = temp_tags
				return render_template('project.html', project=project, edit=session['edit'], form=form2 ,tag_form = tag_form, tags=temp_tags, remove_err = project_removal_error)
		elif 'submit' in request.form:
			temp_tags = session['tags']
			session['removed_tags'].append(request.form['submit'])
			temp_tags.remove(request.form['submit'])
			session['tags'] = temp_tags
			return render_template('project.html', project=project, edit=session['edit'], form=form2,tag_form = tag_form, tags=temp_tags, remove_err = project_removal_error)
		elif 'update_tags' in request.form:
			# if there are tags in the dict...returns false if empty
			list.remove('edit_tags')
			session['edit'] = list
			temp_tags = session['tags']
			removed_tags = session['removed_tags']
			# if there are tags that exist for the project session
			if temp_tags:
				# get each tag in the dict
				for tag in temp_tags:
					# see if the tag already exists in the database
					skip = False
					# makes sure the tag is not already associated with a project
					for real_tag in project.p_tags:
						real_tag = real_tag.name.lower()
						tag = tag.lower()
						if real_tag == tag:
							skip = True
							break
					# skip the tag if it is already associated with the project
					if skip:
						skip = False
						continue
					tag = tag.capitalize()
					temp_tag = Tag(name=tag)
					# try to create the tag in the database
					try:
						db.session.add(temp_tag)
						project.p_tags.append(temp_tag)
						db.session.commit()
					# if fails, means the tag already exists
					except IntegrityError:
						db.session.rollback()
						temp_tag = Tag.query.filter_by(name=tag).first()
						project.p_tags.append(temp_tag)
						db.session.commit()
# could have error here if someone deletes the tag... ^^^^
			# if there are tags that need to be removed from the project
			if removed_tags:
				for tag in removed_tags:
					tag = tag.lower()
					tag = tag.capitalize()
					try:
						db_tag = Tag.session.query.filter_by(name=tag).first()
						project.p_tags.remove(db_tag)
						db.session.commit()
					except:
						print("Tag no longer in the system")
		elif 'remove_project' in request.form:
			if 'remove_project' not in list:
				list.append('remove_project')
			session['edit']=list
		elif 'remove_project_final' in request.form:
			if 'remove_project' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			else:
				title = request.form['remove_project_title']
				if title == project.title:
					db.session.delete(project)
					db.session.commit()
					list.remove('remove_project')
					return redirect(url_for('home'))
				else:
					project_removal_error = "\"" + str(title) + "\"" + " does not match the project title"
					print(str(title) + " does not match the project title")
		return render_template('project.html', project=project, edit=session['edit'], form=form2,tag_form = tag_form, remove_err = project_removal_error)
	elif project_id is None:
		searchForm = SearchForm()
		tag = None
		projects = []
		if request.method == "POST":
			if searchForm.validate_on_submit():
				tag = searchForm.search_tags.data
				print(str(tag))
				actual_tag = Tag.query.filter_by(name=tag).first()
				if actual_tag is None:
					projects = None
				else:
					for proj in actual_tag.projects:
						projects.append(proj)
		else:
			projects = Project.query.all()
		if 'edit' in session:
			session.pop('edit', None)
		for proj in projects:
			print(str(proj.title))
		# just a error check for now
		# will eventually want to show a list of all projects
		return render_template('projects.html', projects=projects, user=g.user, form=searchForm, len=6, current_page=2)
	else:
		if 'edit' in session:
			session.pop('edit', None)
		project = Project.query.filter_by(pid = project_id).first()
		if project is None:
			abort(404)
		else:
			return render_template('project.html', project = project, edit=[], form=ProjectForm(request.form))


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
			new_tag = form.tags.data.lower()
			new_tag = new_tag.capitalize()
			if new_tag in temp_tags:
				pass
			else:
				temp_tags.append(new_tag)
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
			db.session.add(Project(
				title = my_dict['title'],
				background = my_dict['background'],
				description = my_dict['description'],
				contact = my_dict['contact'],
				user = g.user.user_id))
			db.session.commit()
		# if there are tags in the dict...returns false if empty
			if temp_tags:
# this line could cause issues if two projects have the same title....
				project = Project.query.filter_by(title = my_dict['title']).first()
				# get each tag in the dict
				for tag in temp_tags:
					# see if the tag already exists in the database
					tag_list=Tag.query.filter_by(name = tag)
					# if the tag exists, simply associate this project with it
					if tag_list.first():
						if tag == tag_list.first().name:
							print("The tag " + str(tag) + " already existed.")
							temp_tag = tag_list.first()
							temp_tag.projects.append(project)
							# otherwise, need to create the tag in the database and
							# add the project to it
						else:
							db.session.add(Tag(name=tag))
							db.session.commit()
							temp_tag=Tag.query.filter_by(name=tag).first()
							temp_tag.projects.append(project)
					else:
						db.session.add(Tag(name=tag))
						db.session.commit()
						temp_tag=Tag.query.filter_by(name=tag).first()
						temp_tag.projects.append(project)
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
			projects = Project.query.filter_by(user = g.user.user_id).all()
			for project in projects:
				print(str(project.pid))
				print(str(project.title))
				print(str(project.background))
				print(str(project.description))
				#for Tag in project.p_tags:
				#	print("tag: " + str(Tag.name))
			flash(error)
			return render_template('home.html', my_projects=projects)
		else:
			error = "You are not logged in"
			flash(error)
		return render_template('home.html')
