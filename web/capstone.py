from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from sqlalchemy.exc import IntegrityError
from app import *
from models import db, Tag, User, Project, ApplicantTags, KeyWord
from ProjectForm import ProjectForm, TagForm, SearchForm, ApplicantForm, AccountRemovalForm
import math
import operator
import nltk
import re
import string


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


# this is for a user registering themselves
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

# this is for a admin registering a provider
@app.route('/register_provider', methods=['GET', 'POST'])
def registerProvider():
	"""Registers a project provider."""
	if not g.user.admin:
		return redirect(url_for('home'))
	if 'edit' in session:
		session.pop('edit', None)
	error = None
	output = None
	if request.method == 'POST':
		if not request.form['email'] or '@' not in request.form['email']:
			error = 'You have to enter a valid email address'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		else:
			try:
				if(request.form.get('admin')):
					db.session.add(User(
						email = request.form['email'],
						password = request.form['password'],
						provider = True,
						admin = True,
						new_user=True))
				else:
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
			output = 'New user successfully registered!'

	return render_template('register_provider.html', error=error, output = output)

@app.route('/logout')
def logout():
	if 'edit' in session:
		session.pop('edit', None)
	"""Logs the user out."""
	flash('You were logged out. Thanks!')
	session.pop('user_id', None)
	return redirect(url_for('home'))

