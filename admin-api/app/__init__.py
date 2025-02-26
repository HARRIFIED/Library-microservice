from flask import Flask
from .config import Config
from .extensions import db
from .routes import admin_blueprint
from .services.background import bg_loop, start_background_loop
from .services.nats_service import setup_nats
from threading import Thread
import asyncio

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(admin_blueprint, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()

    # Start background event loop in a separate thread
    thread = Thread(target=start_background_loop, args=(bg_loop,), daemon=True)
    thread.start()

    # Schedule NATS setup on the background loop
    asyncio.run_coroutine_threadsafe(setup_nats(app), bg_loop)

    return app
