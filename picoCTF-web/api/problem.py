"""Module for interacting with the problems."""

from random import randint

import pymongo
from voluptuous import ALLOW_EXTRA, Range, Required, Schema

import api
from api import PicoException, check, validate

problem_schema = Schema({
    Required("name"):
    check(("The problem's display name must be a string.", [str])),
    Required("sanitized_name"):
    check(("The problems's sanitized name must be a string.", [str])),
    Required("score"):
    check(("Score must be a positive integer.", [int, Range(min=0)])),
    Required("author"):
    check(("Author must be a string.", [str])),
    Required("category"):
    check(("Category must be a string.", [str])),
    Required("instances"):
    check(("The instances must be a list.", [list])),
    Required("hints"):
    check(("Hints must be a list.", [list])),
    "walkthrough":
    check(("The problem walkthrough must be a string.", [str])),
    "description":
    check(("The problem description must be a string.", [str])),
    "version":
    check(("A version must be a string.", [str])),
    "tags":
    check(("Tags must be described as a list.", [list])),
    "organization":
    check(("Organization must be string.", [str])),
    "pkg_architecture":
    check(("Package architecture must be string.", [str])),
    "pkg_description":
    check(("Package description must be string.", [str])),
    "pkg_name":
    check(("Package name must be string.", [str])),
    "pkg_dependencies":
    check(("Package dependencies must be list.", [list])),
    "pip_requirements":
    check(("pip requirements must be list.", [list])),
    "pip_python_version":
    check(("Pip python version must be a string.", [str])),
    "pid":
    check(("You should not specify a pid for a problem.", [lambda _: False])),
    "_id":
    check(("Your problems should not already have _ids.", [lambda id: False]))
},
                        extra=ALLOW_EXTRA)

instance_schema = Schema({
    Required("description"):
    check(("The description must be a string.", [str])),
    Required("flag"):
    check(("The flag must be a string.", [str])),
    "port":
    check(("The port must be an int", [int])),
    "server":
    check(("The server must be a string.", [str]))
},
                         extra=True)


def get_all_categories():
    """
    Get the set of distinct problem categories.

    Returns:
        The set of distinct problem categories.

    """
    db = api.db.get_conn()
    # Do not return categories that only appear on disabled problems
    match = {"disabled": False}
    return db.problems.find(match).distinct("category")


def upsert_problem(problem, sid):
    """
    Add or update a problem.

    Args:
        problem: problem dict
        sid: shell server ID
    Returns:
        The created/updated problem ID.
    """
    db = api.db.get_conn()

    # Validate the problem object
    # @TODO it may make more sense to do this with e.g. Marshmallow at the
    #       routing level
    validate(problem_schema, problem)
    for instance in problem["instances"]:
        validate(instance_schema, instance)

    problem["pid"] = api.common.hash("{}-{}".format(problem["name"],
                                                    problem["author"]))
    # Initially disable problems
    problem["disabled"] = True

    # Assign instance IDs and server numbers
    server_number = api.shell_servers.get_server(sid)['server_number']
    for instance in problem["instances"]:
        instance["iid"] = api.common.hash(
            str(instance["instance_number"]) + sid + problem["pid"])
        instance["sid"] = sid
        if server_number is not None:
            instance["server_number"] = server_number

    if problem.get("walkthrough"):  # Falsy for None and empty string
        problem["has_walkthrough"] = True
    else:
        problem["has_walkthrough"] = False

    # If the problem already exists, update it instead
    existing = db.problems.find_one({'pid': problem['pid']}, {'_id': 0})
    if existing is not None:
        # Copy over instances on other shell servers from the existing version
        other_server_instances = [i for i in existing['instances']
                                  if i['sid'] != sid]
        problem['instances'].extend(other_server_instances)

        # Copy over the disabled state from the old problem, or
        # set to true if there are no instances
        problem["disabled"] = (existing["disabled"] or
                               len(problem["instances"]) == 0)

        db.problems.find_one_and_update(
            {'pid': problem['pid']},
            {'$set': problem})
        return problem['pid']

    db.problems.insert(problem)
    return problem['pid']