# this method deals with searching projects, and individual project pages
@app.route('/projects', methods=['GET', 'POST'])
@app.route('/projects/<project_id>', methods=['GET', 'POST'])
def projects(project_id = None, search_tags = None):
	print(str(request.method))
	project = None
	if project_id is not None:
		project = Project.query.filter_by(pid=project_id).first()
		if project is None:
			abort(404)
	if request.method == 'POST' and project_id is not None:
		form2 = ProjectForm(request.form, background=project.background, summary=project.summary, description=project.description,
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
				# remove previous keywords generated from the project description
				# could cause issue if keyword removed but keyword was still in background or summary?
				remove_keywords(project.title, project)
				project.title = form2.title.data
				db.session.commit()
				# create text of them all in case keyword removed on accident in remove_keywords
				text = project.title + " " + project.description + " " + project.background + " " + project.summary
				create_inverted_index(text, project)
		elif 'edit_summary' in request.form:
			if 'edit_summary' not in list:
				list.append('edit_summary')
			session['edit']=list
		elif 'update_summary' in request.form:
			if not form2.validate_on_submit():
				if form2.summary.errors:
					return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			if 'edit_summary' not in list:
				return render_template('project.html', project=project, edit=session['edit'], form=form2, tag_form = tag_form, remove_err = project_removal_error)
			else:
				list.remove('edit_summary')
				session['edit'] = list
				# remove previous keywords generated from the project description
				# could cause issue if keyword removed but keyword was still in background or summary?
				remove_keywords(project.summary, project)
				project.summary= form2.summary.data
				db.session.commit()
				# create text of them all in case keyword removed on accident in remove_keywords
				text = project.title + " " + project.description + " " + project.background + " " + project.summary
				create_inverted_index(text, project)
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
				# remove previous keywords generated from the project description
				# could cause issue if keyword removed but keyword was still in background or summary?
				remove_keywords(project.background, project)
				project.background = form2.background.data
				db.session.commit()
				# create text of them all in case keyword removed on accident in remove_keywords
				text = project.title + " " + project.description + " " + project.background + " " + project.summary
				create_inverted_index(text, project)
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
				# remove previous keywords generated from the project description
				# could cause issue if keyword removed but keyword was still in background or summary?
				remove_keywords(project.description, project)
				project.description = form2.description.data
				db.session.commit()
				# create text of them all in case keyword removed on accident in remove_keywords
				text = project.title + " " + project.description + " " + project.background + " " + project.summary
				create_inverted_index(text, project)
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
		elif 'cancel_remove_project' in request.form:
			if 'remove_project' in list:
				list.remove('remove_project')
			if 'remove_project_final' in list:
				list.remove('remove_project_final')
			session['edit'] = list
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

# method to handle when a user updates a project description, background, or title
# and thus new keywords must be generated
# keyword is the string of keywords
# project is the project to remove the keywords from
def remove_keywords(keyword, project):
	key_list = get_key_words(keyword)
	for key in key_list:
		key_tag = KeyWord.query.filter_by(name=key).first()
		# if the keyword exists
		if key_tag:
			# if the keyword is associated with the project, remove it
			if project in key_tag.projects:
				try:
					key_tag.projects.remove(project)
					db.session.commit()
				except:
					print("Keyword no longer in the system")

# method for handling getting correct projects to return based on search
# the argument is a string seperated by spaces
# searching keywords
def find_keywords(keyword):
	# set the search in the cookie
	session['keyword'] = keyword
	keywords = []
	# see if there are any quoted strings in the search
	qlist = re.findall("\".*\"", keyword)
	if(len(qlist) > 0):
		for t in qlist:
			# remove the quoted string fromt the search
			keyword = keyword.replace(t, "")
			# remove the quotes from the quoted string
			t = t.replace('\"', '')
			keywords.append(t)
	# remove any extra white space from search string
	keyword = keyword.strip()
	# get the tokenized tags from the search string
	if len(keyword) > 0:
		keywords = keywords + keyword.split(" ")
	# get the individual tags within the search

	# get the number of tags in the search
	keyword_length = len(keywords)
	# stores the projects that are assoicated with the tags
	temp_projects= []
	# stores the sorted projects based on how many of the tags correspond to the projects
	sorted_output = []
	projects = []
	# add all the projects associated with each individual tag to temp_projects
	# but do not add duplicates
	for num in range(keyword_length):
		# get the tag itself

		#new:
		temp_key = KeyWord.query.filter(KeyWord.name.startswith(keywords[num])).all()
		# if the tag does not exist in the database, skip to next tag to check
		if temp_key is None:
			continue
		# if the tag exists, check the projects it is associated with
		for t in temp_key:
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
		for num in range(keyword_length):
			# get the actual tag
			temp_key = KeyWord.query.filter(KeyWord.name.startswith(keywords[num])).all()
			# if the tag does not exist, skip this search term
			if temp_key is None:
				continue
			for t in temp_key:
				# if the tag to look for is in this project, increment the counter
				if t in proj.p_keys:
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


# method for handling getting correct projects to return based on search
# the argument is a string seperated by spaces
def find_tags_suggested(tags=None):
	# stores the projects that are assoicated with the tags
	temp_projects= []
	# stores the sorted projects based on how many of the tags correspond to the projects
	sorted_output = []
	projects = []
	# add all the projects associated with each individual tag to temp_projects
	# but do not add duplicates
	for tag in tags:
		temp_tag = Tag.query.filter_by(tid = tag.tid).first()
		# if the tag does not exist in the database, skip to next tag to check
		if temp_tag is None:
			continue
		# if the tag exists, check the projects it is associated with
		for proj in temp_tag.projects:
			# if temp_projects does not have this project yet, add it to it
			if proj not in temp_projects and proj.user != g.user.user_id:
				temp_projects.append(proj)
	# iterate through all the projects in temp_projects to see how many of the searched for tags
	# are in each individual project
	for proj in temp_projects:
		# counter used to see how many of the searched terms match what is being looked for
		counter = 0
		# iterate through the tags that are being searched for
		for tag in tags:
			# get the actual tag
			temp_tag = Tag.query.filter_by(tid = tag.tid).first()
			# if the tag does not exist, skip this search term
			if temp_tag is None:
				continue
			# if the tag to look for is in this project, increment the counter
			if temp_tag in proj.p_tags:
				counter = counter + tag.value
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
	if g.user:
		searchForm = SearchForm(request.args)
		tag = None
		projects = []
		length = 0
		current_page = 0
		session['current_page'] = 0
		if request.method == "GET" and (request.args.get('search') or request.args.get('index')):
			# if the user has entered some tag/s to search for, do this
			if searchForm.validate():
				session['search'] = searchForm.search.data
				session['type'] = searchForm.type.data
				search = searchForm.search.data
				print(searchForm.type.data)
				if searchForm.type.data == "Search by tag":
					projects = find_tags(search)
				else:
					projects = find_keywords(search)
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
			session['type'] = ""
			session['current_page'] = 0
			projects = Project.query.all()
			length = len(projects)
			projects = projects[current_page*10:current_page+10]
		# remove edit as no longer editing a single project if on this page
		if 'edit' in session:
			session.pop('edit', None)
		length = math.ceil(length/10.0)
		return render_template('projects.html', projects=projects, user=g.user, form=searchForm, len=length, current_page=session['current_page']+1, search=session['search'], type=session['type'])
	else:
		sample_projects = Project.query.all()
		sample_projects = sample_projects[0:10]
		for t in sample_projects:
			print("1. " + t.title)
		return render_template('projects.html', sample_projects=sample_projects)

# method to get a list of the users and their associated projects
def get_table_users(request=None):
	users = []
	temp_users = None
	length = 0
	actual_index = 0
	if request.method == "GET" and request.args.get('index'):
		temp_users = User.query.order_by(User.email).all()
		length = len(temp_users)
		if request.args.get('index'):
			index = request.args.get('index')
			actual_index = int(index)
			index = int(index) -1
			index = index * 10
			if temp_users is not None:
				temp_users = temp_users[index:index+10]
		else:
			if temp_user is not None:
				temp_users = temp_users[0:10]
	else:
		actual_index = 1
		temp_users = User.query.order_by(User.email).all()
		length = len(temp_users)
		temp_users = temp_users[0:10]
	if 'edit' in session:
		session.pop('edit', None)
	length = math.ceil(length/10.0)

	projects = None
	for user in temp_users:
		projects = None
		p = Project.query.filter_by(user=user.user_id).all()
		if p is not None:
			projects = p
		users.append([user, projects])

	return [users, length, actual_index]

# method to get a list of the users projects that they have listed
def get_table_page(request=None):
	projects = []
	length = 0
	current_page = 0
	session['current_page'] = 0
	if request.method == "GET" and request.args.get('index'):
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

# method to get a list of the users suggested projects
def get_suggested_table(request, tags):
	suggested_projects = find_tags_suggested(tags)
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

# this is for the first page of creating a project
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
								"summary": form.summary.data,
								"tags": [],
								"suggested_tags": demo_nltk(form.title.data, form.background.data, form.description.data, form.summary.data)}
			session['tags'] = []
			return redirect(url_for('create_tags'))
	return render_template('create_project.html', form=form)

