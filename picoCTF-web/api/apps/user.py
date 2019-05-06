"""Routing functions for /api/user."""
from flask import Blueprint, redirect, request, session

import api.auth
import api.common
import api.config
import api.email
import api.shell_servers
import api.stats
import api.user
from api.annotations import check_csrf, require_login, require_admin
from api.common import safe_fail, WebError, WebSuccess

blueprint = Blueprint("user_api", __name__)


@blueprint.route("/authorize/<role>")
def authorize_role(role=None):
    """Verify the role of the logged in user."""
    if role == "user" and safe_fail(api.user.get_user):
        return "Client is logged in.", 200
    elif role == "teacher" and safe_fail(api.user.is_teacher):
        return "Client is a teacher.", 200
    elif role == "admin" and safe_fail(api.user.is_admin):
        return "Client is an administrator.", 200
    elif role == "anonymous":
        return "Client is authorized.", 200
    else:
        return "Client is not authorized.", 401


@blueprint.route('/update_password', methods=['POST'])
@check_csrf
@require_login
def update_password_hook():
    api.user.update_password_request(
        api.common.flat_multi(request.form), check_current=True)
    return WebSuccess("Your password has been successfully updated!"), 200


@blueprint.route('/disable_account', methods=['POST'])
@check_csrf
@require_login
def disable_account_hook():
    api.user.disable_account_request(
        api.common.flat_multi(request.form), check_current=True)
    return WebSuccess("You have successfully disabled your account!"), 200


@blueprint.route('/reset_password', methods=['POST'])
def reset_password_hook():
    username = request.form.get("username", None)

    api.email.request_password_reset(username)
    return WebSuccess(
        "A password reset link has been sent to the email address provided " +
        "during registration."), 200


@blueprint.route('/confirm_password_reset', methods=['POST'])
def confirm_password_reset_hook():
    password = request.form.get("new-password")
    confirm = request.form.get("new-password-confirmation")
    token_value = request.form.get("reset-token")

    api.email.reset_password(token_value, password, confirm)
    return WebSuccess("Your password has been reset."), 200


@blueprint.route('/verify', methods=['GET'])
def verify_user_hook():
    uid = request.args.get("uid")
    token = request.args.get("token")

    # Needs to be more telling of success
    if api.common.safe_fail(api.user.verify_user, uid, token):
        if api.config.get_settings()["max_team_size"] > 1:
            return redirect("/#team-builder")
        else:
            return redirect("/#status=verified")
    else:
        return redirect("/")


@blueprint.route('/login', methods=['POST'])
def login_hook():
    username = request.form.get('username')
    password = request.form.get('password')
    api.auth.login(username, password)
    return WebSuccess(
        message="Successfully logged in as " + username,
        data={
            'teacher': api.user.is_teacher(),
            'admin': api.user.is_admin()
        }), 200


@blueprint.route('/logout', methods=['GET'])
def logout_hook():
    if api.auth.is_logged_in():
        api.auth.logout()
        return WebSuccess("Successfully logged out."), 200
    else:
        return WebError("You do not appear to be logged in."), 400


@blueprint.route('/status', methods=['GET'])
def status_hook():
    settings = api.config.get_settings()
    status = {
        "logged_in":
        api.auth.is_logged_in(),
        "admin":
        api.auth.is_logged_in() and api.user.is_admin(),
        "teacher":
        api.auth.is_logged_in() and api.user.is_teacher(),
        "enable_feedback":
        settings["enable_feedback"],
        "enable_captcha":
        settings["captcha"]["enable_captcha"],
        "reCAPTCHA_public_key":
        settings["captcha"]["reCAPTCHA_public_key"],
        "competition_active":
        api.common.check_competition_active(),
        "username":
        api.user.get_user()['username'] if api.auth.is_logged_in() else "",
        "tid":
        api.user.get_user()["tid"] if api.auth.is_logged_in() else "",
        "email_verification":
        settings["email"]["email_verification"]
    }

    if api.auth.is_logged_in():
        team = api.user.get_team()
        status["team_name"] = team["team_name"]
        status["score"] = api.stats.get_score(tid=team["tid"])

    return WebSuccess(data=status), 200


@blueprint.route('/shell_servers', methods=['GET'])
@require_login
def shell_servers_hook():
    servers = [{
        "host": server['host'],
        "protocol": server['protocol']
    } for server in api.shell_servers.get_assigned_server()]
    return WebSuccess(data=servers), 200


@blueprint.route('/extdata', methods=['GET'])
@require_login
def get_extdata_hook():
    """
    Return user extdata, or empty JSON object if unset.
    """
    user = api.user.get_user(uid=None)
    return WebSuccess(data=user['extdata']), 200


@blueprint.route('/extdata', methods=['PUT'])
@check_csrf
@require_login
def update_extdata_hook():
    """
    Sets user extdata via HTTP form. Takes in any key-value pairs.
    """
    api.user.update_extdata(api.common.flat_multi(request.form))
    return WebSuccess("Your Extdata has been successfully updated."), 200