def assign_instance_to_team(pid, tid=None, reassign=False):
    """
    Assign an instance of problem pid to team tid.

    Args:
        pid: the problem id
        tid: the team id
        reassign: whether or not we should assign over an old assignment

    Returns:
        The iid that was assigned

    """
    team = api.team.get_team(tid=tid)
    problem = get_problem(pid)

    available_instances = problem["instances"]

    settings = api.config.get_settings()
    if settings["shell_servers"]["enable_sharding"]:
        available_instances = list(
            filter(
                lambda i: i.get("server_number") == team.get(
                    "server_number", 1), problem["instances"]))

    if pid in team["instances"] and not reassign:
        raise PicoException(
            "Team with tid {} already has an instance of pid {}.".format(
                tid, pid))

    if len(available_instances) == 0:
        if settings["shell_servers"]["enable_sharding"]:
            raise PicoException(
                "Your assigned shell server is currently down. " +
                "Please contact an admin.")
        else:
            raise PicoException(
                "Problem {} has no instances to assign.".format(pid))

    instance_number = randint(0, len(available_instances) - 1)
    iid = available_instances[instance_number]["iid"]

    team["instances"][pid] = iid

    db = api.db.get_conn()
    db.teams.update({"tid": tid}, {"$set": team})

    return instance_number


def get_instance_data(pid, tid):
    """
    Return the instance dictionary for the specified pid, tid pair.

    Args:
        pid: the problem id
        tid: the team id

    Returns:
        The instance dictionary

    """
    instance_map = api.team.get_team(tid=tid)["instances"]
    problem = get_problem(pid)

    if pid not in instance_map:
        iid = assign_instance_to_team(pid, tid)
    else:
        iid = instance_map[pid]

    for instance in problem["instances"]:
        if instance["iid"] == iid:
            return instance

    # Cannot find assigned instance. Reassign instance and recurse.
    assign_instance_to_team(pid, tid, reassign=True)
    return get_instance_data(pid, tid)


def filter_problem_instances(problem, tid):
    """
    Replace problem fields with those in a team's assigned instance.

    Also removes the original 'instances' field.

    Args:
        problem: the problem dict
        tid: the team id

    Returns:
        The filtered problem dict

    """
    instance = get_instance_data(problem['pid'], tid)
    problem.pop("instances")
    problem.update(instance)
    return problem


# @memoize
def get_problem(pid):
    """
    Get a single problem.

    Args:
        pid: The problem id

    Returns:
        The problem dictionary from the database or None if problem not found

    """
    db = api.db.get_conn()
    problem = db.problems.find_one({'pid': pid}, {'_id': 0})
    if api.user.is_logged_in() and api.user.get_user().get('admin', False):
        problem['reviews'] = api.problem_feedback.get_problem_feedback(
            pid=problem['pid'])
    return problem


def get_all_problems(category=None, show_disabled=False):
    """
    Get all of the problems, with optional filtering.

    Args:
        category (optional): Return only problems from this category
        show_disabled (optional): Include disabled problems

    Returns:
        List of problem dicts

    """
    db = api.db.get_conn()

    match = {}
    if category is not None:
        match.update({'category': category})

    if not show_disabled:
        match.update({'disabled': False})

    # Return all except objectID
    projection = {"_id": 0}

    problems = list(
        db.problems.find(match, projection).sort([('score', pymongo.ASCENDING),
                                                  ('name',
                                                   pymongo.ASCENDING)]))
    if api.user.is_logged_in() and api.user.get_user().get('admin', False):
        for problem in problems:
            problem['reviews'] = api.problem_feedback.get_problem_feedback(
                pid=problem['pid'])
    return problems


# @memoize
def get_solved_problems(tid=None, uid=None, category=None,
                        show_disabled=False):
    """
    Get the solved problems for a given team or user.

    Args:
        tid: The team id
        category: Optional parameter to restrict which problems are returned
    Returns:
        List of solved problem dictionaries
    """
    if uid is not None and tid is None:
        team = api.user.get_team(uid=uid)
    else:
        team = api.team.get_team(tid=tid)

    members = api.team.get_team_uids(tid=team["tid"])

    submissions = api.submissions.get_submissions(
        tid=tid, uid=uid, category=category, correctness=True)

    for uid in members:
        submissions += api.submissions.get_submissions(
            uid=uid, category=category, correctness=True)

    pids = []
    result = []

    # Team submissions will take precedence because they appear first
    # in the submissions list.
    for submission in submissions:
        if submission["pid"] not in pids:
            pids.append(submission["pid"])
            problem = get_problem(submission['pid'])
            problem.pop('flag', None)
            problem.pop('tags', None)
            problem.pop('files', None)
            problem['solved'] = True
            problem['unlocked'] = True
            problem["solve_time"] = submission["timestamp"]
            if not problem["disabled"] or show_disabled:
                result.append(problem)

    return result


def get_solved_pids(*args, **kwargs):
    """
    Get the solved pids for a given team or user.

    Args:
        tid: The team id
        category: Optional parameter to restrict which problems are returned
    Returns:
        List of solved problem ids
    """
    return [problem["pid"] for problem in get_solved_problems(*args, **kwargs)]


