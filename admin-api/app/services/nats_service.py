import asyncio
import json
from datetime import datetime
from nats.aio.client import Client as NATS
from flask import current_app
from app.extensions import db
from app.models.book import Book
from app.models.borrow_record import BorrowRecord
from app.models.user import User
from app.services.background import bg_loop

nc = NATS()
js = None

async def connect_jetstream():
    global js
    try:
        await nc.connect("nats://localhost:4222")
        js = nc.jetstream()
        print("Connected to NATS JetStream")
    except Exception as e:
        print(f"Error connecting to NATS: {e}")

    # Delete any existing durable consumer for borrowed events
    # try:
    #     await js.delete_consumer("BOOKS", "admin-durable")
    #     print("Deleted existing consumer 'admin-durable'")
    # except Exception as e:
    #     print("No existing 'admin-durable' consumer to delete or error:", e)

    # Purge the stream to clear out old messages (if needed)
    # try:
    #     await js.purge_stream("BOOKS")
    #     print("Purged stream BOOKS")
    # except Exception as e:
    #     print("Error purging stream BOOKS:", e)

    # Ensure the stream exists
    try:
        await js.stream_info("BOOKS")
    except Exception as e:
        print("Stream BOOKS not found, creating it.")
        await js.add_stream(name="BOOKS", subjects=["books.*"])

async def publish_book_update(event_type, book):
    data = {
        "event": event_type,
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher,
            "category": book.category,
            "is_borrowed": book.is_borrowed,
            "due_date": book.due_date.isoformat() if book.due_date else None
        }
    }
    await js.publish("books.updates", json.dumps(data).encode())
    print(f"Published book update: {data}")

async def subscribe_enroll_user(app):
    async def message_handler(msg):
        with app.app_context():
            data = json.loads(msg.data.decode())
            print(f"Received message: {data}")
            user_data = data.get("data")
            if not user_data:
                print("Enroll User event received without user data.")
                return
            if data.get("event") == "enroll_user":
                
                # Record the borrow event
                record = User(
                    id= user_data["id"],
                    firstname=user_data["firstname"],
                    lastname=user_data["lastname"],
                    email=user_data["email"]
                )
                db.session.add(record)
                db.session.commit()

            print(f"Received message on subject {msg.subject}: {msg.data.decode()}")
        await msg.ack()

    await js.subscribe("books.enroll_user", durable="admin-durable-enroll", cb=message_handler)
    print("Subscribed to books.enroll_user, and listening for user events")

async def subscribe_borrowed(app):
    async def message_handler(msg):
        with app.app_context():
            data = json.loads(msg.data.decode())
            print(f"Received message: {data}")
            borrow_data = data.get("data")
            if not borrow_data:
                print("Borrowed event received without book data.")
                return
            if data.get("event") == "borrowed":
                book_id = borrow_data["book_id"]
                user_id = borrow_data["user_id"]
                borrow_days = int(borrow_data["borrow_days"])
                borrow_date = borrow_data["borrow_date"]
                due_date_str = borrow_data["due_date"]

                book = Book.query.get(book_id)
                if book:
                    book.is_borrowed = True
                    book.due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
                    db.session.commit()

                # Record the borrow event
                record = BorrowRecord(
                    id=borrow_data["id"],
                    user_id=user_id, 
                    book_id=book_id,
                    borrow_date=datetime.fromisoformat(borrow_date),
                    borrow_days=borrow_days,
                    due_date=datetime.fromisoformat(due_date_str) if due_date_str else None
                )
                db.session.add(record)
                db.session.commit()

                # Publish an update about the changed book
                asyncio.run_coroutine_threadsafe(publish_book_update("updated", book), bg_loop)
            print(f"Received message on subject {msg.subject}: {msg.data.decode()}")
        await msg.ack()

    await js.subscribe("books.borrowed", durable="admin-durable-borrowed", cb=message_handler)
    print("Subscribed to books.borrowed, and listening for borrowed events")

async def setup_nats(app):
    await connect_jetstream()
    await subscribe_borrowed(app),
    await subscribe_enroll_user(app)