# method to handle a user ranking their tags
@app.route('/my_tags/values', methods=['Get', 'Post'])
def tag_ranking():
	if not g.user:
		return redirect(url_for('home'))
	temp_tags = []
	output = None
	if request.method == 'POST':
		print(request.form)
		for tag in request.form:
			my_tag = ApplicantTags.query.filter_by(tid=tag).first()
			my_tag.value = request.form[tag]
		db.session.commit()
		output = "Your tag values have been updated"

	tag_ids = ApplicantTags.query.filter_by(uid=g.user.user_id).all()
	for t in tag_ids:
		tag = Tag.query.filter_by(tid=t.tid).first()
		temp_tags.append([tag, t.value])
	return render_template('tag_ranks.html', tags = temp_tags, output = output)

# this deals with a user editing their tags associated with themselves
@app.route('/my_tags', methods=['Get', 'Post'])
def my_tags():
	if not g.user:
		return redirect(url_for('home'))
	all_tags = Tag.query.all()
	tags = []
	for tag in all_tags:
		if tag.projects.first():
			tags.append(tag)
	temp_tags = []
	tag_ids = ApplicantTags.query.filter_by(uid = g.user.user_id).all()
	for id in tag_ids:
		tag = Tag.query.filter_by(tid = id.tid).first()
		temp_tags.append(tag)
	form = TagForm(request.form)
	if request.method == 'POST':
		if 'submit' in request.form:
			temp_tag = Tag.query.filter_by(name=request.form['submit']).first()
			if temp_tag in temp_tags:
				tag = request.form['submit']
				remove_user_tag(tag)
				temp_tags.remove(temp_tag)
			else:
				tag = request.form['submit']
				print("Trying to add tag " + tag)
				add_user_tag(tag)
				t = Tag.query.filter_by(name=tag).first()
				temp_tags.append(t)
			return render_template('my_tags.html', tags=tags, my_tags = temp_tags, form=form)
		elif form.submit2.data and form.validate_on_submit():
			new_tag = form.tags.data.lower()
			new_tag = new_tag.capitalize()
			if new_tag in temp_tags:
				pass
			else:
				add_user_tag(new_tag)
				t = Tag.query.filter_by(name=new_tag).first()
				temp_tags.append(t)
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
			users = ApplicantTags.query.filter_by(tid = temp_tag.tid).filter_by(uid = g.user.user_id).first()
			if not users:
				db.session.add(ApplicantTags(uid=g.user.user_id, tid=temp_tag.tid, value=3))
			# otherwise, need to create the tag in the database and
			# add the user to it
			# probably redundant but just in case
		else:
			db.session.add(Tag(name=tag, freq=0))
			db.session.commit()
			temp_tag=Tag.query.filter_by(name=tag).first()
			db.session.add(ApplicantTags(uid=g.user.user_id, tid=temp_tag.tid, value=3))
	else:
		db.session.add(Tag(name=tag, freq=0))
		db.session.commit()
		temp_tag=Tag.query.filter_by(name=tag).first()
		db.session.add(ApplicantTags(uid=g.user.user_id, tid=temp_tag.tid, value=3))
		#temp_tag.users.append(g.user, 3)
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
			utag = ApplicantTags.query.filter_by(uid = g.user.user_id).filter_by(tid = temp_tag.tid).first()
			if utag:
				db.session.delete(utag)
				db.session.commit()

