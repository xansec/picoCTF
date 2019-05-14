"""
Legacy API shim to support 2019 game.

Provides legacy behavior for:

/user/login
/user/logout
/user/status
/user/minigame
/user/clear_minigames
/user/extdata
/problems
/problems/submit
/problems/unlock_walkthrough
/problems/walkthrough?pid=<pid>
/problems/clear_walkthroughs
/team/score
"""
import hashlib
from datetime import datetime
from functools import wraps

from bson import json_util
from flask import Blueprint, request, session
from voluptuous import Length, Required, Schema

import api
from api import PicoException, check, validate

blueprint = Blueprint('v0_api', __name__)

user_login_schema = Schema({
    Required('username'):
    check(("Usernames must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]),),
    Required('password'):
    check(("Passwords must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]))
})


def WebSuccess(message=None, data=None):
    """Legacy successful response wrapper."""
    return json_util.dumps({
            'status': 1,
            'message': message,
            'data': data
        })


def WebError(message=None, data=None):
    """Legacy failure response wrapper."""
    return json_util.dumps({
            'status': 0,
            'message': message,
            'data': data
        })


def require_login(f):
    """Wrap routing functions that require a user to be logged in."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_logged_in():
            return WebError("You must be logged in")
        return f(*args, **kwds)

    return wrapper


def check_csrf(f):
    """Wrap routing functions that require a CSRF token."""
    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        if 'token' not in session:
            return WebError("CSRF token not in session")
        if 'token' not in request.form:
            return WebError("CSRF token not in form")
        if session['token'] != request.form['token']:
            return WebError("CSRF token is not correct")
        return f(*args, **kwds)
    return wrapper


def block_before_competition():
    """Wrap routing functions that are blocked prior to the competition."""
    def decorator(f):
        """Inner decorator."""
        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() > api.config.get_settings(
            )["start_time"].timestamp():
                return f(*args, **kwds)
            else:
                return WebError("The competition has not begun yet!")
        return wrapper
    return decorator


def block_after_competition():
    """Wrap routing functions that are blocked after the competition."""
    def decorator(f):
        """Inner decorator."""
        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() < api.config.get_settings(
            )["end_time"].timestamp():
                return f(*args, **kwds)
            else:
                return WebError("The competition is over!")
        return wrapper
    return decorator


@blueprint.route('/user/login', methods=['POST'])
def login_hook():
    """Legacy login route."""
    username = request.form.get('username')
    password = request.form.get('password')
    validate(user_login_schema, {"username": username, "password": password})
    try:
        api.user.login(username, password)
    except PicoException as e:
        return WebError(
            message=e.message
        )
    return WebSuccess(
        message="Successfully logged in as " + username,
        data={
            'teacher': api.user.is_teacher(),
            'admin': api.user.is_admin()
        }), 200


@blueprint.route('/user/logout', methods=['GET'])
def logout_hook():
    """Legacy logout route."""
    if api.user.is_logged_in():
        api.user.logout()
        return WebSuccess("Successfully logged out."), 200
    else:
        return WebError("You do not appear to be logged in."), 400


@blueprint.route('/user/status', methods=['GET'])
def status_hook():
    """Legacy status route."""
    settings = api.config.get_settings()
    user = None
    is_logged_in = api.user.is_logged_in()
    if is_logged_in:
        user = api.user.get_user()
    status = {
        "logged_in":
        is_logged_in,
        "admin":
        is_logged_in and user.get('admin', False),
        "teacher":
        is_logged_in and user.get('teacher', False),
        "enable_feedback":
        settings["enable_feedback"],
        "enable_captcha":
        settings["captcha"]["enable_captcha"],
        "reCAPTCHA_public_key":
        settings["captcha"]["reCAPTCHA_public_key"],
        "competition_active":
        api.config.check_competition_active(),
        "username":
        user['username'] if is_logged_in else "",
        "tid":
        user["tid"] if is_logged_in else "",
        "email_verification":
        settings["email"]["email_verification"],
    }

    if is_logged_in:
        team = api.user.get_team()
        status["team_name"] = team["team_name"]
        status["score"] = api.stats.get_score(tid=team["tid"])
        status["unlocked_walkthroughs"] = user.get("unlocked_walkthroughs", [])
        status["completed_minigames"] = user.get("completed_minigames", [])
        status["tokens"] = user.get("tokens", 0)

    return WebSuccess(data=status), 200


@blueprint.route('/user/extdata', methods=['GET'])
@require_login
def get_extdata_hook():
    """Return user extdata, or empty JSON object if unset."""
    user = api.user.get_user(uid=None)
    return WebSuccess(data=user['extdata']), 200


@blueprint.route('/user/extdata', methods=['PUT'])
@check_csrf
@require_login
def update_extdata_hook():
    """
    Set user extdata via HTTP form. Takes in any key-value pairs.

    An optional nonce may be included in payload, which will then
    be evaluated against the previous nonce, if it exists.

    If no nonce is included, default behavior is to over-write.
    """
    data = api.common.flat_multi(request.form)
    prev_nonce = int(api.user.get_user()["extdata"].get("nonce", 0))
    nonce = data.get("nonce")
    if nonce is not None and int(nonce) < prev_nonce:
        return WebError("Session expired. Please reload your client.")
    else:
        data.pop("token", None)
        api.user.update_extdata(data)
        return WebSuccess("Your extdata has been successfully updated.")


@blueprint.route("/user/minigame", methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def request_minigame_completion_hook():
    """Mark a minigame as completed and award tokens to the user."""
    minigame_id = request.form.get('mid')
    validation = request.form.get('v')

    if minigame_id is None or validation is None:
        return WebError("Invalid input!")

    settings = api.config.get_settings()
    minigame_config = settings.get("minigame", {}).get("token_values", 0)

    if minigame_id not in minigame_config:
        return WebError("Invalid input!")

    user = api.user.get_user()

    hashstring = minigame_id + user["username"] + \
        settings.get("minigame", {}).get("secret")

    if hashlib.md5(hashstring.encode('utf-8')).hexdigest() != validation:
        return WebError("Invalid input!")

    if minigame_id not in user.get("completed_minigames"):
        tokens_earned = minigame_config[minigame_id]
        db = api.common.get_conn()

        db.users.update_one({
            'uid': user["uid"],
            'completed_minigames': {
                '$ne': minigame_id
            }
        }, {
            '$push': {
                'completed_minigames': minigame_id
            },
            '$inc': {
                'tokens': tokens_earned
            }
        })
        token_count = api.user.get_user()["tokens"]
        return WebSuccess(
            message="You win! You have earned " + str(tokens_earned) +
                    " tokens.",
            data={"tokens": token_count}
        )
    else:
        return WebError(
            message="You win! You have already completed this minigame, " +
                    "so you have not earned additional tokens.",
            data={"tokens": user["tokens"]},
        )


@blueprint.route("/user/clear_minigames", methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def request_minigame_clear_hook():
    """Clear completed minigame progress."""
    # if DEBUG_KEY is not None:

    db = api.common.get_conn()
    db.users.update_one({
        'uid': api.user.get_user()["uid"],
    }, {
        '$set': {
            'completed_minigames': []
        },
    })
    return WebSuccess("Minigame progress cleared.")


@blueprint.route('/problems', methods=['GET'])
@require_login
@block_before_competition()
def get_visible_problems_hook():
    """Legacy problems endpoint."""
    tid = api.user.get_user()['tid']
    all_problems = api.problem.get_all_problems(show_disabled=False)
    unlocked_pids = api.problem.get_unlocked_pids(tid)
    solved_pids = api.problem.get_solved_pids(tid=tid)

    visible_problems = []
    for problem in all_problems:
        if problem["pid"] in unlocked_pids:
            problem = api.problem.filter_problem_instances(problem, tid)
            problem.pop('flag', None)
            problem.pop('tags', None)
            problem.pop('files', None)
            problem['solved'] = problem["pid"] in solved_pids
            problem['unlocked'] = True
            visible_problems.append(problem)
    for problem in visible_problems:
        problem['solves'] = api.stats.get_problem_solves(problem['pid'])
    return WebSuccess(
        data=api.problem.sanitize_problem_data(visible_problems)), 200


@blueprint.route('/problems/submit', methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
@block_after_competition()
def submit_key_hook():
    """Legacy solution submission endpoint."""
    user_account = api.user.get_user()
    tid = user_account['tid']
    uid = user_account['uid']
    pid = request.form.get('pid', '')
    key = request.form.get('key', '')
    method = request.form.get('method', '')
    ip = request.remote_addr

    (correct, previously_solved_by_user,
     previously_solved_by_team) = api.submissions.submit_key(
            tid, pid, key, method, uid, ip)

    if correct and not previously_solved_by_team:
        return WebSuccess("That is correct!"), 200
    elif not correct and not previously_solved_by_team:
        return WebError("That is incorrect!"), 200
    elif correct and previously_solved_by_user:
        return WebSuccess(
            'Flag correct: however, you have already solved ' +
            'this problem.'
        ), 200
    elif correct and previously_solved_by_team:
        return WebSuccess(
            'Flag correct: however, your team has already received points ' +
            'for this flag.'
        ), 200
    elif not correct and previously_solved_by_user:
        return WebError(
            'Flag incorrect: please note that you have ' +
            'already solved this problem.'
        ), 200
    elif not correct and previously_solved_by_team:
        return WebError(
            'Flag incorrect: please note that someone on your team has ' +
            'already solved this problem.'
        ), 200


@blueprint.route('/team/score', methods=['GET'])
@require_login
def get_team_score_hook():
    """Legacy score endpoint."""
    score = api.stats.get_score(tid=api.user.get_user()['tid'])
    if score is not None:
        return WebSuccess(data={'score': score})
    return WebError("There was an error retrieving your score."), 500


@blueprint.route("/problems/walkthrough", methods=['GET'])
@require_login
@block_before_competition()
def request_problem_walkthrough_hook():
    """Get the walkthrough for a problem, if the user has unlocked it."""
    pid = request.args.get("pid")

    if pid is None:
        return WebError("Please supply a pid.")

    uid = api.user.get_user()["uid"]

    problem = api.problem.get_problem(pid=pid)
    if problem.get("walkthrough") is None:
        return WebError("This problem does not have a walkthrough!")
    else:
        if pid not in api.problem.get_unlocked_walkthroughs(uid):
            return WebError("You haven't unlocked this walkthrough yet!")
        else:
            return WebSuccess(problem["walkthrough"])


@blueprint.route("/problems/unlock_walkthrough", methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def request_walkthrough_unlock_hook():
    """Attempt to unlock the walkthrough for a problem by spending tokens."""
    pid = request.form.get('pid')

    if pid is None:
        return WebError("Please supply a pid.")

    user = api.user.get_user()

    uid = user["uid"]
    if pid in api.problem.get_unlocked_walkthroughs(uid):
        return WebError("You have already unlocked this walkthrough!")

    problem = api.problem.get_problem(pid=pid)
    if problem.get("walkthrough") is None:
        return WebError("This problem does not have a walkthrough!")
    else:
        if user.get("tokens", 0) >= problem["score"]:
            api.problem.unlock_walkthrough(uid, pid, problem["score"])
            return WebSuccess("Walkthrough unlocked.")
        else:
            return WebError(
                "You do not have enough tokens to unlock this walkthrough!")


@blueprint.route("/problems/clear_walkthroughs", methods=['POST'])
@check_csrf
@require_login
@block_before_competition()
def request_clear_walkthroughs_hook():
    """Clear the user's unlocked walkthroughs."""
    # if DEBUG_KEY is not None:

    db = api.common.get_conn()
    db.users.update_one({
        'uid': api.user.get_user()["uid"]
    }, {
        '$set': {
            'unlocked_walkthroughs': []
        },
    })
    return WebSuccess("Walkthroughs cleared.")
