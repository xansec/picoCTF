"""Routing functions for /api/team."""
from flask import Blueprint, request

import api.common
import api.config
import api.stats
import api.team
import api.user
from api.annotations import jsonify, check_csrf, require_login
from api.common import WebError, WebSuccess

blueprint = Blueprint("team_api", __name__)


@blueprint.route('', methods=['GET'])
@jsonify
@require_login
def team_information_hook():
    return WebSuccess(data=api.team.get_team_information())


@blueprint.route('/score', methods=['GET'])
@jsonify
@require_login
def get_team_score_hook():
    score = api.stats.get_score(tid=api.user.get_user()['tid'])
    if score is not None:
        return WebSuccess(data={'score': score})
    return WebError("There was an error retrieving your score.")


@blueprint.route('/create', methods=['POST'])
@jsonify
@require_login
def create_new_team_hook():
    api.team.create_new_team_request(api.common.flat_multi(request.form))
    return WebSuccess("You now belong to your newly created team.")


@blueprint.route('/update_password', methods=['POST'])
@jsonify
@check_csrf
@require_login
def update_team_password_hook():
    api.team.update_password_request(api.common.flat_multi(request.form))
    return WebSuccess("Your team password has been successfully updated!")


@blueprint.route('/join', methods=['POST'])
@jsonify
@require_login
def join_team_hook():
    api.team.join_team_request(api.common.flat_multi(request.form))
    return WebSuccess("You have successfully joined that team!")


@blueprint.route("/settings")
@jsonify
def get_team_status():
    settings = api.config.get_settings()

    filtered_settings = {
        "max_team_size": settings["max_team_size"],
        "email_filter": settings["email_filter"]
    }

    return WebSuccess(data=filtered_settings)
