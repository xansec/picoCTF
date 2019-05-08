"""Module dealing with authentication to the API."""

import logging

import bcrypt
from flask import session
from voluptuous import Length, Required, Schema

import api.email
import api.user
import api.logger
from api.common import check, safe_fail, validate, WebException, PicoException

log = logging.getLogger(__name__)

user_login_schema = Schema({
    Required('username'):
    check(("Usernames must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]),),
    Required('password'):
    check(("Passwords must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]))
})


def confirm_password(attempt, password_hash):
    """
    Verify the password attempt.

    Args:
        attempt: the password attempt
        password_hash: the real password hash
    """
    return bcrypt.hashpw(attempt.encode('utf-8'),
                         password_hash) == password_hash


# @TODO clean up these exceptions
@api.logger.log_action
def login(username, password):
    """Authenticate a user."""
    # Read in submitted username and password
    validate(user_login_schema, {"username": username, "password": password})

    user = safe_fail(api.user.get_user, name=username, include_pw_hash=True)
    if user is None:
        raise WebException("Incorrect username.")

    if user.get("disabled", False):
        raise WebException("This account has been disabled.")

    if not user["verified"]:
        raise WebException("This account has not been verified yet.")

    if confirm_password(password, user['password_hash']):
        session['uid'] = user['uid']
        session.permanent = True
    else:
        raise PicoException('Incorrect password', 401)


@api.logger.log_action
def logout():
    """Clear the session."""
    session.clear()


def is_logged_in():
    """
    Check if the user is currently logged in.

    Returns:
        True if the user is logged in, false otherwise.

    """
    logged_in = "uid" in session
    if logged_in:
        user = safe_fail(api.user.get_user, uid=session["uid"])
        if not user or user["disabled"]:
            logout()
            return False
    return logged_in


def get_uid():
    """
    Get the user id from the session if it is logged in.

    Returns:
        The user id of the logged in user, or None

    """
    if is_logged_in():
        return session['uid']
    else:
        return None
