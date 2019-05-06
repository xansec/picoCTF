"""User management and registration module."""

import json
import re
import string
import urllib.parse
import urllib.request

import flask
from voluptuous import Length, Required, Schema

import api.auth
import api.common
import api.config
import api.db
import api.email
import api.group
import api.team
import api.token
import api.user
import api.logger
from api.common import (InternalException, safe_fail, validate,
                        WebException, PicoException)


def check_blacklisted_usernames(username):
    """
    Verify that the username isn't present in the username blacklist.

    Args:
        username: the username to check
    """
    settings = api.config.get_settings()
    return username not in settings.get(
        "username_blacklist",
        api.config.default_settings["username_blacklist"])


def verify_email_in_whitelist(email, whitelist=None):
    """
    Verify that the email address passes the global whitelist if one exists.

    Args:
        email: The email address to verify
    """
    if whitelist is None:
        settings = api.config.get_settings()
        whitelist = settings["email_filter"]

    # Nothing to check against!
    if len(whitelist) == 0:
        return True

    for email_domain in whitelist:
        if re.match(r".*?@{}$".format(email_domain), email) is not None:
            return True

    return False


def get_team(uid=None):
    """
    Retrieve the the corresponding team to the user's uid.

    Args:
        uid: user's userid
    Returns:
        The user's team.
    """
    user = get_user(uid=uid)
    return api.team.get_team(tid=user["tid"])


def get_user(name=None, uid=None):
    """
    Retrieve a user based on a property, or the current user, if logged in.

    Args:
        name: the user's username
        uid: the user's uid
    Returns:
        Returns the corresponding user object or None if it could not be found
    """
    db = api.db.get_conn()

    match = {}

    if uid is not None:
        match.update({'uid': uid})
    elif name is not None:
        match.update({'username': name})
    elif api.auth.is_logged_in():
        match.update({'uid': api.auth.get_uid()})
    else:
        raise InternalException("uid or name must be specified for get_user")

    user = db.users.find_one(match)

    if user is None:
        raise InternalException("User does not exist")

    return user


def get_all_users():
    """
    Find all users in the database.

    Returns:
        Returns all user dicts.

    """
    db = api.db.get_conn()
    return list(db.users.find({}, {'_id': 0}))


def _validate_captcha(data):
    """
    Validate a captcha with google's reCAPTCHA.

    Args:
        data: the posted form data
    """
    settings = api.config.get_settings()["captcha"]

    post_data = urllib.parse.urlencode({
        "secret":
        settings['reCAPTCHA_private_key'],
        "response":
        data["g-recaptcha-response"],
        "remoteip":
        flask.request.remote_addr
    }).encode("utf-8")

    request = urllib.request.Request(
        settings['captcha_url'], post_data, method='POST')
    response = urllib.request.urlopen(request).read().decode("utf-8")
    parsed_response = json.loads(response)
    return parsed_response['success'] is True


@api.logger.log_action
def add_user(params):
    """
    Register a new user and creates a team for them automatically.

    Assume arguments to be specified in a dict.

    Args:
        params:
            username: user's username
            password: user's password
            firstname: user's first name
            lastname: user's first name
            email: user's email
            country: 2-digit country code
            affiliation: user's affiliation
            usertype: "student", "teacher" or other
            demo: arbitrary dict of demographic data
            gid (optional): group registration
            rid (optional): registration id
    """
    # Make sure the username is unique
    db = api.db.get_conn()
    if db.users.find_one({'username': params['username']}):
        raise PicoException(
            'There is already a user with this username.', 409)
    if db.teams.find_one({'team_name': params['username']}):
        raise PicoException(
            'There is already a team with this username.', 409)

    # If gid is specified, force affiliation to that team's name
    email_whitelist = None
    if params.get("gid", None):
        group = api.group.get_group(gid=params["gid"])
        group_settings = api.group.get_group_settings(gid=group["gid"])
        params["affiliation"] = group["name"]
        email_whitelist = group_settings["email_filter"]

    # If rid is specified and gid and email match,
    # get teacher status from registration token.
    # Additionally, invited users are automatically validated.
    user_is_teacher = params["usertype"] == "teacher"
    user_was_invited = False
    if params.get("rid", None):
        key = api.token.find_key_by_token("registration_token", params["rid"])
        if params.get("gid") != key["gid"]:
            raise PicoException(
                "Registration token group and supplied gid do not match.")
        if params["email"] != key["email"]:
            raise PicoException(
                "Registration token email does not match the supplied one.")
        user_is_teacher = key["teacher"]
        user_was_invited = True
        api.token.delete_token(key, "registration_token")

    # If not invited, validate the user's email against the whitelist
    else:
        if not verify_email_in_whitelist(params["email"], email_whitelist):
            raise PicoException(
                "Your email does not belong to the whitelist. " +
                "Please see the registration form for details.")

    # If CAPTCHAs are enabled, validate the submission
    if (api.config.get_settings()["captcha"]["enable_captcha"] and not
            _validate_captcha(params)):
        raise PicoException("Incorrect captcha!")

    # Create a team for the new user and set its count to 1
    tid = api.team.create_team({
        "team_name": params["username"],
        "password": api.common.token(),
        "affiliation": params["affiliation"],
        "country": params["country"]
    })
    db.teams.update_one(
        {'tid': tid},
        {'$set': {
            'size': 1
        }}
    )

    # The first registered user automatically becomes an admin
    user_is_admin = False
    if db.users.count() == 0:
        user_is_admin = True
        user_is_teacher = True

    # Insert the new user in the DB
    uid = api.common.token()
    settings = api.config.get_settings()
    db.users.insert_one({
        'uid': uid,
        'firstname': params['firstname'],
        'lastname': params['lastname'],
        'username': params['username'],
        'email': params['email'],
        'password_hash': api.common.hash_password(params["password"]),
        'tid': tid,
        'usertype': params['usertype'],
        'country': params['country'],
        'demo': params['demo'],
        'teacher': user_is_teacher,
        'admin': user_is_admin,
        'disabled': False,
        'verified': (not settings["email"]["email_verification"] or
                     user_was_invited),
        'extdata': {},
    })

    # If gid was specified, add the newly created team to the group
    if params.get("gid", None):
        api.group.join_group(
            params["gid"], tid, teacher=user_is_teacher)

    # If email verification is enabled and user wasn't invited, send
    # validation email
    if settings["email"]["email_verification"] and not user_was_invited:
        api.email.send_user_verification_email(params['username'])

    return uid