# this deals with adding tags to a project when creating it
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
				summary = my_dict['summary'],
				user = g.user.user_id))
			db.session.commit()
			text = my_dict['title'] + " " +  my_dict['background'] + " " + my_dict['description']
# this line could cause issues if two projects have the same title....
			project = Project.query.filter_by(title = my_dict['title']).filter_by(user = g.user.user_id).first()
			create_inverted_index(text, project)
		# if there are tags in the dict...returns false if empty
			if temp_tags:
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

# this method will strip a string of all punctuation excpet for '
# also returns a list of tokenized strings
# this method is used for generating the inverted index table of terms referenced in projects
def get_key_words(text):
	punct = "!\"#$%&()*+,-./:;<=>?@[\]^_`{|}~”“"
	temp = text.translate(str.maketrans('', '', punct))
	tokens = None
	if temp:
		tokens = temp.split(" ")
	for t in tokens:
		print(t)
	return tokens

# method handles generating the inverted index for the terms referenced in a project
def create_inverted_index(text, project):
	tokens = get_key_words(text)
	if tokens:
		for term in tokens:
			if len(term) > 24:
				continue
			keyword = KeyWord.query.filter_by(name=term).first()
			if not keyword:
				try:
					db.session.add(KeyWord(name=term)) # need to add project here..
					db.session.commit()
					keyword = KeyWord.query.filter_by(name=term).first()
					if project not in keyword.projects:
						keyword.projects.append(project)
						db.session.commit()
					print("Keyword " + str(term) + " added to db")
				# if fails, means the keword already exists
				except IntegrityError:
					db.session.rollback()
					keyword = KeyWord.query.filter_by(name=term).first()
					if project not in keyword.projects:
						keyword.projects.append(project)
						# want to consider adding frequency of term in project...
						db.session.commit()
					print("Keyword " + str(term) + " added to db")
			else:
				if project not in keyword.projects:
					keyword.projects.append(project)
					db.session.commit()
				print("Keyword " + str(term) + " added to db")

# method for a user updating their own email
def update_email(form, list):
	error = None
	if (g.user.provider or g.user.admin) and '@' not in form.email.data:
		error = "You must enter a email address"
		if 'update_email' not in list:
			list.append('update_email')
	elif g.user and not(g.user.provider or g.user.admin) and '@pitt.edu' not in form.email.data:
		error = "You must enter your University of Pittsburgh email"
		if 'update_email' not in list:
			list.append('update_email')
	else:
		try:
			g.user.email = form.email.data
			print(form.email.data)
			print(g.user.email)
			db.session.commit()
			list.remove('edit_email')
			if 'update_email' in list:
				list.remove('update_email')
			session.pop('edit_account', None)
			session['edit_account'] = list
		except IntegrityError:
			db.session.rollback()
			error = "Email aleady exists in the system"
			list.append('edit_email')
			list.append('update_email')
	return error

