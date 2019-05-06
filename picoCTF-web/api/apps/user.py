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

@blueprint.route('/update_password', methods=['POST'])
@check_csrf
@require_login
def update_password_hook():
    api.user.update_password_request(
        api.common.flat_multi(request.form), check_current=True)
    return WebSuccess("Your password has been successfully updated!"), 200


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

