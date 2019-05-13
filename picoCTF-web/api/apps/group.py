"""Routing functions for /api/group/."""
import json

from flask import Blueprint, request
from voluptuous import Length, Required, Schema

import api.common
import api.email
import api.group
import api.stats
import api.team
import api.user
from api.common import (check, safe_fail, validate, WebError, PicoException,
                        WebSuccess)
from api.user import require_login, require_teacher, check_csrf


join_group_schema = Schema({
    Required("group-name"):
    check(("Classroom name must be between 3 and 50 characters.",
           [str, Length(min=3, max=100)]),),
    Required("group-owner"):
    check(("The teacher name must be between 3 and 40 characters.",
           [str, Length(min=3, max=40)]),)
},
                           extra=True)

leave_group_schema = Schema({
    Required("group-name"):
    check(("Classroom name must be between 3 and 50 characters.",
           [str, Length(min=3, max=100)]),),
    Required("group-owner"):
    check(("The teacher name must be between 3 and 40 characters.",
           [str, Length(min=3, max=40)]),)
},
                            extra=True)

blueprint = Blueprint("group_api", __name__)


@blueprint.route('/join', methods=['POST'])
@check_csrf
@require_login
def join_group_hook():
    """
    Try to place a team into a group.

    Validates forms. All required arguments are assumed to be keys in params.
    """
    params = api.common.flat_multi(request.form)
    validate(join_group_schema, params)

    owner_team = safe_fail(api.team.get_team, name=params["group-owner"])

    if not owner_team:
        raise PicoException("No teacher exists with that name!", 404)

    if safe_fail(
            api.group.get_group,
            name=params["group-name"],
            owner_tid=owner_team["tid"]) is None:
        raise PicoException("No classroom exists with that name!", 404)

    group = api.group.get_group(
        name=params["group-name"], owner_tid=owner_team["tid"])

    group_settings = api.group.get_group_settings(gid=group["gid"])

    team = api.team.get_team()

    if group_settings["email_filter"]:
        for member_uid in api.team.get_team_uids(tid=team["tid"]):
            member = api.user.get_user(uid=member_uid)
            if not api.user.verify_email_in_whitelist(
                    member["email"], group_settings["email_filter"]):
                raise PicoException(
                    "{}'s email does not belong to the whitelist " +
                    "for that classroom. Your team may not join this " +
                    "classroom at this time.".format(member["username"]), 403)

    roles = api.group.get_roles_in_group(group["gid"], tid=team["tid"])
    if roles["teacher"] or roles["member"]:
        raise PicoException("Your team is already a member of that classroom!",
                            422)

    api.group.join_group(group["gid"], team["tid"])

    return WebSuccess("Successfully joined classroom"), 200


@blueprint.route('/teacher/role_switch', methods=['POST'])
@require_teacher
def switch_user_role_group_hook():
    gid = request.form.get("gid")
    tid = request.form.get("tid")
    role = request.form.get("role")

    user = api.user.get_user()

    if gid is None or tid is None:
        return WebError(
            message="You must specify a gid and tid to perform " +
                    "a role switch."), 400

    if role not in ["member", "teacher"]:
        return WebError(message="A user's role is either a member " +
                                "or teacher."), 400

    group = api.group.get_group(gid=gid)

    roles = api.group.get_roles_in_group(group["gid"], uid=user["uid"])
    if not roles["teacher"]:
        return WebError(
            message="You do not have sufficient privilege to do that."), 401

    affected_team = api.team.get_team(tid=tid)
    affected_team_roles = api.group.get_roles_in_group(
        group["gid"], tid=affected_team["tid"])
    if affected_team_roles["owner"]:
        return WebError(message="You can not change the role of the owner " +
                        "of the classroom."), 400

    api.group.switch_role(group["gid"], affected_team["tid"], role)
    return WebSuccess(message="User's role has been successfully " +
                              "changed."), 200
