"""Routing functions for /api/admin."""
from flask import Blueprint

import api.common
import api.config
import api.logger
import api.problem
import api.problem_feedback
import api.shell_servers
import api.stats
import api.user
from api.annotations import require_admin
from api.common import WebError, WebSuccess

blueprint = Blueprint("admin_api", __name__)


@blueprint.route('/users', methods=['GET'])
@require_admin
def get_all_users_hook():
    users = api.user.get_all_users()
    if users is None:
        return WebError("There was an error query users from the database.")
    return WebSuccess(data=users), 200


