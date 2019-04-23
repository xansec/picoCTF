"""picoCTF API v1 app."""

from flask import Blueprint, jsonify
from flask_restplus import Api

from api.common import PicoException

from .achievements import ns as achievements_ns

blueprint = Blueprint('api', __name__)
api = Api(
    app=blueprint,
    title='picoCTF API',
    version='1.0',
)

api.add_namespace(achievements_ns)


@api.errorhandler(PicoException)
def handle_pico_exception(e):
    """Handle exceptions."""
    response = jsonify(e.to_dict())
    response.status_code = 203
    return response
