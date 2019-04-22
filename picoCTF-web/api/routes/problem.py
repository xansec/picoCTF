"""Routing functions for /api/problem."""
import json

from flask import Blueprint, request

import api.auth
import api.config
import api.problem
import api.problem_feedback
import api.user
from api.annotations import (block_after_competition, block_before_competition,
                             check_csrf, log_action, require_admin,
                             require_login, require_teacher)
from api.common import WebError, WebSuccess

blueprint = Blueprint("problem_api", __name__)


@blueprint.route('', defaults={'category': None}, methods=['GET'])
@blueprint.route('/category/<category>', methods=['GET'])
@require_login
@block_before_competition()
def get_visible_problems_hook(category) -> str:
    visible_problems = api.problem.get_visible_problems(
        api.user.get_user()['tid'], category=category)
    return WebSuccess(data=api.problem.sanitize_problem_data(visible_problems)).as_json()


@blueprint.route('/all', defaults={'category': None}, methods=['GET'])
@blueprint.route('/all/category/<category>', methods=['GET'])
@require_login
@require_teacher
@block_before_competition()
def get_all_problems_hook(category) -> str:
    all_problems = api.problem.get_all_problems(
        category=category, basic_only=True)
    return WebSuccess(data=api.problem.sanitize_problem_data(all_problems)).as_json()


@blueprint.route('/count', defaults={'category': None}, methods=['GET'])
@blueprint.route('/count/<category>', methods=['GET'])
@require_login
@block_before_competition()
def get_all_problems_count_hook(category) -> str:
    return WebSuccess(data=api.problem.count_all_problems(category=category)).as_json()


@blueprint.route('/unlocked', methods=['GET'])
@require_login
@block_before_competition()
def get_unlocked_problems_hook() -> str:
    unlocked_problems = api.problem.get_unlocked_problems(
        api.user.get_user()['tid'])
    return WebSuccess(
        data=api.problem.sanitize_problem_data(unlocked_problems)).as_json()


@blueprint.route('/solved', methods=['GET'])
@require_login
@block_before_competition()
def get_solved_problems_hook() -> str:
    solved_problems = api.problem.get_solved_problems(
        tid=api.user.get_user()['tid'])

    return WebSuccess(data=api.problem.sanitize_problem_data(solved_problems)).as_json()


@blueprint.route('/submit', methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
@block_after_competition()
def submit_key_hook() -> str:
    user_account = api.user.get_user()
    tid = user_account['tid']
    uid = user_account['uid']
    pid = request.form.get('pid', '')
    key = request.form.get('key', '')
    method = request.form.get('method', '')
    ip = request.remote_addr

    (correct, previously_solved_by_user,
     previously_solved_by_team) = api.problem.submit_key(
            tid, pid, key, method, uid, ip)

    if correct and not previously_solved_by_team:
        return WebSuccess("That is correct!")
    elif not correct and not previously_solved_by_team:
        return WebError("That is incorrect!")
    elif correct and previously_solved_by_user:
        return WebSuccess(
            'Flag correct: however, you have already solved ' +
            'this problem.'
        )
    elif correct and previously_solved_by_team:
        return WebSuccess(
            'Flag correct: however, your team has already received points ' +
            'for this flag.'
        )
    elif not correct and previously_solved_by_user:
        return WebError(
            'Flag incorrect: please note that you have ' +
            'already solved this problem.'
        )
    elif not correct and previously_solved_by_team:
        return WebError(
            'Flag incorrect: please note that someone on your team has ' +
            'already solved this problem.'
        )


@blueprint.route('/<path:pid>', methods=['GET'])
@require_login
@block_before_competition()
@block_after_competition()
def get_single_problem_hook(pid) -> str:
    problem_info = api.problem.get_problem(pid, tid=api.user.get_user()['tid'])
    if not api.user.is_admin():
        problem_info.pop("instances")
    return WebSuccess(data=api.problem.sanitize_problem_data(problem_info)).as_json()


@blueprint.route('/feedback', methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def problem_feedback_hook() -> str:
    feedback = json.loads(request.form.get("feedback", ""))
    pid = request.form.get("pid", None)

    if feedback is None or pid is None:
        return WebError("Please supply a pid and feedback.").as_json()

    if not api.config.get_settings()["enable_feedback"]:
        return WebError("Problem feedback is not currently being accepted.").as_json()

    api.problem_feedback.add_problem_feedback(pid, api.auth.get_uid(),
                                              feedback)
    return WebSuccess("Your feedback has been accepted.").as_json()


@blueprint.route('/feedback/reviewed', methods=['GET'])
@require_login
@block_before_competition()
def problem_reviews_hook() -> str:
    uid = api.user.get_user()['uid']
    return WebSuccess(data=api.problem_feedback.get_problem_feedback(uid=uid)).as_json()


@blueprint.route("/hint", methods=['GET'])
@require_login
@block_before_competition()
def request_problem_hint_hook() -> str:
    @log_action
    def hint(pid, source):
        return None

    source = request.args.get("source")
    pid = request.args.get("pid")

    if pid is None:
        return WebError("Please supply a pid.")
    if source is None:
        return WebError("You have to supply the source of the hint.").as_json()

    tid = api.user.get_team()["tid"]
    if pid not in api.problem.get_unlocked_pids(tid, category=None):
        return WebError("Your team hasn't unlocked this problem yet!").as_json()

    hint(pid, source)
    return WebSuccess("Hint noted.").as_json()


@blueprint.route("/load_problems", methods=['POST'])
@require_login
@require_admin
def load_problems_hook() -> str:
    data = json.loads(request.form.get("competition_data", ""))

    api.problem.load_published(data)
    return WebSuccess("Inserted {} problems.".format(len(data["problems"]))).as_json()


@blueprint.route('/clear_submissions', methods=['GET'])
@require_login
@require_admin
def clear_all_submissions_hook() -> str:
    api.problem.clear_all_submissions()
    return WebSuccess("All submissions reset.").as_json()