# method for a admin updating a users email
def update_email_admin(form, list, user):
	error = None
	if (user.provider or user.admin) and '@' not in form.email.data:
		error = "You must enter a email address"
		if 'update_email' not in list:
			list.append('update_email')
	elif user and not(user.provider or user.admin) and '@pitt.edu' not in form.email.data:
		error = "You must enter your University of Pittsburgh email"
		if 'update_email' not in list:
			list.append('update_email')
	else:
		try:
			user.email = form.email.data
			print(form.email.data)
			print(user.email)
			db.session.commit()
			list.remove('edit_email')
			if 'update_email' in list:
				list.remove('update_email')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
		except IntegrityError:
			db.session.rollback()
			error = "Email aleady exists in the system"
			list.append('edit_email')
			list.append('update_email')
	return error

# method for a user updating their own password
def update_password(form, list):
	success = False
	if(len(form.password.data) < 1):
		form.password.errors.append("A password must be entered")
		print(form.password.data)
	if(len(form.password2.data) < 1):
		form.password2.errors.append("A password must be entered")
	if(len(form.password3.data) < 1):
		form.password3.errors.append("A password must be entered")
	elif(g.user.password != form.password.data):
		form.password.errors.append("The password is incorrect")
		form.password.data=""
	elif(len(form.password2.data) < 6):
		form.password2.errors.append("Password must be at least 6 characters")
	elif(form.password3.data != form.password2.data):
		form.password3.errors.append("This password does not match the new password")
	elif(len(form.password2.data) > 20):
		form.password2.errors.append("Password cannot be greater than 20 characters")
	elif(len(form.password3.data) > 20):
		form.password3.errors.append("Password cannot be greater than 20 characters")
	elif(form.password2.data == g.user.password):
		form.password2.errors.append("The new password matches the old password")
	else:
		try:
			g.user.password = form.password2.data
			print(form.password2.data)
			db.session.commit()
			if 'update_pass' in list:
				list.remove('update_pass')
			session.pop('edit_account', None)
			session['edit_account'] = list
			print("password updated")
			success = True
		except IntegrityError:
			db.session.rollback()
			form.password1.errors.append("There was an error updating the password")
	form.password.data=""
	form.password2.data=""
	form.password3.data=""
	return success

# method for a admin updating a users password
def update_password_admin(form, list, user):
	success = False
	if(len(form.password.data) < 1):
		form.password.errors.append("A password must be entered")
		print(form.password.data)
	if(len(form.password2.data) < 1):
		form.password2.errors.append("A password must be entered")
	if(len(form.password3.data) < 1):
		form.password3.errors.append("A password must be entered")
	elif(g.user.password != form.password.data):
		print(g.user.password)
		print(form.password.data)
		form.password.errors.append("Your password is incorrect")
		form.password.data=""
	elif(len(form.password2.data) < 6):
		form.password2.errors.append("Password must be at least 6 characters")
	elif(form.password3.data != form.password2.data):
		form.password3.errors.append("This password does not match the new password")
	elif(len(form.password2.data) > 20):
		form.password2.errors.append("Password cannot be greater than 20 characters")
	elif(len(form.password3.data) > 20):
		form.password3.errors.append("Password cannot be greater than 20 characters")
	elif(form.password2.data == user.password):
		form.password2.errors.append("The new password matches the old password")
	else:
		try:
			user.password = form.password2.data
			db.session.commit()
			if 'update_pass' in list:
				list.remove('update_pass')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
			success = True
		except IntegrityError:
			db.session.rollback()
			form.password1.errors.append("There was an error updating the password")
	form.password.data=""
	form.password2.data=""
	form.password3.data=""
	return success

