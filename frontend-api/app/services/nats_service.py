import asyncio
import json
import datetime
from nats.aio.client import Client as NATS
from app.extensions import db
from app.models.book import Book
from app.models.borrow_record import BorrowRecord

nc = NATS()
js = None  # JetStream context

async def connect_jetstream():
    global js
    try:
        await nc.connect("nats://nats-server:4222")
        js = nc.jetstream()
        print("Connected to NATS JetStream")
    except Exception as e:
        print(f"Error connecting to NATS: {e}")

    # Ensure the stream exists; if not, create it for subjects "books.*"
    try:
        await js.stream_info("BOOKS")
    except Exception as e:
        print("Stream BOOKS not found, creating it.")
        await js.add_stream(name="BOOKS", subjects=["books.*"])

async def publish_book_Borrowed(event_type, record):
    """
    Publish a book borrow event on the 'books.borrowed' JetStream subject.
    """
    data = {
        "event": event_type,
        "data": {
            "id": record.id,
            "book_id": record.book_id,
            "user_id": record.user_id,
            "borrow_days": record.borrow_days,
            "borrow_date": record.borrow_date.isoformat(),
            "due_date": record.due_date.isoformat()
        }
    }
    try:
        await js.publish("books.borrowed", json.dumps(data).encode())
        print(f"Published book borrowed: {data}")
    except Exception as e:
        print(f"Failed to publish borrowed data: {e}")

async def publish_enroll_user(event_type, record):
    """
    Publish a book borrow event on the 'books.borrowed' JetStream subject.
    """
    data = {
        "event": event_type,
        "data": {
            "id": record.id,
            "firstname": record.firstname,
            "lastname": record.lastname,
            "email": record.email,
        }
    }
    try:
        await js.publish("books.enroll_user", json.dumps(data).encode())
        print(f"Published enroll user: {data}")
    except Exception as e:
        print(f"Failed to publish enroll_user data: {e}")

async def subscribe_books_updates(app):
    async def message_handler(msg):
        with app.app_context():
            data = json.loads(msg.data.decode())
            print(f"Received message: {data}")
            event = data.get("event")
            book_data = data.get("book")
            if event == "added":
                if not Book.query.get(book_data["id"]):
                    book = Book(
                        id=book_data["id"],
                        title=book_data["title"],
                        author=book_data["author"],
                        publisher=book_data["publisher"],
                        category=book_data["category"],
                        is_available=not book_data.get("is_borrowed", False),
                        due_date=datetime.datetime.fromisoformat(book_data["due_date"]) 
                            if book_data.get("due_date") else None
                    )
                    db.session.add(book)
                    db.session.commit()
            elif event == "removed":
                book = Book.query.get(book_data["id"])
                if book:
                    db.session.delete(book)
                    db.session.commit()
            elif event == "updated":
                book = Book.query.get(book_data["id"])
                if book:
                    book.title = book_data["title"]
                    book.author = book_data["author"]
                    book.publisher = book_data["publisher"]
                    book.category = book_data["category"]
                    book.is_available = not book_data.get("is_borrowed", False)
                    book.due_date = (datetime.datetime.fromisoformat(book_data["due_date"]) 
                                     if book_data.get("due_date") else None)
                    db.session.commit()
            print(f"Received message on subject {msg.subject}: {msg.data.decode()}")
        await msg.ack()

    # Subscribe to the 'books.updates' subject using a durable consumer.
    await js.subscribe("books.updates", durable="frontend-durable-book-updates", cb=message_handler)
    print("Subscribed to 'books.updates' and listening indefinitely.")

async def setup_nats(app):
    await connect_jetstream()
    await subscribe_books_updates(app)
