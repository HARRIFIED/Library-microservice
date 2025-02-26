from app.extensions import db

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    author = db.Column(db.String(120))
    publisher = db.Column(db.String(120))
    category = db.Column(db.String(120))
    is_available = db.Column(db.Boolean, default=True)
    due_date = db.Column(db.DateTime, nullable=True)