# method for a admin chaning a users rights
def update_rights_admin(form, list, user, rights):
	success = False
	try:
		# if set to admin, automatically given provider rights
		if 'admin' in rights:
			user.admin = True
			user.provider = True
		else:
			user.admin = False
			if 'provider' in rights:
				user.provider = True
			else:
				user.provider = False
				# if setting the provider to false, remove their projects
				projects = Project.query.filter_by(user = user.user_id).all()
				if projects is not None:
					for p in projects:
						db.session.delete(p)
		db.session.commit()
		if 'update_rights' in list:
			list.remove('update_rights')
		list.remove('edit_rights')
		session.pop('edit_account_admin', None)
		session['edit_account_admin'] = list
		success = True
	except IntegrityError:
		db.session.rollback()
	return success


# method for a user to delete their own account
def remove_account(form, list):
	success = False
	if(len(form.password.data) < 1 or len(form.email.data) < 1):
		if(len(form.password.data) < 1):
			form.password.errors.append("Your password must be entered")
		if(len(form.email.data) < 1):
			form.email.errors.append("Your email must be entered")
	elif(g.user.email != form.email.data):
		form.email.errors.append("The email is incorrect")
		form.email.data=""
	elif(g.user.password != form.password.data):
		form.password.errors.append("The password is incorrect")
		form.password.data=""
	else:
		user = User.query.filter_by(user_id=g.user.user_id).first()
		tags = ApplicantTags.query.filter_by(uid=user.user_id).all()
		for t in tags:
			db.session.delete(t)
		projects = Project.query.filter_by(user=user.user_id).all()
		for p in projects:
			db.session.delete(p)
		db.session.commit()
		try:
			db.session.delete(user)
			db.session.commit()
			print("Account deleted")
			success = True
		except IntegrityError:
			db.session.rollback()
			form.password.errors.append("There was an error deleting the account")
	form.password.data=""
	form.email.data=""
	return success

# method for a admin user to an account
def remove_account_admin(form, list, user):
	success = False
	if(len(form.password.data) < 1 or len(form.email.data) < 1):
		if(len(form.password.data) < 1):
			form.password.errors.append("Your password must be entered")
		if(len(form.email.data) < 1):
			form.email.errors.append("The account to removes email must be entered")
	elif(user.email != form.email.data):
		form.email.errors.append("The email is incorrect")
		form.email.data=""
	elif(g.user.password != form.password.data):
		form.password.errors.append("Your password is incorrect")
		form.password.data=""
	else:
		tags = ApplicantTags.query.filter_by(uid=user.user_id).all()
		for t in tags:
			db.session.delete(t)
		projects = Project.query.filter_by(user=user.user_id).all()
		for p in projects:
			db.session.delete(p)
		db.session.commit()
		try:
			db.session.delete(user)
			db.session.commit()
			print("Account deleted")
			success = True
		except IntegrityError:
			db.session.rollback()
			form.password.errors.append("There was an error deleting the account")
	form.password.data=""
	form.email.data=""
	return success

