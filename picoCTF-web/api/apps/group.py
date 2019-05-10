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

register_group_schema = Schema({
    Required("group-name"):
    check(("Classroom name must be between 3 and 50 characters.",
           [str, Length(min=3, max=100)]),)
},
                               extra=True)

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

delete_group_schema = Schema({
    Required("group-name"):
    check(("Classroom name must be between 3 and 50 characters.",
           [str, Length(min=3, max=100)]),)
},
                             extra=True)

blueprint = Blueprint("group_api", __name__)


@blueprint.route('/settings', methods=['GET'])
def get_group_settings_hook():
    gid = request.args.get("gid")
    group = api.group.get_group(gid=gid)

    prepared_data = {
        "name": group["name"],
        "settings": api.group.get_group_settings(gid=group["gid"])
    }

    return WebSuccess(data=prepared_data), 200


@blueprint.route('/settings', methods=['POST'])
@require_teacher
def change_group_settings_hook():
    gid = request.form.get("gid")
    settings = json.loads(request.form.get("settings"))

    user = api.user.get_user()
    group = api.group.get_group(gid=gid)

    roles = api.group.get_roles_in_group(gid=group["gid"], uid=user["uid"])

    if roles["teacher"]:
        api.group.change_group_settings(group["gid"], settings)
        return WebSuccess(
            message="Classroom settings changed successfully."), 200
    else:
        return WebError(
            message="You do not have sufficient privilege to do that."), 401


@blueprint.route('/invite', methods=['POST'])
@require_teacher
def invite_email_to_group_hook():
    gid = request.form.get("gid")
    email = request.form.get("email")
    role = request.form.get("role")

    user = api.user.get_user()

    if gid is None or email is None or len(email) == 0:
        return WebError(
            message="You must specify a gid and email address to invite."), 400

    if role not in ["member", "teacher"]:
        return WebError(
            message="A user's role is either a member or teacher."), 400

    group = api.group.get_group(gid=gid)
    roles = api.group.get_roles_in_group(group["gid"], uid=user["uid"])

    if roles["teacher"]:
        api.email.send_email_invite(
            group["gid"], email, teacher=(role == "teacher"))
        return WebSuccess(message="Email invitation has been sent."), 200
    else:
        return WebError(
            message="You do not have sufficient privilege to do that."), 401


@blueprint.route('/score', methods=['GET'])
@require_teacher
def get_group_score_hook():
    name = request.args.get("group-name")

    user = api.user.get_user()
    roles = api.group.get_roles_in_group(gid, uid=user["uid"])

    if not roles["teacher"]:
        return WebError("You are not a teacher for this classroom."), 401

    score = api.stats.get_group_scores(name=name)
    if score is None:
        return WebError(
            "There was an error retrieving the classroom's score."), 500

    return WebSuccess(data={'score': score}), 200


@blueprint.route('/create', methods=['POST'])
@check_csrf
@require_teacher
def create_group_hook():
    """
    Create a new group. Validates forms.

    All required arguments are assumed to be keys in params.
    """
    params = api.common.flat_multi(request.form)
    validate(register_group_schema, params)

    # Current user is the prospective owner.
    team = api.user.get_team()

    if safe_fail(
            api.group.get_group, name=params["group-name"],
            owner_tid=team["tid"]) is not None:
        return WebError("A classroom with that name already exists!"), 409

    gid = api.group.create_group(team["tid"], params["group-name"])
    return WebSuccess("Successfully created classroom.", data=gid), 201


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


@blueprint.route('/leave', methods=['POST'])
@check_csrf
@require_login
def leave_group_hook():
    """
    Try to remove a team from a group.

    Validates forms. All required arguments are assumed to be keys in params.
    """
    params = api.common.flat_multi(request.form)

    validate(leave_group_schema, params)
    owner_team = api.team.get_team(name=params["group-owner"])

    group = api.group.get_group(
        name=params["group-name"], owner_tid=owner_team["tid"])

    team = api.user.get_team()
    roles = api.group.get_roles_in_group(group["gid"], tid=team["tid"])

    if not roles["member"] and not roles["teacher"]:
        raise PicoException("Your team is not a member of that classroom!",
                            403)

    api.group.leave_group(group["gid"], team["tid"])

    return WebSuccess("Successfully left classroom."), 200


@blueprint.route('/delete', methods=['POST'])
@check_csrf
@require_teacher
def delete_group_hook():
    """
    Try to delete a group.

    Validates forms. All required arguments are assumed to be keys in params.
    """
    params = api.common.flat_multi(request.form)

    validate(delete_group_schema, params)

    if params.get("group-owner"):
        owner_team = api.team.get_team(name=params["group-owner"])
    else:
        owner_team = api.team.get_team()

    group = api.group.get_group(
        name=params["group-name"], owner_tid=owner_team["tid"])

    user = api.user.get_user()
    roles = api.group.get_roles_in_group(group["gid"], uid=user["uid"])

    if roles["owner"]:
        api.group.delete_group(group["gid"])
    else:
        raise PicoException("Only the owner of a classroom can delete it!",
                            403)

    return WebSuccess("Successfully deleted classroom"), 200


@blueprint.route('/teacher/leave', methods=['POST'])
@check_csrf
@require_teacher
def force_leave_group_hook():
    gid = request.form.get("gid")
    tid = request.form.get("tid")

    if gid is None or tid is None:
        return WebError("You must specify a gid and tid."), 400

    user = api.user.get_user()
    roles = api.group.get_roles_in_group(gid, uid=user["uid"])
    if not roles["teacher"]:
        return WebError("You must be a teacher of a classroom " +
                        "to remove a team."), 401

    api.group.leave_group(gid, tid)

    return WebSuccess("Team has successfully left the classroom."), 200


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
