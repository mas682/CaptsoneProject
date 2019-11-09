from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
import os

app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'flask key'
POSTGRES = {
    'user': 'postgres',
    'pw': 'password',
    'db': 'capstone',
    'host': 'localhost',
    'port': '5432',
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

#postgresql://postgres:password@localhost:5432/capstone
#SQLALCHEMY_DATABASE_URI = 'postgresql:///' + os.path.join(app.root_path, 'library.db')
#'postgresql://%(user)s:\%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(__name__)
