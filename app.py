from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # Hashing boi 
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from datetime import datetime
import json
import random


import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np


# God of flask https://www.youtube.com/watch?v=8aTnmsDMldY&list=RDCMUC-QDfvrRIDB6F0bIO4I4HkQ&start_radio=1&rv=8aTnmsDMldY&t=144

## #Create the database and app
db_name = 'database.db'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name # 3 / is a relative path (4 absolute)

### Login manager stuff and bootstrap
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):  # Connects flask login and the database itself.
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    ## Checks whether they're a user or not with security measures - SHA256
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() # Get the first result that comes from quering the user table.
        if user:
            if check_password_hash(user.password, form.password.data): # Checks if their input hash is the same as the password hash.
                login_user(user, remember=form.remember.data) # Log them in 
                return redirect(url_for('dashboard')) # Move them to the dashboard page

        return '<h1>Invalid username or password</h1> Return to <a href="/"> home </a>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    # Registers account and hashes password with SHA256.
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256') # Hashes the password so that the database only holds hashed passwords.

        # Shove the user into the db and save it via SQLAlchemy magic
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>, <a href="/"> Return to index page. </a>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)


@app.route('/dashboard')
@login_required # Only give people with logins access to dashboard (which has the 'sensitive' data)
def dashboard():
        ##### Bureau of Meteorology Data
    redcliffe_data = [[], [], []] # Temp, humidity, time. # WE put stuff here because if it was outside, it'd keep adding the same data every time you refresh  home.
    uri = "http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.95591.json"
    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
       return "Connection Error"  
    Jresponse = uResponse.text
    data = json.loads(Jresponse)
    redcliffe_hum = data["observations"]["data"][0]["rel_hum"]
    redcliffe_temp = data["observations"]["data"][0]["air_temp"]
    redcliffe_time = data["observations"]["data"][0]["local_date_time_full"]
    redcliffe_time = datetime.strptime(redcliffe_time, "%Y%m%d%H%M%S")
    useful_data = data['observations']['data']
    string = ""
    # Loops through all the most recent updates from the json (last time I checked, there were like 143 of em).
    for i in range(len(useful_data)):
        humi = str(useful_data[i]["rel_hum"])
        temp = str(useful_data[i]["air_temp"])
        time = str(datetime.strptime(useful_data[i]["local_date_time_full"], "%Y%m%d%H%M%S"))
        # Appends the data to a list.
        redcliffe_data[0].append(humi)
        redcliffe_data[1].append(temp)
        redcliffe_data[2].append(time)


    temp = create_graph_good(redcliffe_data, 'temperature')
    humidity = create_graph_good(redcliffe_data, 'humidity')
    return render_template('dashboard.html', tempplot=temp, humidityplot = humidity, data = redcliffe_data, name=current_user.username, table_name = "BOM Weather Data") # PLOT=BAR IS SUS STUFF.


@app.route('/dashboard/pi_data')
@login_required # Only give people with logins access to dashboard (which has the 'sensitive' data)
def dashboard_pi():
    # Getting the time 
    uri = "http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.95591.json"
    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
       return "Connection Error"  
    Jresponse = uResponse.text
    data = json.loads(Jresponse)
    useful_data = data['observations']['data']

    ## Chungus Raspberry Pi data (not randomly generated btw)
    pi_data = [[], [], []] # Temp, humidity, time. # WE put stuff here because if it was outside, it'd keep adding the same data every time you refresh  home.
    for i in range(len(useful_data)):
        ## Setting up the real redcliffe data so we can fake it better.
        humi = useful_data[i]["rel_hum"]
        temp = useful_data[i]["air_temp"]
 
        ## Faking the data
        pi_hum = str(random.randrange(humi-5, humi+5)) # Gets random integer with a +- error margin on the real one (so it doesn't just graph randomness)
        pi_temp = str(round(random.uniform(temp-0.5,temp+1), 1)) # Gets a random float error margin thing yes.
        pi_time = str(datetime.strptime(useful_data[i]["local_date_time_full"], "%Y%m%d%H%M%S")) # Same time because lol 
        pi_data[0].append(pi_hum)
        pi_data[1].append(pi_temp)
        pi_data[2].append(pi_time)
    

    temp = create_graph_good(pi_data, 'temperature')
    humidity = create_graph_good(pi_data, 'humidity')
    return render_template('dashboard.html',  tempplot=temp, humidityplot = humidity, data = pi_data, name=current_user.username, table_name = "Raspberry Pi Weather Data")

##### Helper functions
# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# def create_plot(feature): Was testing how plotly worked
#     if feature == 'Bar':
#         N = 40
#         x = np.linspace(0, 1, N)
#         y = np.random.randn(N)
#         df = pd.DataFrame({'x': x, 'y': y}) # creating a sample dataframe
#         data = [
#             go.Bar(
#                 x=df['x'], # assign x as the dataframe column 'x'
#                 y=df['y']
#             )
#         ]
#     else:
#         N = 1000
#         random_x = np.random.randn(N)
#         random_y = np.random.randn(N)

#         # Create a trace
#         data = [go.Scatter(
#             x = random_x,
#             y = random_y,
#             mode = 'markers'
#         )]


#     graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

#     return graphJSON

def create_graph_good(data, output_type):
    """ Creates a graph. Data is in [[humidity...,], [temp], [time]] format
    Output_type is just whether you want a temp / humidity data set, it's a bad name I know."""
    humidity = data[0]
    temperature = data[1]
    date = data[2]
    weather_df = pd.DataFrame({'Humidity': humidity, 'Temperature': temperature, 'Date': date})

    if output_type == 'temperature':
        data = [go.Scatter(
            x=weather_df['Date'],
            y=weather_df['Temperature'],
            

        )]
    else:
        data = [go.Scatter(
            x=weather_df['Date'],
            y=weather_df['Humidity'],

        )]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


# @app.route('/bar', methods=['GET', 'POST'])
# def change_features():

#     feature = request.args['selected']
#     graphJSON= create_plot(feature)

#     return graphJSON



if __name__ == '__main__':
    app.run()
