from flask import request, jsonify
from datetime import datetime
import asyncio
from app.extensions import db
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord
from app.services.nats_service import publish_book_update
from app.services.background import bg_loop
from . import admin_blueprint

@admin_blueprint.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    publisher = data.get('publisher')
    category = data.get('category')
    if not all([title, author, publisher, category]):
        return jsonify({"error": "Missing fields"}), 400

    book = Book(title=title, author=author, publisher=publisher, category=category)
    db.session.add(book)
    db.session.commit()

    # Schedule publish_book_update on the background loop
    asyncio.run_coroutine_threadsafe(publish_book_update("added", book), bg_loop)
    print("Book added")
    return jsonify({
        "message": "Book added",
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher,
            "category": book.category
        }
    }), 201

@admin_blueprint.route('/books', methods=['GET'])
def list_books():
    books = Book.query.all()
    books_data = [{
         "id": book.id,
         "title": book.title,
         "author": book.author,
         "publisher": book.publisher,
         "category": book.category
    } for book in books]
    return jsonify(books_data), 200

@admin_blueprint.route('/books/<int:book_id>', methods=['DELETE'])
def remove_book(book_id):
    book = Book.query.get(book_id)
    if not book:
         return jsonify({"error": "Book not found"}), 404
    db.session.delete(book)
    db.session.commit()
    asyncio.run_coroutine_threadsafe(publish_book_update("removed", book), bg_loop)
    return jsonify({"message": "Book removed"}), 200

@admin_blueprint.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    users_data = [{
         "id": user.id,
         "email": user.email,
         "firstname": user.firstname,
         "lastname": user.lastname
    } for user in users]
    return jsonify(users_data), 200

@admin_blueprint.route('/users_borrowed', methods=['GET'])
def list_users_borrowed():
    records = BorrowRecord.query.all()
    result = []
    for rec in records:
         user = User.query.get(rec.user_id)
         book = Book.query.get(rec.book_id)
         result.append({
              "user": {
                  "id": user.id,
                  "email": user.email,
                  "firstname": user.firstname,
                  "lastname": user.lastname,
              },
              "book": {
                  "id": book.id,
                  "title": book.title,
                  "author": book.author,
              },
              "borrow_date": rec.borrow_date.isoformat(),
              "borrow_days": rec.borrow_days,
              "due_date": rec.due_date.isoformat()
         })
    return jsonify(result), 200

@admin_blueprint.route('/books/unavailable', methods=['GET'])
def list_unavailable_books():
    books = Book.query.filter_by(is_borrowed=True).all()
    books_data = [{
         "id": book.id,
         "title": book.title,
         "author": book.author,
         "due_date": book.due_date.isoformat() if book.due_date else None
    } for book in books]
    return jsonify(books_data), 200
