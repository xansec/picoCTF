"""API functions relating to admin users."""

import pymongo

import api.cache
import api.db
import api.problem
import api.user
from api.common import WebException


def give_admin_role(name=None, uid=None):
    """
    Grant a particular user admin privileges.

    There is no option to give a particular user admin privileges by default.

    Args:
        name: the user's name
        uid: the user's id
    """
    db = api.db.get_conn()

    user = api.user.get_user(name=name, uid=uid)
    db.users.update({
        "uid": user["uid"]
    }, {"$set": {
        "admin": True,
        "teacher": True
    }})


def give_teacher_role(name=None, uid=None):
    """
    Grant a particular user teacher privileges.

    Args:
        name: the user's name
        uid: the user's id
    """
    db = api.db.get_conn()

    user = api.user.get_user(name=name, uid=uid)
    db.users.update({"uid": user["uid"]}, {"$set": {"teacher": True}})


def set_problem_availability(pid, disabled):
    """
    Update a problem's availability.

    A problem with no active instances cannot be disabled.

    Args:
        pid: the problem's pid
        disabled: whether or not the problem should be disabled.
    Returns:
        The updated problem object.

    """
    problem = api.problem.get_problem(pid=pid)
    if len(problem['instances']) < 1:
        raise WebException(
            "You cannot change the availability of \"{}\".".format(
                problem["name"]))
    result = api.problem.update_problem(pid, {"disabled": disabled})
    api.cache.clear_all()
    return result


def get_api_exceptions(result_limit=50, sort_direction=pymongo.DESCENDING):
    """
    Retrieve api exceptions.

    Args:
        result_limit: the maximum number of exceptions to return.
        sort_direction: pymongo.ASCENDING or pymongo.DESCENDING
    """
    db = api.db.get_conn()

    results = db.exceptions.find({
        "visible": True
    }).sort([("time", sort_direction)]).limit(result_limit)
    return list(results)


def dismiss_api_exceptions(trace):
    """
    Remove exceptions from the management tab.

    Args:
        trace: the exception trace
    """
    db = api.db.get_conn()
    db.exceptions.remove({"trace": trace})
