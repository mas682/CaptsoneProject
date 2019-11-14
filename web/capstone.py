from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from sqlalchemy.exc import IntegrityError
from app import *
from models import db, Tag, User, Project, Applicantsclass, t_projecttags, t_applicantstags
from ProjectForm import ProjectForm, TagForm, SearchForm
import math
import operator
import nltk
import re



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
	#print(str(request.headers))
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
					admin = False,
					new_user=True))
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
					admin = False,
					new_user=True))
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
def projects(project_id = None, search_tags = None):
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
					temp_tag = Tag(name=tag, freq=1)
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
						temp_tag.freq = temp_tag.freq + 1
						db.session.commit()
# could have error here if someone deletes the tag... ^^^^
			# if there are tags that need to be removed from the project
			if removed_tags:
				for tag in removed_tags:
					tag = tag.lower()
					tag = tag.capitalize()
					print("REMOVE TAG: " + str(tag))
					try:
						db_tag = Tag.query.filter_by(name=tag).first()
						db_tag.projects.remove(project)
						db_tag.freq = db_tag.freq -1;
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
	# if there is not a project ID, this means go to the project page with a listing of the projects
	elif project_id is None:
		return search_projects(request)
	else:
		if 'edit' in session:
			session.pop('edit', None)
		project = Project.query.filter_by(pid = project_id).first()
		if project is None:
			abort(404)
		else:
			return render_template('project.html', project = project, edit=[], form=ProjectForm(request.form))

# method for handling getting correct projects to return based on search
# the argument is a string seperated by spaces
def find_tags(tag=None):
	# set the search in the cookie
	session['search'] = tag
	tags = []
	# see if there are any quoted strings in the search
	qlist = re.findall("\".*\"", tag)
	if(len(qlist) > 0):
		for t in qlist:
			# remove the quoted string fromt the search
			tag = tag.replace(t, "")
			# remove the quotes from the quoted string
			t = t.replace('\"', '')
			tags.append(t)
	# remove any extra white space from search string
	tag = tag.strip()
	# get the tokenized tags from the search string
	if len(tag) > 0:
		tags = tags + tag.split(" ")
	# get the individual tags within the search

	# get the number of tags in the search
	tag_length = len(tags)
	# stores the projects that are assoicated with the tags
	temp_projects= []
	# stores the sorted projects based on how many of the tags correspond to the projects
	sorted_output = []
	projects = []
	# add all the projects associated with each individual tag to temp_projects
	# but do not add duplicates
	for num in range(tag_length):
		# get the tag itself
		tags[num] = tags[num].lower()
		tags[num] = tags[num].capitalize()

		#old:
		#temp_tag = Tag.query.filter_by(name=tags[num]).first()
		#new:
		temp_tag = Tag.query.filter(Tag.name.startswith(tags[num])).all()
		# if the tag does not exist in the database, skip to next tag to check
		if temp_tag is None:
			continue
		# if the tag exists, check the projects it is associated with
		for t in temp_tag:
			for proj in t.projects:
				# if temp_projects does not have this project yet, add it to it
				if proj not in temp_projects:
					temp_projects.append(proj)
	# iterate through all the projects in temp_projects to see how many of the searched for tags
	# are in each individual project
	for proj in temp_projects:
		# counter used to see how many of the searched terms match what is being looked for
		counter = 0
		# iterate through the tags that are being searched for
		for num in range(tag_length):
			# get the actual tag
			temp_tag = Tag.query.filter(Tag.name.startswith(tags[num])).all()
			# if the tag does not exist, skip this search term
			if temp_tag is None:
				continue
			for t in temp_tag:
				# if the tag to look for is in this project, increment the counter
				if t in proj.p_tags:
					counter = counter + 1
		# after the inner for loop, add a (project id, tag occurrences) tuple to sorted_output
		sorted_output.append((proj.pid, counter))
	# sort the output by the number of occurences of a tag in a project
	# thus, if every term searched for is in a project, it should be at the front of the list
	sorted_output.sort(key = operator.itemgetter(1), reverse=True)

	# add the projects to a list based off of the indexes in the sorted_output
	for pair in sorted_output:
		project = Project.query.filter_by(pid=pair[0]).first()
		projects.append(project)
	# return the projects to be output
	return projects

