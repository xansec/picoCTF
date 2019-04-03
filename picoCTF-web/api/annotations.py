""" API annotations and assorted wrappers. """

import logging
import traceback
from datetime import datetime
from functools import wraps

import api.auth
import api.config
import api.user
from api.common import (InternalException, SevereInternalException, WebError,
                        WebException)
from bson import json_util
from flask import request, session

write_logs_to_db = False  # Default value, can be overwritten by api.py

log = logging.getLogger(__name__)

_get_message = lambda exception: exception.args[0]


def log_action(f):
    """
    Logs a given request if available.
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        """
        Provides contextual information to the logger.
        """

        log_information = {
            "name": "{}.{}".format(f.__module__, f.__name__),
            "args": args,
            "kwargs": kwds,
            "result": None,
        }

        try:
            log_information["result"] = f(*args, **kwds)
        except WebException as error:
            log_information["exception"] = _get_message(error)
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
    """
    Wraps routing functions that require a user to be logged in
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.auth.is_logged_in():
            raise WebException("You must be logged in")
        return f(*args, **kwds)

    return wrapper

def require_teacher(f):
    """
    Wraps routing functions that require a user to be a teacher
    """

    @require_login
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_teacher() or not api.config.get_settings(
        )["enable_teachers"]:
            raise WebException("You must be a teacher!")
        return f(*args, **kwds)

    return wrapper


def check_csrf(f):

    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        if 'token' not in session:
            raise InternalException("CSRF token not in session")
        if 'token' not in request.form:
            raise InternalException("CSRF token not in form")
        if session['token'] != request.form['token']:
            raise InternalException("CSRF token is not correct")
        return f(*args, **kwds)

    return wrapper


def deny_blacklisted(f):

    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        # if auth.is_blacklisted(session['tid']):
        #    abort(403)
        return f(*args, **kwds)

    return wrapper


def require_admin(f):
    """
    Wraps routing functions that require a user to be an admin
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_admin():
            raise WebException("You do not have permission to view this page.")
        return f(*args, **kwds)

    return wrapper


def block_before_competition(return_result):
    """
    Wraps a routing function that should be blocked before the start time of the competition
    """

    def decorator(f):
        """
        Inner decorator
        """

        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() > api.config.get_settings(
            )["start_time"].timestamp():
                return f(*args, **kwds)
            else:
                return return_result

        return wrapper

    return decorator


def block_after_competition(return_result):
    """
    Wraps a routing function that should be blocked after the end time of the competition
    """

    def decorator(f):
        """
        Inner decorator
        """

        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() < api.config.get_settings(
            )["end_time"].timestamp():
                return f(*args, **kwds)
            else:
                return return_result

        return wrapper

    return decorator
