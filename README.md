# stripe-flask-randonumba-minimal

This is a dummy application that generates random numbers and was used for demonstrating how to implement Stripe payment processing for credit card purchases in a Python web application.

### Dependencies

* Flask 1.0
* Flask-Login 0.4
* python-dotenv 0.10
* Flask-Migrate 2.4
* Flask-SQLAlchemy 2.3
* stripe 2.23

### Tags

There are three tags for this application which demonstrate three different levels of functionality

* 0.0.1 - simply the basic application which will generate random numbers and has no Stripe intregration 
* 0.0.2 - provides the ability for one off purchase by generating a Stripe charge using the stock Stripe checkout button
* 0.0.3 - utilizes custom JQuery / JavaScript to control Stripe checkout and provides the ability for one off purchase by generating Stripe charges for one time buys or purchasing of credits for authenticated users
