"""API annotations and assorted wrappers."""

import logging
from datetime import datetime
from functools import wraps

from bson import json_util
from flask import request, session

import api.auth
import api.config
import api.user
from api.common import InternalException, WebError, WebException

log = logging.getLogger(__name__)


def log_action(f):
    """Log a function invocation and its result."""
    @wraps(f)
    def wrapper(*args, **kwds):
        """Provide contextual information to the logger."""
        log_information = {
            "name": "{}.{}".format(f.__module__, f.__name__),
            "args": args,
            "kwargs": kwds,
            "result": None,
        }
        try:
            log_information["result"] = f(*args, **kwds)
        except WebException as error:
            log_information["exception"] = error.args[0]
            raise
        finally:
            log.info(log_information)
        return log_information["result"]

    return wrapper


def jsonify(f):
    """Convert response data to JSON."""
    @wraps(f)
    def wrapper(*args, **kwds):
        return json_util.dumps(f(*args, **kwds))

    return wrapper


def require_login(f):
    """Wrap routing functions that require a user to be logged in."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.auth.is_logged_in():
            raise WebException("You must be logged in")
        return f(*args, **kwds)

    return wrapper


def require_teacher(f):
    """Wrap routing functions that require a user to be a teacher."""
    @require_login
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_teacher():
            raise WebException("You do not have permission to view this page.")
        return f(*args, **kwds)

    return wrapper


def require_admin(f):
    """Wrap routing functions that require a user to be an admin."""
    @require_login
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_admin():
            raise WebException("You do not have permission to view this page.")
        return f(*args, **kwds)

    return wrapper


def check_csrf(f):
    """Wrap routing functions that require a CSRF token."""
    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        if 'token' not in session:
            raise InternalException("CSRF token not in session")
        if 'token' not in request.form:
            raise WebException("CSRF token not in form")
        if session['token'] != request.form['token']:
            raise WebException("CSRF token is not correct")
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
