"""Routing functions for /api/problem."""
import json

from flask import Blueprint, request

import api.auth
import api.config
import api.problem
import api.problem_feedback
import api.submissions
import api.user
from api.annotations import (block_after_competition, block_before_competition,
                             check_csrf, require_admin, require_login,
                             require_teacher)
from api.common import WebError, WebSuccess

blueprint = Blueprint("problem_api", __name__)


@blueprint.route('/feedback', methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def problem_feedback_hook():
    feedback = json.loads(request.form.get("feedback", ""))
    pid = request.form.get("pid", None)

    if feedback is None or pid is None:
        return WebError("Please supply a pid and feedback."), 400

    if not api.config.get_settings()["enable_feedback"]:
        return WebError(
            "Problem feedback is not currently being accepted."), 403

    api.problem_feedback.add_problem_feedback(pid, api.auth.get_uid(),
                                              feedback)
    return WebSuccess("Your feedback has been accepted."), 201


@blueprint.route('/feedback/reviewed', methods=['GET'])
@require_login
@block_before_competition()
def problem_reviews_hook():
    uid = api.user.get_user()['uid']
    return WebSuccess(
        data=api.problem_feedback.get_problem_feedback(uid=uid)), 200


@blueprint.route("/hint", methods=['GET'])
@require_login
@block_before_competition()
def request_problem_hint_hook():
    source = request.args.get("source")
    pid = request.args.get("pid")

    if pid is None:
        return WebError("Please supply a pid."), 400
    if source is None:
        return WebError("You have to supply the source of the hint."), 400

    tid = api.user.get_team()["tid"]
    if pid not in api.problem.get_unlocked_pids(tid):
        return WebError("Your team hasn't unlocked this problem yet!"), 403

    return WebSuccess("Hint noted."), 200
