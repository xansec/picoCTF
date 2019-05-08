"""picoCTF API v1 app."""

from flask import Blueprint, jsonify
from flask_restplus import Api

from api.common import PicoException

from .achievements import ns as achievements_ns
from .problems import ns as problems_ns
from .shell_servers import ns as shell_servers_ns
from .exceptions import ns as exceptions_ns
from .settings import ns as settings_ns
from .bundles import ns as bundles_ns
from .submissions import ns as submissions_ns
from .feedback import ns as feedback_ns
from .users import ns as users_ns
from .user import ns as user_ns
from .status import ns as status_ns
from .team import ns as team_ns
from .stats import ns as stats_ns
from .teams import ns as teams_ns
from .groups import ns as groups_ns

blueprint = Blueprint('v1_api', __name__)
api = Api(
    app=blueprint,
    title='picoCTF API',
    version='1.0',
)

for ns in [
    achievements_ns,
    problems_ns,
    shell_servers_ns,
    exceptions_ns,
    settings_ns,
    bundles_ns,
    submissions_ns,
    feedback_ns,
    users_ns,
    user_ns,
    status_ns,
    team_ns,
    stats_ns,
    teams_ns,
    groups_ns,
        ]:
    api.add_namespace(ns)
















@api.errorhandler(PicoException)
def handle_pico_exception(e):
    """Handle exceptions."""
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response
