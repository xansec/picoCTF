"""Routing functions for /api/admin."""
from bson import json_util
from flask import Blueprint, current_app, request

import api.admin
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


@blueprint.route('/problems', methods=['GET'])
@require_admin
def get_problem_data_hook() -> str:
    problems = list(
        filter(lambda p: len(p["instances"]) > 0,
               api.problem.get_all_problems(show_disabled=True)))

    for problem in problems:
        problem["reviews"] = api.problem_feedback.get_problem_feedback(
            pid=problem["pid"])

    data = {"problems": problems, "bundles": api.problem.get_all_bundles()}

    return WebSuccess(data=data).as_json()


@blueprint.route('/users', methods=['GET'])
@require_admin
def get_all_users_hook() -> str:
    users = api.user.get_all_users()
    if users is None:
        return WebError("There was an error query users from the database.")
    return WebSuccess(data=users).as_json()


@blueprint.route('/exceptions', methods=['GET'])
@require_admin
def get_exceptions_hook() -> str:
    try:
        limit = abs(int(request.args.get("limit")))
        exceptions = api.admin.get_api_exceptions(result_limit=limit)
        return WebSuccess(data=exceptions).as_json()

    except (ValueError, TypeError):
        return WebError("limit is not a valid integer.").as_json()


@blueprint.route('/exceptions/dismiss', methods=['POST'])
@require_admin
def dismiss_exceptions_hook() -> str:
    trace = request.form.get("trace", None)
    if trace:
        api.admin.dismiss_api_exceptions(trace)
        return WebSuccess(
            data="Successfully changed exception visibility.").as_json()
    else:
        return WebError(message="You must supply a trace to hide.").as_json()


@blueprint.route("/problems/submissions", methods=["GET"])
@require_admin
def get_problem() -> str:
    submission_data = {
        p["name"]: api.stats.get_problem_submission_stats(pid=p["pid"])
        for p in api.problem.get_all_problems(show_disabled=True)
    }
    return WebSuccess(data=submission_data).as_json()


@blueprint.route("/problems/availability", methods=["POST"])
@require_admin
def change_problem_availability_hook() -> str:
    pid = request.form.get("pid", None)
    desired_state = request.form.get("state", None)

    if desired_state is None:
        return WebError("Problems are either enabled or disabled.").as_json()
    else:
        state = json_util.loads(desired_state)

    api.admin.set_problem_availability(pid, state)
    return WebSuccess(data="Problem state changed successfully.").as_json()


@blueprint.route("/shell_servers", methods=["GET"])
@require_admin
def get_shell_servers() -> str:
    return WebSuccess(data=api.shell_servers
                              .get_servers(get_all=True)).as_json()


@blueprint.route("/shell_servers/add", methods=["POST"])
@require_admin
def add_shell_server() -> str:
    params = api.common.flat_multi(request.form)
    api.shell_servers.add_server(params)
    return WebSuccess("Shell server added.").as_json()


@blueprint.route("/shell_servers/update", methods=["POST"])
@require_admin
def update_shell_server() -> str:
    params = api.common.flat_multi(request.form)

    sid = params.get("sid", None)
    if sid is None:
        return WebError("Must specify sid to be updated").as_json()

    api.shell_servers.update_server(sid, params)
    return WebSuccess("Shell server updated.").as_json()


@blueprint.route("/shell_servers/remove", methods=["POST"])
@require_admin
def remove_shell_server() -> str:
    sid = request.form.get("sid", None)
    if sid is None:
        return WebError("Must specify sid to be removed").as_json()

    api.shell_servers.remove_server(sid)
    return WebSuccess("Shell server removed.").as_json()


@blueprint.route("/shell_servers/load_problems", methods=["POST"])
@require_admin
def load_problems_from_shell_server() -> str:
    sid = request.form.get("sid", None)

    if sid is None:
        return WebError("Must provide sid to load from.").as_json()

    number = api.shell_servers.load_problems_from_server(sid)
    return WebSuccess(
        "Loaded {} problems from the server".format(number)).as_json()


@blueprint.route("/shell_servers/check_status", methods=["GET"])
@require_admin
def check_status_of_shell_server() -> str:
    sid = request.args.get("sid", None)

    if sid is None:
        return WebError("Must provide sid to load from.").as_json()

    all_online, data = api.shell_servers.get_problem_status_from_server(sid)

    if all_online:
        return WebSuccess("All problems are online", data=data).as_json()
    else:
        return WebError(
            "One or more problems are offline. " +
            "Please connect and fix the errors.",
            data=data).as_json()


@blueprint.route("/shell_servers/reassign_teams", methods=['POST'])
@require_admin
def reassign_teams_hook() -> str:
    if not api.config.get_settings()["shell_servers"]["enable_sharding"]:
        return WebError(
            "Enable sharding first before assigning server numbers.").as_json()
    else:
        include_assigned = request.form.get("include_assigned", False)
        count = api.shell_servers.reassign_teams(
            include_assigned=include_assigned)
        if include_assigned:
            action = "reassigned."
        else:
            action = "assigned."
        return WebSuccess(str(count) + " teams " + action).as_json()


@blueprint.route("/bundle/dependencies_active", methods=["POST"])
@require_admin
def bundle_dependencies() -> str:
    bid = request.form.get("bid", None)
    state = request.form.get("state", None)

    if bid is None:
        return WebError("Must provide bid to load from.").as_json()

    if state is None:
        return WebError("Must provide a state to set.").as_json()

    state = json_util.loads(state)

    api.problem.set_bundle_dependencies_enabled(bid, state)

    return WebSuccess(
        "Dependencies are now {}."
        .format("enabled" if state else "disabled")).as_json()


@blueprint.route("/settings", methods=["GET"])
@require_admin
def get_settings() -> str:
    return WebSuccess(data=api.config.get_settings()).as_json()


@blueprint.route("/settings/change", methods=["POST"])
@require_admin
def change_settings() -> str:
    data = json_util.loads(request.form["json"])
    api.config.change_settings(data)
    # May need to recreate the Flask-Mail object if mail settings changed
    api.update_mail_config(current_app)
    api.logger.setup_logs({"verbose": 2})
    return WebSuccess("Settings updated").as_json()
