# randonumba/__init__.py
from datetime import datetime
import os
import random
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import stripe

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(verbose=True, dotenv_path=os.path.join(BASE_DIR, '.env'))
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

DB_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'randonumba.sqlite'))

app = Flask(__name__)
app.config.update(
  SECRET_KEY=os.getenv('SECRET_KEY'),
  SQLALCHEMY_TRACK_MODIFICATIONS=False,
  SQLALCHEMY_DATABASE_URI=DB_URI
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_mgr = LoginManager(app)

#####################
# View Functions    #
#####################

@app.route('/')
def index():
    return render_template('index.html', stripe_pub_key=os.getenv('STRIPE_PUB_KEY'))

@app.route('/number', methods=('POST',))
def generate_number():
    purchase = None
    if current_user.is_authenticated:
        if current_user.credits < 1:
            # generate a purchase
            purchase = Purchase.make_purchase(
              request.form['stripeToken'],
              int(request.form['stripePurchaseAmount']),
              user_id=current_user.id
            )
            if purchase:
                current_user.credits += purchase.credits
        else:
            purchase = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.id.desc()).first()

    else:
        purchase = Purchase.make_purchase(request.form['stripeToken'], 100)

    if purchase:
        number = RandomNumber(value=random.randrange(1, 9), purchase_id=purchase.id)
        db.session.add(number)
        if current_user.is_authenticated:
            current_user.credits -= 1
        db.session.commit()
        print(f'Random Number Generated {number.value}')
        return render_template(
          'index.html',
          number=number.value,
          stripe_pub_key=os.getenv('STRIPE_PUB_KEY')
        )
    return redirect(url_for('.index'))

@app.route('/login')
def show_login():
    return render_template('login.html')

@app.route('/login', methods=('POST',))
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    # cutting some corners here ...
    # if email exists then try to authenticate
    if User.query.filter_by(email=email).count():
        user = User.authenticate(email, password)
        if not user:
            return redirect(url_for('.show_login'))

    # other wise just add (register) them to 
    # the system and authenticate them
    else:
        db.session.add(User(email=email, password=password))
        db.session.commit()
        User.authenticate(email, password)

    return redirect(url_for('.index'))

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('.index'))


#####################
# Data Model        #
#####################

@login_mgr.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    def __init__(self, email, password, credits=0, stripe_id=None):
        self.email = email
        self.password = generate_password_hash(password)
        self.credits = credits
        self.stripe_id = stripe_id

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, index=True, unique=True)
    password = db.Column(db.String)
    credits = db.Column(db.Integer)
    stripe_id = db.Column(db.String)
    purchases = db.relationship('Purchase', backref='user', lazy=True)

    @classmethod
    def authenticate(cls, email, password):
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return user
        return None

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credits = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stripe_id = db.Column(db.String)
    numbers = db.relationship('RandomNumber', backref='purchase', lazy=True)

    @classmethod
    def make_purchase(cls, stripe_token, stripe_amount, user_id=None):
        try:
            charge = stripe.Charge.create(
              amount=stripe_amount,
              currency='usd',
              description='Random Number Purchase',
              source=stripe_token
            )
            if charge.status != 'failed':
                purchase = Purchase(credits=stripe_amount // 100, stripe_id=charge.id, user_id=user_id)
                db.session.add(purchase)
                db.session.commit()
                return purchase
        except Exception as e:
            print(e)
        return None


class RandomNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
