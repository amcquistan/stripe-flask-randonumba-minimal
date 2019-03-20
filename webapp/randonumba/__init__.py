# randonumba/__init__.py
from datetime import datetime
import os
import random
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(verbose=True, dotenv_path=os.path.join(BASE_DIR, '.env'))

DB_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'randonumba.sqlite'))

app = Flask(__name__)
app.config.update(
  SQLALCHEMY_TRACK_MODIFICATIONS=False,
  SQLALCHEMY_DATABASE_URI=DB_URI
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#####################
# View Functions    #
#####################

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/number', methods=('POST',))
def generate_number():
    number = random.randrange(0, 9)
    return render_template('index.html', number=number)

#####################
# Data Model        #
#####################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, index=True, unique=True)
    password = db.Column(db.String)
    credits = db.Column(db.Integer)
    stripe_id = db.Column(db.String)
    purchases = db.relationship('Purchase', backref='user', lazy=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credits = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stripe_id = db.Column(db.String)
    numbers = db.relationship('RandomNumber', backref='purchase', lazy=True)

class RandomNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
