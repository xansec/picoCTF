"""Routing functions for /api/user."""
from flask import Blueprint, redirect, request

import api.auth
import api.common
import api.config
import api.email
import api.shell_servers
import api.stats
import api.user
from api.common import WebSuccess

blueprint = Blueprint("user_api", __name__)


@blueprint.route('/confirm_password_reset', methods=['POST'])
def confirm_password_reset_hook():
    password = request.form.get("new-password")
    confirm = request.form.get("new-password-confirmation")
    token_value = request.form.get("reset-token")

    api.user.reset_password(token_value, password, confirm)
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

