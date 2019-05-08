"""Manage loggers for the API."""

import logging
import logging.handlers
import time
from datetime import datetime
from functools import wraps

import pymongo
from flask import has_request_context
from flask import logging as flask_logging
from flask import request

import api.config
import api.db
import api.team
import api.user
from api.common import WebException

critical_error_timeout = 600
log = logging.getLogger(__name__)


class StatsHandler(logging.StreamHandler):
    """Logs statistical information into the mongodb."""

    time_format = "%H:%M:%S %Y-%m-%d"

    action_parsers = {
        "api.user.create_user_request":
            lambda params, result=None: {
                "username": params["username"]
            },
        "api.achievement.process_achievement":
            lambda aid, data, result=None: {
                "aid": aid,
                "success": result[0]
            },
        "api.autogen.grade_problem_instance":
            lambda pid, tid, key, result=None: {
                "pid": pid,
                "key": key,
                "correct": result["correct"]
            },
        "api.group.create_group":
            lambda uid, group_name, result=None: {
                "name": group_name,
                "owner": uid
            },
        "api.group.join_group":
            lambda gid, tid, teacher=False, result=None: {
                "gid": gid,
                "tid": tid
            },
        "api.group.leave_group":
            lambda gid, tid, result=None: {
                "gid": gid,
                "tid": tid
            },
        "api.group.delete_group":
            lambda gid, result=None: {
                "gid": gid
            },

        # @TODO fix this
        "api.submissions.submit_key":
            lambda tid, pid, key, method, uid=None, ip=None, result=None: {
                "pid": pid,
                "key": key,
                "method": method,
                "success": result,
            },
        "api.problem_feedback.add_problem_feedback":
            lambda pid, uid, feedback, result=None: {
                "pid": pid,
                "feedback": feedback
            },
        "api.user.update_password_request":
            lambda params, uid=None, check_current=False, result=None: {},
        "api.team.update_password_request":
            lambda params, result=None: {},
        "api.email.request_password_reset":
            lambda username, result=None: {},
        "api.team.create_team":
            lambda params, result=None: params,
        "api.app.hint":
            lambda pid, source, result=None: {"pid": pid, "source": source}
    }

    def __init__(self):
        """Initialize the logger."""
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        """Store record into the db."""
        information = get_request_information()

        result = record.msg

        if type(result) == dict:

            information.update({
                "event": result["name"],
                "time": datetime.now()
            })

            information["pass"] = True
            information["action"] = {}

            if "exception" in result:

                information["action"]["exception"] = result["exception"]
                information["pass"] = False

            elif result["name"] in self.action_parsers:
                action_parser = self.action_parsers[result["name"]]

                result["kwargs"]["result"] = result["result"]
                action_result = action_parser(*result["args"],
                                              **result["kwargs"])

                information["action"].update(action_result)

            api.db.get_conn().statistics.insert(information)


class ExceptionHandler(logging.StreamHandler):
    """Logs exceptions into mongodb."""

    def __init__(self):
        """Initialize the logger."""
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        """Store record into the db."""
        information = get_request_information()

        information.update({
            "id": api.common.token(),
            "time": datetime.now(),
            "trace": record.msg,
            "visible": True
        })

        api.db.get_conn().exceptions.insert(information)


class SevereHandler(logging.handlers.SMTPHandler):
    """An email logger for severe exceptions."""

    messages = {}

    def __init__(self):
        """Initialize the logger."""
        settings = api.config.get_settings()
        logging.handlers.SMTPHandler.__init__(
            self,
            mailhost=settings["email"]["smtp_url"],
            fromaddr=settings["email"]["from_addr"],
            toaddrs=settings["logging"]["admin_emails"],
            subject="Critical Error in {}".format(
                settings["competition_name"]),
            credentials=(settings["email"]["email_username"],
                         settings["email"]["email_password"]),
            secure=())

    def emit(self, record):
        """Store record into the db."""
        # Don't excessively emit the same message.
        last_time = self.messages.get(record.msg, None)
        if last_time is None or time.time(
        ) - last_time > api.config.get_settings()["critical_error_timeout"]:
            super(SevereHandler, self).emit(record)
            self.messages[record.msg] = time.time()


def get_request_information():
    """
    Return a dictionary of information about the user at the time of logging.

    Returns:
        The dictionary.

    """
    information = {}

    if has_request_context():
        information["request"] = {
            "api_endpoint_method": request.method,
            "api_endpoint": request.path,
            "ip": request.remote_addr,
            "platform": request.user_agent.platform,
            "browser": request.user_agent.browser,
            "browser_version": request.user_agent.version,
            "user_agent": request.user_agent.string
        }

        if api.user.is_logged_in():

            user = api.user.get_user()
            team = api.user.get_team()
            groups = api.team.get_groups(user['tid'])

            information["user"] = {
                "username": user["username"],
                "email": user["email"],
                "team_name": team["team_name"],
                "groups": [group["name"] for group in groups]
            }

    return information


def setup_logs(args):
    """
    Initialize the api loggers.

    Args:
        args: dict containing the configuration options.
    """
    flask_logging.create_logger = lambda app: logging.getLogger(
        app.logger_name)

    if not args.get("debug", True):
        logger = logging.getLogger("werkzeug")
        if logger:
            logger.setLevel(logging.ERROR)

    level = [logging.WARNING, logging.INFO, logging.DEBUG][min(
        args.get("verbose", 1), 2)]

    internal_error_log = ExceptionHandler()
    internal_error_log.setLevel(logging.ERROR)

    log.root.setLevel(level)
    log.root.addHandler(internal_error_log)

    if api.config.get_settings()["email"]["enable_email"]:
        severe_error_log = SevereHandler()
        severe_error_log.setLevel(logging.CRITICAL)
        log.root.addHandler(severe_error_log)

    stats_log = StatsHandler()
    stats_log.setLevel(logging.INFO)

    log.root.addHandler(stats_log)


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


def get_api_exceptions(result_limit=50):
    """
    Retrieve the most recent logged exceptions.

    Args:
        result_limit: the maximum number of exceptions to return.

    Returns:
        list of exception dicts

    """
    db = api.db.get_conn()
    results = db.exceptions.find({'visible': True}, {'_id': 0}).sort(
        [("time", pymongo.DESCENDING)]).limit(result_limit)
    return list(results)


def get_api_exception(exception_id):
    """
    Retrieve a specific exception.

    Args:
        exception_id: ID of the exception to retrieve.

    Returns:
        the specified exception dict, or None if not found

    """
    db = api.db.get_conn()
    return db.exceptions.find_one({'id': exception_id}, {'_id': 0})


def dismiss_api_exceptions(exception_id=None):
    """
    Dismiss logged exceptions.

    Args:
        id (optional): ID of the exception to dismiss. If not provided,
                       dismisses all logged exceptions.

    Returns:
        the number of dismissed exceptions

    """
    db = api.db.get_conn()
    match = {}
    if exception_id:
        match['id'] = exception_id
    res = db.exceptions.update_many(match, {'$set': {'visible': False}})
    return res.modified_count