# method for handling a request for the projects page
def search_projects(request=None):
	searchForm = SearchForm(request.args)
	tag = None
	projects = []
	length = 0
	current_page = 0
	session['current_page'] = 0
	if request.method == "GET" and (request.args.get('search_tags') or request.args.get('index')):
		# if the user has entered some tag/s to search for, do this
		if searchForm.validate():
			tag = searchForm.search_tags.data
			projects = find_tags(tag)
		# if no tags entered, return list of all pages
		else:
			current_page = 0
			session['current_page'] = 0
			projects = Project.query.all()
		length = len(projects)
		# if the POST was done to get more entries from the table
		if request.args.get('index'):
			# get the page value that was clicked on
			index = request.args.get('index')
			index = int(index) -1
			session['current_page'] = index
			index = index * 10
			if projects is not None:
				projects = projects[index:index+10]
		else:
			if projects is not None:
				projects = projects[0:10]
	# if no search_tags argument or index
	else:
		current_page = 0
		session['search'] = ""
		session['current_page'] = 0
		projects = Project.query.all()
		length = len(projects)
		projects = projects[current_page*10:current_page+10]
	# remove edit as no longer editing a single project if on this page
	if 'edit' in session:
		session.pop('edit', None)
	length = math.ceil(length/10.0)

	return render_template('projects.html', projects=projects, user=g.user, form=searchForm, len=length, current_page=session['current_page']+1, search=session['search'])

# method for handling a request for the home page
def get_table_page(request=None):
	projects = []
	length = 0
	current_page = 0
	session['current_page'] = 0
	if request.method == "GET" and request.args.get('index'):
		current_page = 0
		session['current_page'] = 0
		projects = Project.query.filter_by(user = g.user.user_id).all()
		length = len(projects)
		# if the POST was done to get more entries from the table
		if request.args.get('index'):
			# get the page value that was clicked on
			index = request.args.get('index')
			index = int(index) -1
			session['current_page'] = index
			index = index * 5
			if projects is not None:
				projects = projects[index:index+5]
		else:
			if projects is not None:
				projects = projects[0:5]
	# if no search_tags argument or index
	else:
		current_page = 0
		session['current_page'] = 0
		projects = Project.query.filter_by(user = g.user.user_id).all()
		length = len(projects)
		projects = projects[current_page*5:current_page+5]
	# remove edit as no longer editing a single project if on this page
	if 'edit' in session:
		session.pop('edit', None)
	length = math.ceil(length/5.0)

	return [projects, length, session['current_page'] + 1]

def get_suggested_table(request, tag_string):
	suggested_projects = find_tags(tag_string)
	length = 0
	current_page = 0
	session['current_page2'] = 0
	if request.method == "GET" and request.args.get('index2'):
		current_page = 0
		session['current_page2'] = 0
		length = len(suggested_projects)
		# if the POST was done to get more entries from the table
		if request.args.get('index2'):
			# get the page value that was clicked on
			index = request.args.get('index2')
			index = int(index) -1
			session['current_page2'] = index
			index = index * 5
			if suggested_projects is not None:
				suggested_projects = suggested_projects[index:index+5]
		else:
			if suggested_projects is not None:
				suggested_projects = suggested_projects[0:5]
	# if no search_tags argument or index
	else:
		current_page = 0
		session['current_page2'] = 0
		length = len(suggested_projects)
		suggested_projects = suggested_projects[current_page*5:current_page+5]
	# remove edit as no longer editing a single project if on this page
	if 'edit' in session:
		session.pop('edit', None)
	print(length)
	length = math.ceil(length/5.0)
	print(length)

	return [suggested_projects, length, session['current_page2'] + 1]


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
								"tags": [],
								"suggested_tags": demo_nltk(form.title.data, form.background.data, form.description.data)}
			session['tags'] = []
			flash(form.title.data)
			return redirect(url_for('create_tags'))
	return render_template('create_project.html', form=form)