# method for the my account page
@app.route('/my_account', methods=['Get', 'Post'])
def account():
	if not g.user:
		flash("You are not logged in")
		return redirect(url_for('home'))
	else:
		my_tags = []
		tag_ids = ApplicantTags.query.filter_by(uid=g.user.user_id).all()
		for tag in tag_ids:
			t = Tag.query.filter_by(tid = tag.tid).first()
			my_tags.append(t)
		form = ApplicantForm(request.form, email=g.user.email)
		form2=AccountRemovalForm(request.form)
		if request.method == 'POST':
			user = User.query.filter_by(user_id=g.user.user_id).first()
			list = []
			if 'edit_account' not in session:
				list = []
				session['edit_account'] = []
			else:
				list = session['edit_account']
				for t in list:
					print(t)
			if 'edit_email' in request.form:
				print("Here1")
				if 'edit_email' not in list:
					list.append('edit_email')
				if 'update_pass' in list:
					list.remove('update_pass')
				session.pop('edit_account', None)
				session['edit_account'] = list
			# if update email button pushed
			elif 'update_email' in request.form:
				# mark that the button pushed indicated updating email, not password
				if 'edit_email' not in list:
						return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, form2=form2)
				if 'update_pass' in list:
					list.remove('update_pass')
				error = None
				if not form.validate_on_submit():
					error = update_email(form, list)
				else:
					error = update_email(form, list)
				if error is not None:
					form.email.errors.append(error)
				if not form.email.errors:
					output = "Your email has been updated"
				else:
					print(form.email.errors)
					output = None
				return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, form2=form2, updated_email = output)
			elif 'cancel_update_email' in request.form:
				if 'edit_email' in list:
					list.remove('edit_email')
				elif 'update_email' in list:
					list.remove('update_email')
				session.pop('edit_account', None)
				session['edit_account'] = list
				return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, form2=form2)
			elif 'update_password' in request.form:
				if 'update_email' in list:
					list.remove('update_email')
				if('update_pass' not in list):
					list.append('update_pass')
				success = False
				if not form.validate_on_submit():
					success = update_password(form, list)
				else:
					success = update_password(form, list)
				if success:
					success = "Your password has been updated"
				else:
					success = None
				return render_template('my_account.html', edit = session['edit_account'], form=form, success = success, tags=my_tags, form2=form2)
			elif 'edit_tags' in request.form:
				return redirect(url_for('my_tags'))
			elif 'remove_account' in request.form:
				if 'remove_account' not in list:
					list.append('remove_account')
				session.pop('edit_account', None)
				session['edit_account']=list
				return render_template('my_account.html', edit = session['edit_account'], form=form, form2=form2, tags=my_tags)
			elif 'remove_account_final' in request.form:
				if('remove_account_final' not in list):
					list.append('remove_account_final')
				removal_success = False
				if not form2.validate_on_submit():
					removal_success = remove_account(form2, list)
				else:
					removal_success = remove_account(form2, list)
				if removal_success:
					removal_success = "Your account has been deleted"
					return redirect(url_for('home'))
				else:
					removal_success = None
				return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, removal_success = removal_success, form2=form2)
			elif 'cancel_remove_account' in request.form:
				if 'remove_account_final' in list:
					list.remove('remove_account_final')
				if 'remove_account' in list:
					list.remove('remove_account')
				return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, form2=form2)
			return render_template('my_account.html', edit = session['edit_account'], form=form, tags=my_tags, form2=form2)
		return render_template('my_account.html', edit = [], form = form, tags=my_tags, form2=form2)
#########################################################################################
# Other page routes
#########################################################################################


def demo_nltk(title, description, background, summary):
	testStr=[]
	testStr.append(title)
	testStr.append(description)
	testStr.append(background)
	testStr.append(summary)
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
			t = tag.lower()
			t = tag.capitalize()
			if len(t) > 50:
				continue
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

