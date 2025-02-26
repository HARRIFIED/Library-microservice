from app.extensions import db

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    book_id = db.Column(db.Integer)
    borrow_date = db.Column(db.DateTime)
    borrow_days = db.Column(db.Integer)
    due_date = db.Column(db.DateTime)
