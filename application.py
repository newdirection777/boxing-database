from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Boxer, Base, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///boxing.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
	"""Show the login page"""
	
	# Create anti-forgery state token
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
					for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	"""Handle facebook logins"""
	
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data

	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(
		open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
		app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# Use token to get user info from API
	userinfo_url = "https://graph.facebook.com/v2.5/me"
	# strip expire tag from access token
	token = result.split("&")[0]


	url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data["name"]
	login_session['email'] = data["email"]
	login_session['facebook_id'] = data["id"]

	# The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token

	# Get user picture
	url = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data["data"]["url"]

	# see if user exists
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['email']

	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

	return output


# @app.route('/fbdisconnect')
def fbdisconnect():
	"""Log out of facebook"""
	
	facebook_id = login_session['facebook_id']
	
	# The access token must be included to successfully logout
	access_token = login_session['access_token']
	
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	
	return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
	"""Handle google login"""
	
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		   % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	# ADD PROVIDER TO LOGIN SESSION
	login_session['provider'] = 'google'

	# see if user exists, if it doesn't make a new one
	user_id = getUserID(data["email"])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['email']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

	return output

	
	
# User Helper Functions

def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session[
				   'email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

		
		
# DISCONNECT - Revoke a current user's token and reset their login_session

# @app.route('/gdisconnect')
def gdisconnect():
	"""Log out of google"""
	
	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(
			json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	if result['status'] != '200':
		# For whatever reason, the given token was invalid.
		response = make_response(
			json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response




@app.route('/')
@app.route('/categories/')
def HomePage():
	"""Show the home page"""
	
	categories = session.query(Category)
	
	# Show the 5 most recently added boxers
	lim = 5
	boxers = session.query(Boxer).order_by(Boxer.id.desc()).limit(lim)
	
	return render_template('homepage.html', categories=categories, boxers=boxers)
	
	
	

@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/boxers/')
def CategoryBoxers(category_id):
	"""Show the boxers belonging to a specific category"""
	
	category = session.query(Category).filter_by(id=category_id).one()

	boxers = session.query(Boxer).filter_by(category_id=category.id)
	
	if 'username' not in login_session:
		return render_template('publiccategoryboxers.html', category = category, boxers = boxers)
	else:
		return render_template('categoryboxers.html', category = category, boxers = boxers)



@app.route('/categories/<int:category_id>/<int:boxer_id>/')
def BoxerInfo(category_id, boxer_id):
	"""Show the details for a specific boxer
	
	Args:
		category_id: id of the category to which the boxer belongs.
		boxer_id: boxer's id number.
	"""
	
	boxer = session.query(Boxer).filter_by(id=boxer_id).one()
	
	creator = getUserInfo(boxer.user_id)
	
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicboxerinfo.html', boxer=boxer)
	else:
		return render_template('boxerinfo.html', boxer=boxer)
	
	

@app.route('/categories/<int:category_id>/addboxer/', methods = ['GET', 'POST'])
def AddBoxer(category_id):
	"""Add a new boxer to the category identified by category_id"""
	
	if 'username' not in login_session:
		return redirect('/login')

	if request.method == 'POST':
		newBoxer = Boxer(name=request.form['name'], description=request.form['description'], category_id=category_id, user_id=login_session['user_id'])
		session.add(newBoxer)
		session.commit()
		return redirect(url_for('CategoryBoxers', category_id=category_id))
	else:
		category = session.query(Category).filter_by(id = category_id).one()
		return render_template('addboxer.html', category=category)

		
	
	
@app.route('/categories/<int:category_id>/<int:boxer_id>/edit/', methods = ['GET', 'POST'])
def EditBoxer(category_id, boxer_id):
	"""Edit boxer's info.
	
	Args: 
		category_id: category that the boxer belongs to.
		boxer_id:  id number of the boxer to edit.
	"""
	
	if 'username' not in login_session:
		return redirect('/login')
		
	boxer = session.query(Boxer).filter_by(id = boxer_id).one()
		
	if boxer.user_id != login_session['user_id']:
		return "Permission Denied"
	
	if request.method == 'POST':
		if request.form['name']:
			boxer.name = request.form['name']
		if request.form['description']:
			boxer.description = request.form['description']
		session.commit()
		return redirect(url_for('CategoryBoxers', category_id = category_id))
	else:
		return render_template('editboxer.html', boxer=boxer)

	
	

@app.route('/categories/<int:category_id>/<int:boxer_id>/delete/', methods = ['GET', 'POST'])
def DeleteBoxer(category_id, boxer_id):
	"""Delete boxer from database.
	
	Args: 
		category_id: category that the boxer belongs to.
		boxer_id:  id number of the boxer to delete.
	"""
	
	if 'username' not in login_session:
		return redirect('/login')
		
	boxer = session.query(Boxer).filter_by(id = boxer_id).one()
		
	if boxer.user_id != login_session['user_id']:
		return "Permission Denied"
	
	if request.method == 'POST':
		session.delete(boxer)
		session.commit()
		return redirect(url_for('CategoryBoxers', category_id = category_id))
	else:
		return render_template('deleteboxer.html', boxer=boxer)
		
		
		

# API endpoint for GET 
@app.route('/JSON/')
@app.route('/categories/JSON/')
def HomePageJSON():
	categories = session.query(Category)
	return jsonify(Categories = [c.serialize for c in categories])



@app.route('/disconnect')
def disconnect():
	"""Handle user logout based on provider"""

	# google_login is a flag used to trigger a command
	# for logging out of google
	google_login = False
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			google_login = True
			gdisconnect()
			del login_session['gplus_id']
			del login_session['credentials']
			
		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
			del login_session['access_token']
		
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']
		
		# remove state
		del login_session['state']
		
		if google_login:
			return redirect("https://www.google.com/accounts/Logout?continue=https://appengine.google.com/_ah/logout?continue=http://localhost:5000")
		return redirect(url_for('HomePage'))
	else:
		print 'provider is undefined'
		print "You were not logged in"
		print 'redirecting to homepage'
		return redirect(url_for('HomePage'))


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = False
	app.run(host='0.0.0.0', port=5000)