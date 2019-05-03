"""Module for handling problem feedback."""

from datetime import datetime

from voluptuous import Length, Required, Schema

import api.achievement
import api.auth
import api.db
import api.logger
import api.problem
import api.user
from api.common import check, validate, PicoException

feedback_schema = Schema({
    Required("liked"):
    check(("liked must be a boolean", [lambda x: type(x) == bool])),
    "comment":
    check(("The comment must be no more than 500 characters",
           [str, Length(max=500)])),
    "timeSpent":
    check(("Time spend must be a number", [int])),
    "source":
    check(("The source must be no more than 500 characters",
           [str, Length(max=10)]))
})


def get_problem_feedback(pid=None, tid=None, uid=None):
    """
    Retrieve feedback for a given problem, team, or user.

    Args:
        pid: the problem id
        tid: the team id
        uid: the user id
    Returns:
        A list of problem feedback entries.
    """
    db = api.db.get_conn()
    match = {}

    if pid is not None:
        match.update({"pid": pid})
    if tid is not None:
        match.update({"tid": tid})
    if uid is not None:
        match.update({"uid": uid})

    return list(db.problem_feedback.find(match, {"_id": 0}))


@api.logger.log_action
def upsert_feedback(pid, feedback):
    """
    Add or update problem feedback in the database.

    Args:
        pid: the problem id
        feedback: the problem feedback.
    Raises:
        PicoException if provided pid does not exist
    """
    db = api.db.get_conn()

    uid = api.auth.get_uid()

    # Make sure the problem actually exists.
    if not api.problem.get_problem(pid):
        raise PicoException('Problem not found', 404)

    team = api.user.get_team(uid=uid)
    solved = pid in api.problem.get_solved_pids(tid=team["tid"])

    validate(feedback_schema, feedback)

    # update feedback if already present
    if get_problem_feedback(pid=pid, uid=uid) != []:
        db.problem_feedback.update({
            "pid": pid,
            "uid": uid
        }, {"$set": {
            "timestamp": datetime.utcnow(),
            "feedback": feedback
        }})
    else:
        db.problem_feedback.insert({
            "pid": pid,
            "uid": uid,
            "tid": team["tid"],
            "solved": solved,
            "timestamp": datetime.utcnow(),
            "feedback": feedback
        })

        api.achievement.process_achievements("review", {
            "uid": uid,
            "tid": team['tid'],
            "pid": pid
        })
