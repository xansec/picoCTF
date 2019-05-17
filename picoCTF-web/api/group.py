"""Module for handling groups of teams."""

from voluptuous import Required, Schema

import api
from api import check, PicoException, validate

group_settings_schema = Schema({
    Required("email_filter"):
    check(("Email filter must be a list of emails.",
           [lambda emails: type(emails) == list])),
    Required("hidden"):
    check(("Hidden property of a group is a boolean.",
           [lambda hidden: type(hidden) == bool]))
})


def get_group(gid=None, name=None, owner_tid=None):
    """
    Retrieve a group based on its name or gid.

    Args:
        name: the name of the group
        gid: the gid of the group
        owner_tid: the tid of the group owner
    Returns:
        The group dict, or None if not found.
    """
    db = api.db.get_conn()

    match = {}
    if name is not None and owner_tid is not None:
        match.update({"name": name})
        match.update({"owner": owner_tid})
    elif gid is not None:
        match.update({"gid": gid})
    else:
        return None

    return db.groups.find_one(match, {"_id": 0})


def get_teacher_information(gid):
    """
    Retrieve the team information for all teams in a group.

    Args:
        gid: the group id
    Returns:
        A list of team information
    """
    group = get_group(gid=gid)

    member_information = []
    for tid in group["teachers"]:
        team_information = api.team.get_team_information(tid=tid)
        team_information["teacher"] = True
        member_information.append(team_information)

    return member_information


def get_member_information(gid):
    """
    Retrieve the team information for all teams in a group.

    Args:
        gid: the group id
    Returns:
        A list of team information
    """
    group = get_group(gid=gid)

    member_information = []
    for tid in group["members"]:
        team = api.team.get_team(tid=tid)
        if team["size"] > 0:
            member_information.append(
                api.team.get_team_information(tid=team["tid"]))

    return member_information


@api.logger.log_action
def create_group(tid, group_name):
    """
    Insert group into the db. Assumes everything is validated.

    Args:
        tid: The id of the team creating the group.
        group_name: The name of the group.
    Returns:
        The new group's gid.

    """
    db = api.db.get_conn()

    gid = api.common.token()

    db.groups.insert({
        "name": group_name,
        "owner": tid,
        "teachers": [],
        "members": [],
        "settings": {
            "email_filter": [],
            "hidden": False
        },
        "gid": gid
    })

    return gid


def get_group_settings(gid):
    """Get various group settings."""
    db = api.db.get_conn()

    # Ensure it exists.
    group = api.group.get_group(gid=gid)
    group_result = db.groups.find_one({"gid": group["gid"]}, {
        "_id": 0,
        "settings": 1
    })

    return group_result["settings"]


def change_group_settings(gid, settings):
    """
    Replace the current settings with the supplied ones.

    Args:
        gid: ID of the group to update
        settings: new settings object

    Raises:
        PicoException if attempting to change 'hidden' from true to false
    """
    db = api.db.get_conn()

    validate(group_settings_schema, settings)

    group = api.group.get_group(gid=gid)
    if group["settings"]["hidden"] and not settings["hidden"]:
        raise PicoException('Cannot make a previously hidden group public',
                            status_code=422)

    db.groups.update({"gid": group["gid"]}, {"$set": {"settings": settings}})


@api.logger.log_action
def join_group(gid, tid, teacher=False):
    """
    Add a team to a group. Assumes everything is valid.

    Args:
        tid: the team id
        gid: the group id to join
        teacher: whether or not the user is a teacher
    """
    db = api.db.get_conn()

    role_group = "teachers" if teacher else "members"

    if teacher:
        uids = api.team.get_team_uids(tid=tid)
        for uid in uids:
            db.users.update({"uid": uid}, {"$set": {"teacher": True}})

    db.groups.update({'gid': gid}, {'$push': {role_group: tid}})


@api.logger.log_action
def leave_group(gid, tid):
    """
    Remove a team from a group.

    Args:
        tid: the team id
        gid: the group id to leave
    """
    db = api.db.get_conn()
    db.groups.update({'gid': gid}, {'$pull': {"teachers": tid}})
    db.groups.update({'gid': gid}, {'$pull': {"members": tid}})


@api.logger.log_action
def delete_group(gid):
    """
    Delete a group.

    Args:
        gid: the group id to delete
    """
    db = api.db.get_conn()
    db.groups.remove({'gid': gid})


def get_all_groups():
    """Return a list of all groups in the database."""
    db = api.db.get_conn()
    return list(db.groups.find({}, {"_id": 0}))