@app.route('/my_tags', methods=['Get', 'Post'])
def my_tags():
	if not g.user:
		return redirect(url_for('home'))
	all_tags = Tag.query.all()
	tags = []
	for tag in all_tags:
		if tag.projects.first():
			tags.append(tag)
	temp_tags = g.user.u_tags
	form = TagForm(request.form)
	if request.method == 'POST':
		if 'submit' in request.form:
			temp_tag = Tag.query.filter_by(name=request.form['submit']).first()
			if temp_tag in temp_tags:
				tag = request.form['submit']
				remove_user_tag(tag)
				temp_tags = User.query.filter_by(user_id=g.user.user_id).first().u_tags
			else:
				tag = request.form['submit']
				print("Trying to add tag " + tag)
				add_user_tag(tag)
				temp_tags = User.query.filter_by(user_id=g.user.user_id).first().u_tags
			return render_template('my_tags.html', tags=tags, my_tags = temp_tags, form=form)
		elif form.submit2.data and form.validate_on_submit():
			new_tag = form.tags.data.lower()
			new_tag = new_tag.capitalize()
			if new_tag in temp_tags:
				pass
			else:
				add_user_tag(new_tag)
				temp_tags = User.query.filter_by(user_id=g.user.user_id).first().u_tags
			return render_template('my_tags.html', tags=tags, my_tags = temp_tags, form=form)
	tags.sort(key=lambda x: x.name)
	return render_template('my_tags.html',tags=tags, form=form, my_tags = temp_tags)

def add_user_tag(tag):
	# see if the tag already exists in the database
	tag_list=Tag.query.filter_by(name = tag)
	# if the tag exists, see if the user is already associated with it
	if tag_list.first():
		if tag == tag_list.first().name:
			temp_tag = tag_list.first()
			# make sure user not associated with tag before trying to add user to it
			if g.user not in temp_tag.users:
				temp_tag.users.append(g.user)
			# otherwise, need to create the tag in the database and
			# add the user to it
			# probably redundant but just in case
		else:
			db.session.add(Tag(name=tag, freq=0))
			db.session.commit()
			temp_tag=Tag.query.filter_by(name=tag).first()
			temp_tag.users.append(g.user)
	else:
		db.session.add(Tag(name=tag, freq=0))
		db.session.commit()
		temp_tag=Tag.query.filter_by(name=tag).first()
		temp_tag.users.append(g.user)
	db.session.commit()

# method to handle removing a tag from a user
def remove_user_tag(tag):
	print("Remove tag with name " + tag)
	# see if the tag already exists in the database, which it should
	tag_list=Tag.query.filter_by(name = tag)
	# if the tag exists, remove it from assoication to user
	if tag_list.first():
		if tag == tag_list.first().name:
			temp_tag = tag_list.first()
			# make sure user already associated with the tag
			if g.user in temp_tag.users:
				temp_tag.users.remove(g.user);
		db.session.commit()

@app.route('/create_project/create_tags', methods=['Get', 'Post'])
def create_tags():
	form = TagForm(request.form)
	if not g.user.provider:
		return redirect(url_for('home'))
	if not 'form1' in session:
		return redirect(url_for('home'))
	my_dict = session['form1']
	temp_tags = my_dict['tags']
	suggested_tags = my_dict['suggested_tags']
	if request.method =='POST':
		if form.submit2.data and form.validate_on_submit():
			new_tag = form.tags.data.lower()
			new_tag = new_tag.capitalize()
			if new_tag in temp_tags:
				pass
			else:
				temp_tags.append(new_tag)
			my_dict['tags'] = temp_tags
			session.pop('form1', None)
			session['form1'] = my_dict
			return render_template('create_tags.html', form=form, tags=session['form1']['tags'], suggested_tags = suggested_tags)
		elif 'submit' in request.form:
			temp_tags.remove(request.form['submit'])
			my_dict['tags'] = temp_tags
			session.pop('form1', None)
			session['form1'] = my_dict
			return render_template('create_tags.html', form=form, tags=temp_tags, suggested_tags=suggested_tags)
		elif 'submit_suggested' in request.form:
			tag = request.form['submit_suggested']
			if tag not in temp_tags:
				temp_tags.append(tag)
			my_dict['tags'] = temp_tags
			session.pop('form1', None)
			session['form1'] = my_dict
			return render_template('create_tags.html', form=form, tags=temp_tags, suggested_tags=suggested_tags)
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
							temp_tag.freq = temp_tag.freq + 1
							temp_tag.projects.append(project)
							# otherwise, need to create the tag in the database and
							# add the project to it
						else:
							db.session.add(Tag(name=tag, freq=1))
							db.session.commit()
							temp_tag=Tag.query.filter_by(name=tag).first()
							temp_tag.projects.append(project)
					else:
						db.session.add(Tag(name=tag, freq=1))
						db.session.commit()
						temp_tag=Tag.query.filter_by(name=tag).first()
						temp_tag.projects.append(project)
					db.session.commit()
				for tag in suggested_tags:
					if not tag in temp_tags:
						sug_tag = Tag.query.filter_by(name=tag).first()
						print(tag + " not in temp tags")
						if sug_tag:
							sug_tag.freq = sug_tag.freq -1
							print("decreasing value for " + sug_tag.name + " to " + str(sug_tag.freq))
					db.session.commit()
			session.pop('form1', None)
			return redirect(url_for('home'))
	return render_template('create_tags.html', form=form, tags=temp_tags, suggested_tags=suggested_tags)

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


