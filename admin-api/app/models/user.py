from app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    firstname = db.Column(db.String(120))
    lastname = db.Column(db.String(120))
