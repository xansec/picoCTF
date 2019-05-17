"""Module for handling flag submissions."""

from voluptuous import Length, Required, Schema

from datetime import datetime
import api
from api import check, validate, PicoException

submission_schema = Schema({
    Required("tid"):
    check(("This does not look like a valid tid.", [str, Length(max=100)])),
    Required("pid"):
    check(("This does not look like a valid pid.", [str, Length(max=100)])),
    Required("key"):
    check(("This does not look like a valid key.", [str, Length(max=100)]))
})

DEBUG_KEY = None


def grade_problem(pid, key, tid=None):
    """
    Grade the problem with its associated flag.

    Args:
        tid: tid if provided
        pid: problem's pid
        key: user's submission

    Returns:
        bool: whether the key is correct

    """
    if tid is None:
        tid = api.user.get_user()["tid"]

    instance = api.problem.get_instance_data(pid, tid)

    correct = instance['flag'] in key
    if not correct and DEBUG_KEY is not None:
        correct = DEBUG_KEY in key

    return correct


@api.logger.log_action
def submit_key(tid, pid, key, method, uid, ip=None):
    """
    User problem submission.

    Args:
        tid: user's team id
        pid: problem's pid
        key: answer text
        method: submission method (e.g. 'game')
        uid: user's uid
        ip: user's ip
    Returns:
        tuple: (correct, previously_solved_by_user,
                previously_solved_by_team)
    """
    db = api.db.get_conn()
    validate(submission_schema, {"tid": tid, "pid": pid, "key": key})

    if pid not in api.problem.get_unlocked_pids(tid):
        raise PicoException(
            "You can't submit flags to problems you haven't unlocked.", 422)

    previously_solved_by_user = db.submissions.find_one(
        filter={
            'pid': pid,
            'uid': uid,
            'correct': True
        }) is not None

    previously_solved_by_team = db.submissions.find_one(
        filter={
            'pid': pid,
            'tid': tid,
            'correct': True
        }) is not None

    correct = grade_problem(pid, key, tid)

    if not previously_solved_by_user:
        db.submissions.insert({
            'uid': uid,
            'tid': tid,
            'timestamp': datetime.utcnow(),
            'pid': pid,
            'ip': ip,
            'key': key,
            'method': method,
            'category': api.problem.get_problem(pid)['category'],
            'correct': correct,
        })

    # if correct and not previously_solved_by_user:
        # Immediately invalidate some caches
        # @TODO caching is planned to be reworked
        # api.stats.get_score(tid=tid, uid=uid)
        # api.stats.get_unlocked_pids(tid)
        # api.problem.get_solved_problems(tid=tid, uid=uid)
        # api.stats.get_score_progression(tid=tid, uid=uid)

        # @TODO achievement processing needs to be fixed/reviewed
        # api.achievement.process_achievements("submit", {
        #     "uid": uid,
        #     "tid": tid,
        #     "pid": pid
        # })

    return (correct, previously_solved_by_user, previously_solved_by_team)


def get_submissions(pid=None,
                    uid=None,
                    tid=None,
                    category=None,
                    correctness=None,
                    ):
    """
    Get the submissions from a team or user.

    Optional filters of pid or category.

    Args:
        uid: the user id
        tid: the team id

        category: category filter.
        pid: problem filter.
        correctness: correct filter
    Returns:
        A list of submissions from the given entity.
    """
    db = api.db.get_conn()

    match = {}

    if uid is not None:
        match.update({"uid": uid})
    elif tid is not None:
        match.update({"tid": tid})

    if pid is not None:
        match.update({"pid": pid})

    if category is not None:
        match.update({"category": category})

    if correctness is not None:
        match.update({"correct": correctness})

    return list(db.submissions.find(match, {"_id": 0}))


def clear_all_submissions():
    """Remove all submissions from the database."""
    if DEBUG_KEY is not None:
        db = api.db.get_conn()
        db.submissions.remove()
        api.cache.clear()
    else:
        raise PicoException("Debug mode must be enabled", 500)
