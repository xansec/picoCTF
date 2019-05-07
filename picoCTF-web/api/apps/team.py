"""Routing functions for /api/team."""
from flask import Blueprint, request

import api.common
import api.config
import api.stats
import api.team
import api.user
from api.annotations import check_csrf, require_login
from api.common import WebSuccess

blueprint = Blueprint("team_api", __name__)

# @TODO move to /teams, GET /teams should only show teams you belong to unless admin
@blueprint.route('/create', methods=['POST'])
@require_login
def create_new_team_hook():
    api.team.create_new_team_request(api.common.flat_multi(request.form))
    return WebSuccess("You now belong to your newly created team."), 201

@blueprint.route('/join', methods=['POST'])
@require_login
def join_team_hook():
    api.team.join_team_request(api.common.flat_multi(request.form))
    return WebSuccess("You have successfully joined that team!"), 200