def is_problem_unlocked(problem, solved):
    """
    Check whether the specified problem is unlocked.

    A problem is unlocked if either:
        1. It has no dependencies in any of the bundles
        2. Its threshold is reached in all bundles that
           specify a dependency for it

    Args:
        problem: the problem object to check
        solved: the list of solved problem objects
    """
    unlocked = True

    for bundle in api.bundles.get_all_bundles():
        if problem["sanitized_name"] in bundle["problems"]:
            if "dependencies" in bundle and bundle["dependencies_enabled"]:
                if problem["sanitized_name"] in bundle["dependencies"]:
                    dependency = bundle["dependencies"][
                        problem["sanitized_name"]]
                    weightsum = sum(
                        dependency['weightmap'].get(p['sanitized_name'], 0)
                        for p in solved)
                    if weightsum < dependency['threshold']:
                        unlocked = False

    return unlocked


# @memoize
def get_unlocked_pids(tid):
    """
    Get the unlocked pids for a given team.

    Also assigns instances of unlocked problems to the team, if not present.

    Args:
        tid: The team id

    Returns:
        List of unlocked problem ids

    """
    # Note: Do NOT limit solved problems to category for proper weight count
    solved = get_solved_problems(tid)
    team = api.team.get_team(tid)

    unlocked = []
    for problem in get_all_problems():
        if is_problem_unlocked(problem, solved):
            unlocked.append(problem["pid"])

    for pid in unlocked:
        if pid not in team["instances"]:
            assign_instance_to_team(pid, tid)
    return unlocked


def load_published(data):
    """
    Load in the problems from the shell_manager publish blob.

    Args:
        data: The output of "shell_manager publish"
    """
    for problem in data["problems"]:
        upsert_problem(problem, sid=data["sid"])

    if "bundles" in data:
        for bundle in data["bundles"]:
            api.bundles.upsert_bundle(bundle)

    api.cache.clear()


def sanitize_problem_data(data):
    """
    Remove problem data specified in SANITATION_KEYS.

    Helps to eliminate leakage of unnecessary platform information to players.

    Args:
        data: dict or list of problems
    """
    SANITATION_KEYS = [
        "deployment_directory",
        "flag",
        "flag_sha1",
        "files",
        "iid",
        "instance_number",
        "pip_python_version",
        "pip_requirements",
        "pkg_dependencies",
        "service",
        "should_symlink",
        "sid",
        "tags",
        "user",
        "walkthrough",
    ]

    uid = api.user.get_user()["uid"]
    unlocked_walkthroughs = get_unlocked_walkthroughs(uid)

    def pop_keys(problem_dict):
        for key in SANITATION_KEYS:
            if key == "walkthrough":
                if (problem_dict["has_walkthrough"] and
                        problem_dict["pid"] not in unlocked_walkthroughs):
                    problem_dict["walkthrough"] = ""
            else:
                problem_dict.pop(key, None)

    if isinstance(data, list):
        for problem in data:
            pop_keys(problem)
    elif isinstance(data, dict):
        pop_keys(data)
    return data


def set_problem_availability(pid, disabled):
    """
    Update a problem's availability.

    A problem with no active instances cannot be disabled.

    Args:
        pid: the problem's pid
        disabled: whether or not the problem should be disabled.
    Returns:
        The pid of the updated problem, or None if it could not be found.

    """
    db = api.db.get_conn()
    success = db.problems.find_one_and_update(
        {'pid': pid}, {'$set': {'disabled': disabled}})
    if not success:
        return None
    else:
        api.cache.clear()
        return pid


def get_unlocked_walkthroughs(uid):
    """
    Return list of pids with unlocked walkthroughs.

    Walkthroughs are unlocked when a problem is solved by the user's team,
    or the user spends tokens to unlock.

    Args:
        uid: user id to look up
    """
    return get_solved_pids(uid=uid) + \
        api.user.get_user(uid=uid).get("unlocked_walkthroughs", [])


def unlock_walkthrough(uid, pid, cost):
    """
    Unlocks a problem at cost of tokens.

    Performed as atomic update to decrement tokens while also unlocking,
    also ensures against race conditions by validating token count and
    already-unlocked walkthroughs.

    Args:
        uid: user id
        pid: problem id
        cost: token cost of unlock
    """
    db = api.db.get_conn()
    db.users.update_one({
        'uid': uid,
        'tokens': {
            '$gte': cost
        },
        'unlocked_walkthroughs': {
            '$ne': pid
        }
    }, {
        '$push': {
            'unlocked_walkthroughs': pid
        },
        '$inc': {
            'tokens': (cost * -1)
        }
    })
