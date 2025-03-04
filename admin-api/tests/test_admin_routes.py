import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from app import create_app, db
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord

# Test configuration using an in-memory SQLite database
class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class AdminRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Patch publish_book_update in the module where it is imported in your routes.
        self.publish_patch = patch(
            'app.routes.admin_routes.publish_book_update',  # adjust this to your actual module path
            new=AsyncMock(return_value=None)
        )
        self.mock_publish = self.publish_patch.start()

        # Patch asyncio.run_coroutine_threadsafe to avoid scheduling on the real bg_loop.
        self.run_coroutine_patch = patch(
            'asyncio.run_coroutine_threadsafe',
            new=MagicMock(return_value=MagicMock())
        )
        self.mock_run_coroutine = self.run_coroutine_patch.start()

    def tearDown(self):
        self.publish_patch.stop()
        self.run_coroutine_patch.stop()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_book(self):
        payload = {
            "title": "Test Book",
            "author": "Test Author",
            "publisher": "Test Publisher",
            "category": "Test Category"
        }
        response = self.client.post(
            '/api/admin/books',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("book", data)
        self.assertEqual(data["book"]["title"], "Test Book")
        # Verify book is in the database
        book = Book.query.filter_by(title="Test Book").first()
        self.assertIsNotNone(book)

        def test_list_books(self):
            book = Book(title="List Book", author="Author", publisher="Publisher", category="Category")
            db.session.add(book)
            db.session.commit()
            response = self.client.get('/api/admin/books')
            self.assertEqual(response.status_code, 200)
            books = json.loads(response.data)
            self.assertIsInstance(books, list)
            self.assertGreaterEqual(len(books), 1)

    # def test_remove_book(self):
    #     book = Book(title="Remove Book", author="Author", publisher="Publisher", category="Category")
    #     db.session.add(book)
    #     db.session.commit()
    #     book_id = book.id

    #     response = self.client.delete(f'/api/admin/books/{book_id}')
    #     self.assertEqual(response.status_code, 200)
    #     removed_book = Book.query.get(book_id)
    #     self.assertIsNone(removed_book)

    def test_list_users(self):
        user = User(email="test@example.com", firstname="Test", lastname="User")
        db.session.add(user)
        db.session.commit()
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, 200)
        users = json.loads(response.data)
        self.assertIsInstance(users, list)
        self.assertGreaterEqual(len(users), 1)

    def test_list_users_borrowed(self):
        user = User(email="borrow@example.com", firstname="Borrow", lastname="User")
        book = Book(title="Borrowed Book", author="Author", publisher="Publisher", category="Category")
        db.session.add_all([user, book])
        db.session.commit()

        borrow_date = datetime.utcnow()
        due_date = borrow_date + timedelta(days=7)
        record = BorrowRecord(
            user_id=user.id,
            book_id=book.id,
            borrow_date=borrow_date,
            borrow_days=7,
            due_date=due_date
        )
        db.session.add(record)
        db.session.commit()

        response = self.client.get('/api/admin/users_borrowed')
        self.assertEqual(response.status_code, 200)
        records = json.loads(response.data)
        self.assertIsInstance(records, list)
        self.assertGreaterEqual(len(records), 1)

    def test_list_unavailable_books(self):
        book = Book(
            title="Unavailable Book",
            author="Author",
            publisher="Publisher",
            category="Category",
            is_borrowed=True,
            due_date=datetime.utcnow()
        )
        db.session.add(book)
        db.session.commit()
        response = self.client.get('/api/admin/books/unavailable')
        self.assertEqual(response.status_code, 200)
        books = json.loads(response.data)
        self.assertIsInstance(books, list)
        self.assertGreaterEqual(len(books), 1)

if __name__ == '__main__':
    unittest.main()