def demo_nltk(title, description, background):
	testStr=[]
	testStr.append(title)
	testStr.append(description)
	testStr.append(background)
	finalTags = []
	for line in testStr:
		print("LINE")
		tokenArray=nltk.word_tokenize(line)
		taggedArray=nltk.pos_tag(tokenArray)
		print("\nTagged sentence: \n"+str(taggedArray)+"\n\n\n\n\n\n");
		tags=[]
		for word,type in taggedArray:
			if(type=='NN' or type=='NNP' or type=='NNS' or type=='NNPS'):
				noun=word
				startFrom=tokenArray.index(word)
				#print(startFrom)
				for x in range(startFrom-1,0,-1):
					prevWord=taggedArray[x]
					#print("prevword : "+str(prevWord))
					if(prevWord[1]=='JJ' or prevWord[1] == 'JJR' or prevWord[1]=='JJS'
						or prevWord[1]=='NN' or prevWord[1]=='NNP' or prevWord[1]=='NNS' or prevWord[1]=='NNPS'):
						noun=prevWord[0]+" "+noun
						#print("prev added")
					else:
						break
				for x in range(startFrom+1, len(tokenArray)):
					afterWord=taggedArray[x]
					#print("afterword : "+str(afterWord))
					if(afterWord[1]=='JJ' or afterWord[1] == 'JJR' or afterWord[1]=='JJS'
						or afterWord[1]=='NN' or afterWord[1]=='NNP' or afterWord[1]=='NNS' or afterWord[1]=='NNPS'):
						noun=noun + " "+afterWord[0]
						#print("after added")
					else:
						break
				tags.append(noun)
			tags=list(dict.fromkeys(tags))
			print("TAGS:" + str(tags))
		finalTags = finalTags + tags
	tag_set = set()
	for tag in finalTags:
		tag_arr = tag.split(" ")
		for t in tag_arr:
			t = t.lower()
			t = t.capitalize()
			suggested = Tag.query.filter_by(name=t).first()
			if not suggested:
				db.session.add(Tag(name=t, freq=0))
				tag_set.add(t)
				db.session.commit()
			else:
				# only add tag to suggested if it has not been denied more than some set threshold
				print(suggested.name + " " + str(suggested.freq))
				if(suggested.freq > -3):
					tag_set.add(t)
	print("\nTags:"+str(tag_set))
	return list(tag_set)

# The home page.
@app.route('/', methods=['GET', 'POST'])
def home():
	"""Logs the user in."""
	error = None
	new_user = False
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
			if g.user.new_user:
				g.user.new_user = False
				db.session.commit()
				new_user=True
			error = "You are logged in"
			projects = get_table_page(request)
			tag_string = ""
			for tag in g.user.u_tags:
				tag_string = tag_string + tag.name + " "
			s_projects = get_suggested_table(request, tag_string)
# will want to remove projects that this user is the owner of..
			flash(error)
			return render_template('home.html', new_user = new_user, my_projects=projects[0], len=projects[1], current_page=projects[2], suggested_projects = s_projects[0], len2=s_projects[1], current_page_suggested = s_projects[2])
		else:
			error = "You are not logged in"
			flash(error)
		return render_template('home.html')
