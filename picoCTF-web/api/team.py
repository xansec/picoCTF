"""Team management module."""

from voluptuous import Length, Required, Schema

import api
from api import cache, check, log_action, PicoException
from api.cache import memoize

new_team_schema = Schema({
    Required("team_name"):
    check(
        ("The team name must be between 3 and 40 characters.",
         [str, Length(min=3, max=40)]),
        ("This team name conflicts with an existing user name.",
         [lambda name: api.user.get_user(name=name) is None]),
        ("A team with that name already exists.",
         [lambda name: api.team.get_team(name=name) is None]),
    ),
    Required("team_password"):
    check(("Passwords must be between 3 and 20 characters.",
           [str, Length(min=3, max=20)]))
},
                         extra=True)


def get_team(tid=None, name=None):
    """
    Retrieve a team based on a property (tid, name, etc.).

    Args:
        tid: team id
        name: team name
    Returns:
        Returns the corresponding team object or None if it could not be found
    """
    db = api.db.get_conn()

    match = {}
    if tid is not None:
        match.update({'tid': tid})
    elif name is not None:
        match.update({'team_name': name})
    elif api.user.is_logged_in():
        match.update({"tid": api.user.get_user()["tid"]})
    else:
        return None

    return db.teams.find_one(match, {"_id": 0})


@memoize
def get_groups(tid):
    """
    Get the group membership for a team.

    Args:
        tid: The team id
    Returns:
        List of group objects the team is a member of.
    """
    # Get all groups associated with the given team
    db = api.db.get_conn()
    associated_groups = list(db.groups.find(
        {"$or": [
            {'owner': tid},
            {"teachers": tid},
            {"members": tid}]},
        {
            'name': 1,
            'gid': 1,
            'owner': 1,
            'members': 1,
            '_id': 0
        }))

    for group in associated_groups:
        # Replace the owner tid with the team's name
        group['owner'] = api.team.get_team(tid=group['owner'])['team_name']

        # Add the group's average score - WHY???
        # group['score'] = api.stats.get_group_average_score(gid=group['gid'])

    return associated_groups


def create_and_join_new_team(team_name, team_password, user):
    """
    Fulfill new team requests for users who have already registered.

    Seperate from create_team() as we need to do additional logic:
    - Check that the new team name doesn't conflict with a team or user
    - Check that the user creating the team is on their initial
      1-person "username team"

    Args:
        team_name: The desired name for the team.
                   Must be unique across users and teams.
        team_password: The team's password.
        user: The user

    Returns:
        The tid of the new team

    Raises:
        PicoException if a team or user with name team_name already exists,
                      or if user has already created a team

    """
    # Ensure name does not conflict with existing user or team
    db = api.db.get_conn()
    if db.users.find_one({'username': team_name}):
        raise PicoException(
            'There is already a user with this name.', 409)
    if db.teams.find_one({'team_name': team_name}):
        raise PicoException(
            'There is already a team with this name.', 409)

    # Make sure the creating user has not already created a team
    current_team = api.team.get_team(tid=user['tid'])
    if current_team['team_name'] != user['username']:
        raise PicoException(
            "You can only create one new team per user account!", 422)

    # Create the team and join it
    new_tid = create_team({
        "team_name": team_name,
        "password": api.common.hash_password(team_password),
        "affiliation": current_team["affiliation"],
        "creator": user["uid"],
        "country": user["country"],
    })
    join_team(team_name, team_password, user)

    return new_tid


def create_team(params):
    """
    Directly insert team into the database.

    Assumes all fields have been validated.

    Args:
        params:
            team_name: Name of the team
            password: team's hashed password
            affiliation: team's affiliation
            country: primary country of team
    Returns:
        The newly created team id.
    """
    db = api.db.get_conn()

    params['tid'] = api.common.token()
    params['size'] = 0
    params['instances'] = {}

    settings = api.config.get_settings()
    if settings["shell_servers"]["enable_sharding"]:
        params['server_number'] = api.shell_servers.get_assigned_server_number(
            new_team=True)

    db.teams.insert(params)

    return params['tid']


