from flask import Blueprint

frontend_blueprint = Blueprint('frontend', __name__)

from . import frontend_routes  # This will register all routes with the blueprint.
