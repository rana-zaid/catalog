#! /usr/bin/env python3

# Imports
from flask import Flask, render_template, request,\
        redirect, url_for, flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import User, Category, Item, Base
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import random
import requests
import datetime
import httplib2
import string
import json
from functools import wraps

# Flask instance
app = Flask(__name__)

# gconnect CLIENT_ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalog"

# Connect to database
engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine

# Create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Check If user Is logged in
def login_required(f):
    @wraps(f)
    def x(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return x


# Login page
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Google connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

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
    url = ('https://www.googleapis.com/oauth2/v2/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already\
                                            connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'
    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1 style="text-align:center">Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;\
                border-radius: 150px;-webkit-border-radius: 150px;\
                -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# Google disconnect
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/category')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Facebook connect
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("access token received %s " % access_token)
    app_id = json.loads(open('fb_client_secrets.json', 'r')
                        .read())['web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=\
            fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=\
            %s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server
        token exchange we have to split the token first on commas
        and select the first index which gives us the key : value
        for the server access token then we split it on colons to
        pull out the actual token value and replace the remaining
        quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,\
        id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s\
        &redirect=0&height=200&width=200' % token
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
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


# Facebook disconnect
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s'\
        % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


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
    except Exception:
        return None


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('allCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('allCategories'))


# JSON
@app.route('/catalog/JSON')
def allCategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])


# JSON
@app.route('/catalog/<path:category_name>/items/JSON')
def categoryItemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=category).all()
    return jsonify(Item=[i.serialize for i in items])


# Home page
@app.route('/')
@app.route('/catalog/')
def allCategories():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    for i in items:
        latestItems = session.query(Item).order_by(Item.date.desc())\
            .limit(6).all()
    if 'username' not in login_session:
        return render_template('public_home_page.html',
                               categories=categories,
                               items=items,
                               latestItems=latestItems)
    else:
        return render_template('home_page.html',
                               categories=categories,
                               items=items,
                               latestItems=latestItems)


# Add new category
@app.route('/catalog/category/new', methods=['GET', 'POST'])
@login_required
def newCategory():
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'],
            user_id=login_session['user_id']
            )
        session.add(newCategory)
        session.commit()
        flash('Category Successfully Added!')
        return redirect(url_for('allCategories'))
    else:
        return render_template('new_category.html')


# Edit category
@app.route('/catalog/<path:category_name>/items/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_name):
    categoryToEdit = session.query(Category).filter_by(
        name=category_name).one()
    # check if logged in user is the owner of category
    creator = getUserInfo(categoryToEdit.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user is not category owner
    if creator.id != login_session['user_id']:
        flash("Sorry!! You cannot edit this category.\
            It's %s's category" % creator.name)
        return redirect(url_for('allCategories'))
    if request.method == 'POST':
        categoryToEdit = Category(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(categoryToEdit)
        session.commit()
        flash('Category Successfully Edited!')
        return redirect(url_for('allCategories'))
    else:
        return render_template('edit_category.html',
                               category=categoryToEdit)


# Delete category
@app.route('/catalog/<path:category_name>/items/delete',
           methods=['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    categoryToDelete = session.query(Category).filter_by(
        name=category_name).one()
    # check if logged in user is the owner of category
    creator = getUserInfo(categoryToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user is not category owner
    if creator.id != login_session['user_id']:
        flash("Sorry!! You cannot delete this category. It's %s's category"
              % creator.name)
        return redirect(url_for('allCategories'))
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('Category Successfully Deleted!')
        return redirect(url_for('allCategories'))
    else:
        return render_template('delete_category.html',
                               category=categoryToDelete)


# View category items
@app.route('/catalog/<path:category_name>/items')
def categoryItems(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=category).all()
    counter = session.query(Item).filter_by(category=category).count()
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id !=\
            login_session['user_id']:
        return render_template('public_category_items.html',
                               category=category,
                               items=items,
                               counter=counter,
                               categories=categories)
    else:
        return render_template('category_items.html',
                               category=category,
                               items=items,
                               counter=counter,
                               categories=categories)


# View item details
@app.route('/catalog/<path:category_name>/<path:item_name>/')
def ItemDetails(category_name, item_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session or creator.id !=\
            login_session['user_id']:
        return render_template('public_item_details.html',
                               categories=categories,
                               item=item,
                               category=category_name,
                               creator=creator)
    else:
        return render_template('item_details.html',
                               categories=categories,
                               item=item,
                               category=category_name,
                               creator=creator)


# Add new item
@app.route('/catalog/item/new', methods=['GET', 'POST'])
@login_required
def newItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            author=request.form['author'],
            picture=request.form['picture'],
            date=datetime.datetime.now(),
            category=session.query(Category).filter_by(
                name=request.form['category']).one(),
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('Item Successfully Added!')
        return redirect(url_for('allCategories'))
    else:
        return render_template('new_item.html', categories=categories)


# Edit item
@app.route('/catalog/<path:category_name>/<path:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_name, item_name):
    category = session.query(Category).filter_by(
        name=category_name).one()
    itemToEdit = session.query(Item).filter_by(name=item_name).one()
    categories = session.query(Category).all()
    creator = getUserInfo(itemToEdit.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user is not item owner
    if creator.id != login_session['user_id']:
        flash("Sorry!! You cannot edit this item. It's %s's \
            item" % creator.name)
        return redirect(url_for('allCategories'))
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['author']:
            itemToEdit.author = request.form['author']
        if request.form['picture']:
            itemToEdit.picture = request.form['picture']
        if request.form['category']:
            category = session.query(Category).filter_by(
                name=request.form['category']).one()
            itemToEdit.category = category
            time = datetime.datetime.now()
            itemToEdit.date = time
            session.add(itemToEdit)
        session.commit()
        flash('Item Successfully Edited!')
        return redirect(url_for('categoryItems',
                                category_name=itemToEdit.category.name))
    else:
        return render_template('edit_item.html',
                               category=category,
                               categories=categories,
                               item=itemToEdit)


# Delete item
@app.route('/catalog/<path:category_name>/<path:item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_name, item_name):
    category = session.query(Category).filter_by(
        name=category_name).one()
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    # check if logged in user is the owner of item
    creator = getUserInfo(itemToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user is not item owner
    if creator.id != login_session['user_id']:
        flash("Sorry!! You cannot delete this item. It's %s's\
            item" % creator.name)
        return redirect(url_for('allCategories'))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted!')
        return redirect(url_for('categoryItems',
                                category_name=category.name))
    else:
        return render_template('delete_item.html',
                               item=itemToDelete)


# Main method
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