def get_team_members(tid=None, name=None, show_disabled=True):
    """
    Retrieve the members on a team.

    Args:
        tid: the team id to query
        name: the team name to query
    Returns:
        A list of the team's members.
    """
    db = api.db.get_conn()

    tid = get_team(name=name, tid=tid)["tid"]

    users = list(
        db.users.find({"tid": tid}, {
            "_id": 0,
            "uid": 1,
            "username": 1,
            "firstname": 1,
            "lastname": 1,
            "disabled": 1,
            "email": 1,
            "teacher": 1,
            "country": 1,
            "usertype": 1,
        }))
    return [
        user for user in users
        if show_disabled or not user.get("disabled", False)
    ]


def get_team_uids(tid=None, name=None, show_disabled=True):
    """
    Get the list of uids that belong to a team.

    Args:
        tid: the team id
        name: the team name
    Returns:
        A list of uids
    """
    return [
        user['uid'] for user in get_team_members(
            tid=tid, name=name, show_disabled=show_disabled)
    ]


def get_team_information(tid):
    """
    Retrieve the information of a team.

    Args:
        tid: the team id
    Returns:
        A dict of team information.
            team_name
            members
    """
    team_info = get_team(tid=tid)

    # Sanitize
    team_info.pop("password", None)
    team_info.pop("instances", None)

    # @TODO there is a LOT of stuff being added here - expensive. all needed?
    #       ideally combine/replace this w/ get_team()
    # Add additional information
    team_info["score"] = int(api.stats.get_score(tid=tid))
    team_info["members"] = [{
        "username": member["username"],
        "firstname": member["firstname"],
        "lastname": member["lastname"],
        "email": member["email"],
        "uid": member["uid"],
        "affiliation": member.get("affiliation", "None"),
        "country": member["country"],
        "usertype": member["usertype"],
    } for member in get_team_members(tid=tid, show_disabled=False)]
    team_info["competition_active"] = api.config.check_competition_active()
    team_info["progression"] = api.stats.get_score_progression(tid=tid)
    team_info["flagged_submissions"] = [
        sub for sub in api.stats.check_invalid_instance_submissions()
        if sub['tid'] == tid
    ]
    team_info["max_team_size"] = api.config.get_settings()["max_team_size"]

    if api.config.get_settings()["achievements"]["enable_achievements"]:
        team_info["achievements"] = api.achievement.get_earned_achievements(
            tid)

    team_info["solved_problems"] = []
    for solved_problem in api.problem.get_solved_problems(tid=tid):
        solved_problem.pop("instances", None)
        solved_problem.pop("pkg_dependencies", None)
        solved_problem.pop("hints", None)
        solved_problem.pop("author", None)
        solved_problem.pop("organization", None)
        team_info["solved_problems"].append(solved_problem)

    # Teams flagged as ineligible once will not recalculate their eligibility
    if team_info.get("eligible", True):
        eligiblity = is_eligible(tid)
        team_info["eligible"] = eligiblity
        if eligiblity is False:  # No point in storing positive results
            mark_eligiblity(tid, eligiblity)
    return team_info


def is_eligible(tid):
    """
    Return a team's eligibility for the current event.

    Args:
        tid: the team id
    Returns:
        True or False
    """
    members = get_team_members(tid, show_disabled=False)
    conditions = api.config.get_settings()['eligibility']
    for member in members:
        is_eligible = all(
            (member[k] == conditions[k] for k in conditions.keys()))
        if not is_eligible:
            return False
    return True


def mark_eligiblity(tid, status):
    """Store a team's eligiblity status within their team document."""
    db = api.db.get_conn()
    db.teams.find_one_and_update(
        {'tid': tid}, {'$set': {'eligible': status}}
    )


def get_all_teams(include_ineligible=False, country=None):
    """
    Retrieve all teams.

    Args:
        include_ineligible: include ineligible teams in result
        country: optional country filter

    Returns:
        A list of all of the teams.

    """
    # Ignore empty teams (remnants of single player self-team ids)
    match = {"size": {"$gt": 0}}
    if country is not None:
        match.update({"country": country})

    db = api.db.get_conn()
    teams = list(db.teams.find(match, {"_id": 0}))

    # Filter out ineligible teams, if desired
    if not include_ineligible:
        teams = [t for t in teams if is_eligible(t['tid'])]
    return teams


