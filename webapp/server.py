# webapp/server.py

from randonumba import app, db, User, Purchase, RandomNumber

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Purchase': Purchase, 'RandomNumber': RandomNumber}

