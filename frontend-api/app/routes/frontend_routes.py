import datetime
import asyncio
from flask import request, jsonify
from app.extensions import db
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord
from app.services.nats_service import publish_book_Borrowed
from app.services.background import bg_loop
from . import frontend_blueprint

@frontend_blueprint.route('/users', methods=['POST'])
def enroll_user():
    data = request.get_json()
    email = data.get("email")
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    if not all([email, firstname, lastname]):
         return jsonify({"error": "Missing fields"}), 400
    user = User(email=email, firstname=firstname, lastname=lastname)
    db.session.add(user)
    db.session.commit()
    return jsonify({
         "message": "User enrolled",
         "user": {"id": user.id, "email": user.email,
                  "firstname": user.firstname, "lastname": user.lastname}
    }), 201

@frontend_blueprint.route('/books', methods=['GET'])
def list_books():
    publisher = request.args.get("publisher")
    category = request.args.get("category")
    query = Book.query.filter_by(is_available=True)
    if publisher:
         query = query.filter_by(publisher=publisher)
    if category:
         query = query.filter_by(category=category)
    books = query.all()
    books_data = [{
         "id": book.id,
         "title": book.title,
         "author": book.author,
         "publisher": book.publisher,
         "category": book.category
    } for book in books]
    return jsonify(books_data), 200

@frontend_blueprint.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book or not book.is_available:
         return jsonify({"error": "Book not found or not available"}), 404
    return jsonify({
         "id": book.id,
         "title": book.title,
         "author": book.author,
         "publisher": book.publisher,
         "category": book.category
    }), 200

@frontend_blueprint.route('/books/<int:book_id>/borrow', methods=['POST'])
def borrow_book(book_id):
    data = request.get_json()
    days = data.get("days")
    user_id = data.get("user_id")
    if not days:
         return jsonify({"error": "Borrow duration (days) required"}), 400
    book = Book.query.get(book_id)
    if not book or not book.is_available:
         return jsonify({"error": "Book not available"}), 404
    if not user_id:
         return jsonify({"error": "User ID required to borrow book"}), 400

    # Mark the book as borrowed locally.
    book.is_available = False
    borrow_date = datetime.datetime.utcnow()
    due_date = borrow_date + datetime.timedelta(days=int(days))
    book.due_date = due_date

    record = BorrowRecord(
        user_id=user_id, 
        book_id=book_id, 
        borrow_days=int(days), 
        borrow_date=borrow_date,
        due_date=due_date
    )
    db.session.add(record)
    db.session.commit()

    # Publish a borrow event on the "books.borrowed" subject.
    asyncio.run_coroutine_threadsafe(publish_book_Borrowed("borrowed", record), bg_loop)
    return jsonify({"message": "Book borrowed", "data" : {
           "id": record.id,
           "user_id": user_id,
           "book_id": book_id,
           "borrow_date": borrow_date.isoformat(),
           "borrow_days": days,
           "due_date": due_date.isoformat()
    }}), 200