@app.route('/admin/users/<user>', methods=['GET', 'POST'])
@app.route('/admin/users', methods=['GET'])
def users(user=None):
	print(request.form)
	form = ApplicantForm(request.form, email=g.user.email)
	form2=AccountRemovalForm(request.form)
	if not g.user.admin:
		return redirect(url_for('home'))
	if user is not None:
		user = User.query.filter_by(user_id=user).first()
	if request.method == 'GET' and user is None:
		if 'edit_account' in session:
			session.pop('edit_account', None)
		users = get_table_users(request)
		return render_template('all_users.html', users = users[0], len = users[1], current_page=users[2])
	elif request.method == 'GET' and user is not None:
		projects = Project.query.filter_by(user=user.user_id).all()
		return render_template('user.html', user=user, form=form, form2=form2, projects=projects)
	if request.method == 'POST':
		print(request.form)
		projects = Project.query.filter_by(user=user.user_id).all()
		list = []
		if 'edit_account_admin' not in session:
			list = []
			session['edit_account_admin'] = []
		else:
			list = session['edit_account_admin']
			for t in list:
				print(t)
		if 'edit_email' in request.form:
			if 'edit_email' not in list:
				list.append('edit_email')
			if 'update_pass' in list:
				list.remove('update_pass')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
		# if update email button pushed
		elif 'update_email' in request.form:
			# mark that the button pushed indicated updating email, not password
			if 'edit_email' not in list:
					return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
			if 'update_pass' in list:
				list.remove('update_pass')
			error = None
			if not form.validate_on_submit():
				error = update_email_admin(form, list, user)
			else:
				error = update_email_admin(form, list, user)
			if error is not None:
				form.email.errors.append(error)
			if not form.email.errors:
				output = "The email has been updated"
			else:
				output = None
			return render_template('user.html', edit = session['edit_account_admin'], user=user, form=form, form2=form2, updated_email = output, project=projects)
		elif 'cancel_update_email' in request.form:
			if 'edit_email' in list:
				list.remove('edit_email')
			elif 'update_email' in list:
				list.remove('update_email')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
		elif 'update_password' in request.form:
			if 'update_email' in list:
				list.remove('update_email')
			if('update_pass' not in list):
				list.append('update_pass')
			success = False
			if not form.validate_on_submit():
				success = update_password_admin(form, list, user)
			else:
				success = update_password_admin(form, list, user)
			if success:
				success = "The users password has been updated"
			else:
				success = None
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, success = success, projects=projects, form2=form2)
		elif 'edit_rights' in request.form:
			if 'edit_rights' not in list:
				list.append('edit_rights')
			if 'update_rights' in list:
				list.remove('update_rights')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
		if 'update_rights' in request.form:
			# mark that the button pushed indicated updating email, not password
			if 'edit_rights' not in list:
				return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
			if 'update_pass' in list:
				list.remove('update_pass')
			if 'update_email' in list:
				list.remove('update_email')
			error = None
			rights = []
			if(request.form.get('admin')):
				rights.append("admin")
			if(request.form.get('provider')):
				rights.append('provider')
			error = update_rights_admin(form, list, user, rights)
			error = True
			for right in rights:
				print(right)
			if error is False:
				output = "There was an issue updating the users rights"
			if error is True:
				output = "The users rights have been updated"
			else:
				output = None
			return render_template('user.html', edit = session['edit_account_admin'], user=user, form=form, form2=form2, updated_rights = output, project=projects)
		elif 'cancel_update_rights' in request.form:
			if 'edit_rights' in list:
				list.remove('edit_rights')
			elif 'update_rights' in list:
				list.remove('update_rights')
			session.pop('edit_account_admin', None)
			session['edit_account_admin'] = list
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
		elif 'remove_account' in request.form:
			if 'remove_account' not in list:
				list.append('remove_account')
			session.pop('edit_account_admin', None)
			session['edit_account_admin']=list
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)
		elif 'remove_account_final' in request.form:
			uname = user.email
			if('remove_account_final' not in list):
				list.append('remove_account_final')
			removal_success = False
			if not form2.validate_on_submit():
				removal_success = remove_account_admin(form2, list, user)
			else:
				removal_success = remove_account_admin(form2, list, user)
			if removal_success:
				removal_success = "The account belonging to " + uname + " has been deleted"
				return redirect(url_for('users', user=None))
			else:
				removal_success = None
			return render_template('user.html', user=user, edit = session['edit_account_admin'], removal_success=removal_success, form=form, projects=projects, form2=form2)
		elif 'cancel_remove_account' in request.form:
			if 'remove_account_final' in list:
				list.remove('remove_account_final')
			if 'remove_account' in list:
				list.remove('remove_account')
			return render_template('user.html', user=user, edit = session['edit_account_admin'], form=form, projects=projects, form2=form2)#		return render_template('my_account.html', edit = session['edit_account_admin'], form=form, tags=my_tags, form2=form2)
#	return render_template('my_account.html', edit = [], form = form, email_errors = [], password_errors = [], tags=my_tags, form2=form2)


# The home page.
@app.route('/', methods=['GET', 'POST'])
def home():
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
			if 'edit_account' in session:
				session.pop('edit_account', None)
			if g.user.new_user:
				g.user.new_user = False
				db.session.commit()
				new_user=True
			error = "You are logged in"
			projects = get_table_page(request)
			records = ApplicantTags.query.filter_by(uid = g.user.user_id).all()
			s_projects = get_suggested_table(request,records)
			return render_template('home.html', new_user = new_user, my_projects=projects[0], len=projects[1], current_page=projects[2], suggested_projects = s_projects[0], len2=s_projects[1], current_page_suggested = s_projects[2])
		return render_template('home.html')
