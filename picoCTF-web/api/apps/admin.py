"""Routing functions for /api/admin."""
from bson import json_util
from flask import Blueprint, request

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


@blueprint.route("/problems/submissions", methods=["GET"])
@require_admin
def get_problem():
    submission_data = {
        p["name"]: api.stats.get_problem_submission_stats(pid=p["pid"])
        for p in api.problem.get_all_problems(show_disabled=True)
    }
    return WebSuccess(data=submission_data), 200


@blueprint.route("/bundle/dependencies_active", methods=["POST"])
@require_admin
def bundle_dependencies():
    bid = request.form.get("bid", None)
    state = request.form.get("state", None)

    if bid is None:
        return WebError("Must provide bid to load from."), 400

    if state is None:
        return WebError("Must provide a state to set."), 400

    state = json_util.loads(state)

    api.problem.set_bundle_dependencies_enabled(bid, state)

    return WebSuccess(
        "Dependencies are now {}."
        .format("enabled" if state else "disabled")), 200
