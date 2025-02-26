from flask import Blueprint

admin_blueprint = Blueprint('admin', __name__)

from . import admin_routes  # This registers the endpoints with the blueprint
