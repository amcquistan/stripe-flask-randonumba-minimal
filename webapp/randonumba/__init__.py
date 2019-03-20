# randonumba/__init__.py
from datetime import datetime
import os
import random
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import stripe

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(verbose=True, dotenv_path=os.path.join(BASE_DIR, '.env'))
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

app = Flask(__name__)
app.config.update(
  SQLALCHEMY_TRACK_MODIFICATIONS=False,
  SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(BASE_DIR, 'randonumba.sqlite')
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#####################
# View Functions    #
#####################

@app.route('/')
def index():
    return render_template('index.html', stripe_pub_key=os.getenv('STRIPE_PUB_KEY'))

@app.route('/number', methods=('POST',))
def generate_number():
    import pdb; pdb.set_trace()
    purchase = Purchase.make_anonymous_purchase(
      request.form['stripeToken'],
      'Random Number Purchase'
    )
    if purchase:
        number = RandomNumber(value=random.randrange(0, 9), purchase_id=purchase.id)
        db.session.add(number)
        db.session.commit()
        return render_template(
          'index.html',
          number=number.value,
          stripe_pub_key=os.getenv('STRIPE_PUB_KEY')
        )
    return redirect(url_for('.index'))

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

    @classmethod
    def make_anonymous_purchase(cls, stripe_token, description):
        try:
            charge = stripe.Charge.create(amount=100, currency='usd', description=description, source=stripe_token)
            if charge.status != 'failed':
                purchase = Purchase(credits=1, stripe_id=charge.id)
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