def is_teacher(uid=None):
    """
    Determine if a user is a teacher.

    Args:
        uid: user's uid
    Returns:
        True if the user is a teacher, False otherwise
    """
    user = get_user(uid=uid)
    return user.get('teacher', False)


def is_admin(uid=None):
    """
    Determine if a user is an admin.

    Args:
        uid: user's uid
    Returns:
        True if the user is an admin, False otherwise
    """
    user = get_user(uid=uid)
    return user.get('admin', False)


def verify_user(uid, token_value):
    """
    Verify an unverified user account.

    Link should have been sent to the user's email.

    Args:
        uid: the user id
        token_value: the verification token value
    Returns:
        True if successful verification based on the (uid, token_value)
    """
    db = api.db.get_conn()

    if uid is None:
        raise InternalException("You must specify a uid.")

    token_user = api.token.find_key_by_token("email_verification", token_value)

    if token_user["uid"] == uid:
        db.users.find_and_modify({"uid": uid}, {"$set": {"verified": True}})
        api.token.delete_token({"uid": uid}, "email_verification")
        return True
    else:
        raise InternalException("This is not a valid token for your user.")


@api.logger.log_action
def update_password_request(params, uid=None, check_current=False):
    """
    Update account password.

    Assumes args are keys in params.

    Args:
        uid: uid to reset
        check_current: whether to ensure that current-password is correct
        params (dict):
            current-password: the users current password
            new-password: the new password
            new-password-confirmation: confirmation of password
    """
    user = get_user(uid=uid)

    if check_current and not api.auth.confirm_password(
            params["current-password"], user['password_hash']):
        raise WebException("Your current password is incorrect.")

    if params["new-password"] != params["new-password-confirmation"]:
        raise WebException("Your passwords do not match.")

    if len(params["new-password"]) == 0:
        raise WebException("Your password cannot be empty.")

    update_password(user['uid'], params["new-password"])


def update_password(uid, password):
    """
    Update an account's password.

    Args:
        uid: user's uid.
        password: the new user unhashed password.
    """
    db = api.db.get_conn()
    db.users.update(
        {'uid': uid},
        {'$set': {
            'password_hash': api.common.hash_password(password)
        }})


def disable_account(uid):
    """
    Disable a user account.

    They will no longer be able to login and no longer count towards their
    team's maximum size limit.

    Args:
        uid: user's uid
    """
    db = api.db.get_conn()
    result = db.users.update({
        "uid": uid,
        "disabled": False
    }, {"$set": {
        "disabled": True
    }})

    tid = api.user.get_team(uid=uid)["tid"]

    # Making certain that we have actually made a change.
    # result["n"] refers to how many documents have been updated.
    if result["n"] == 1:
        db.teams.find_and_modify(
            query={
                "tid": tid,
                "size": {
                    "$gt": 0
                }
            },
            update={"$inc": {
                "size": -1
            }},
            new=True)


@api.logger.log_action
def disable_account_request(params, uid=None, check_current=False):
    """
    Disable user account so they can't login or consume space on a team.

    Args:
        uid: uid to reset
        check_current: whether to ensure that current-password is correct
        params (dict):
            current-password: the users current password
    """
    user = get_user(uid=uid)

    if check_current and not api.auth.confirm_password(
            params["current-password"], user['password_hash']):
        raise WebException("Your current password is incorrect.")
    disable_account(user['uid'])

    api.auth.logout()


def update_extdata(params):
    """
    Update user extdata.

    Assumes args are keys in params.

    Args:
        params:
            (any)
    """
    user = get_user(uid=None)
    db = api.db.get_conn()
    params.pop('token', None)
    db.users.update_one({'uid': user['uid']}, {'$set': {'extdata': params}})