def join_team(team_name, password, user):
    """
    Switch a user from their individual team to a proper team.

    You can not use this to freely switch between teams.

    Args:
        team_name: The name of the team to join
        password: The new team's password
        user: The user
    Returns:
        ID of the new team
    """
    current_team = api.user.get_team(uid=user["uid"])
    desired_team = api.team.get_team(name=team_name)

    if current_team["team_name"] != user["username"]:
        raise PicoException(
            "You can not switch teams once you have joined one.", 403)

    # Make sure the password is correct and there is room on the team
    max_team_size = api.config.get_settings()["max_team_size"]
    if desired_team['size'] >= max_team_size:
        raise PicoException(
            'That team is already at maximum capacity.', 403)
    if not api.user.confirm_password(password, desired_team["password"]):
        raise PicoException(
            'That is not the correct password to join that team.', 403)

    # Join the new team
    db = api.db.get_conn()
    user_team_update = db.users.find_and_modify(
        query={
            "uid": user["uid"],
            "tid": current_team["tid"]
        },
        update={"$set": {
            "tid": desired_team["tid"]
        }},
        new=True)

    if not user_team_update:
        raise PicoException("There was an issue switching your team!")

    # Update the sizes of the old and new teams
    db.teams.find_one_and_update(
        {"tid": desired_team["tid"]},
        {"$inc": {
            "size": 1
        }})

    db.teams.find_one_and_update(
        {"tid": current_team["tid"]},
        {"$inc": {
            "size": -1
        }})

    # If country is no longer consistent amongst members, set as mixed
    if user["country"] != desired_team["country"]:
        db.teams.update(
            {"tid": desired_team["tid"]}, {"$set": {"country": "??"}})

    # Remove old team from any groups and attempt to add new team
    previous_groups = get_groups(current_team['tid'])
    for group in previous_groups:
        api.group.leave_group(gid=group["gid"], tid=current_team["tid"])
        # Rejoin with new tid if not already member, and classroom
        # email filter is not enabled.
        if (desired_team['tid'] not in group['members'] and
                desired_team['tid'] not in group['teachers']):
            group_settings = api.group.get_group_settings(gid=group["gid"])
            if not group_settings["email_filter"]:
                api.group.join_group(
                    gid=group["gid"], tid=desired_team["tid"])

    # Immediately invalidate some caches

    cache.invalidate(api.stats.get_score, tid=desired_team['tid'])
    cache.invalidate(api.stats.get_score, uid=user['uid'])
    cache.invalidate(api.problem.get_unlocked_pids, desired_team['tid'])
    cache.invalidate(
        api.problem.get_solved_problems,
        tid=desired_team['tid'],
        uid=user['uid'],
        category=None)
    cache.invalidate(
        api.problem.get_solved_problems,
        tid=desired_team['tid'],
        uid=user['uid'])
    cache.invalidate(api.problem.get_solved_problems, tid=desired_team['tid'])
    cache.invalidate(api.problem.get_solved_problems, uid=user['uid'])
    cache.invalidate(
        api.stats.get_score_progression, tid=desired_team['tid'], category=None)
    cache.invalidate(api.stats.get_score_progression, tid=desired_team['tid'])

    return desired_team['tid']


@log_action
def update_password_request(params):
    """
    Update team password.

    Assumes args are keys in params.

    Args:
        params:
            new-password: the new password
            new-password-confirmation: confirmation of password
    """
    user = api.user.get_user()
    current_team = api.team.get_team(tid=user["tid"])
    if current_team["team_name"] == user["username"]:
        raise PicoException("You have not created a team yet.", 422)

    if params["new-password"] != params["new-password-confirmation"]:
        raise PicoException("Your team passwords do not match.", 422)

    db = api.db.get_conn()
    db.teams.update(
        {'tid': user['tid']},
        {'$set': {
            'password': api.common.hash_password(
                params["new-password"])
        }})


def is_teacher_team(tid):
    """Check if team is a teacher's self-team."""
    team = get_team(tid=tid)
    members = get_team_members(tid=tid)
    if (team["size"] == 1 and members[0]["username"] == team["team_name"] and
            members[0]["teacher"]):
        return True
    else:
        return False
