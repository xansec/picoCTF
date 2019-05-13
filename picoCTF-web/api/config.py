"""Stores and retrieves runtime settings from the database."""

import datetime
from functools import wraps

import api
from api import PicoException

"""
Default Settings

These are the default settings that will be loaded
into the database if no settings are already loaded.
"""
default_settings = {
    "enable_feedback": True,

    # TIME WINDOW
    "start_time": datetime.datetime.utcnow(),
    "end_time": datetime.datetime.utcnow(),

    # COMPETITION INFORMATION
    "competition_name": "",
    "competition_url": "",

    # EMAIL WHITELIST
    "email_filter": [],

    # TEAMS
    "max_team_size": 1,

    # ACHIEVEMENTS
    "achievements": {
        "enable_achievements": True,
        "processor_base_path": "./achievements",
    },
    "username_blacklist": [
        "adm",
        "admin",
        "audio",
        "backup",
        "bin",
        "cdrom",
        "competitors",
        "crontab",
        "daemon",
        "dialout",
        "dip",
        "disk",
        "dnsmasq",
        "fax",
        "floppy",
        "games",
        "gnats",
        "hacksports",
        "input",
        "irc",
        "kmem",
        "list",
        "lp",
        "lxd",
        "mail",
        "man",
        "messagebus",
        "mlocate",
        "netdev",
        "news",
        "nobody",
        "nogroup",
        "operator",
        "plugdev",
        "pollinate",
        "proxy",
        "root",
        "sasl",
        "shadow",
        "shellinabox",
        "src",
        "ssh",
        "sshd",
        "staff",
        "sudo",
        "sync",
        "sys",
        "syslog",
        "tape",
        "tty",
        "ubuntu",
        "users",
        "utmp",
        "uucp",
        "uuidd",
        "vagrant",
        "vboxadd",
        "vboxsf",
        "video",
        "voice",
        "wetty",
    ],

    # EMAIL (SMTP)
    "email": {
        "enable_email": False,
        "email_verification": False,
        "parent_verification_email": False,
        "smtp_url": "",
        "smtp_port": 587,
        "email_username": "",
        "email_password": "",
        "from_addr": "",
        "from_name": "",
        "max_verification_emails": 3,
        "smtp_security": "TLS"
    },

    # CAPTCHA
    "captcha": {
        "enable_captcha": False,
        "captcha_url": "https://www.google.com/recaptcha/api/siteverify",
        "reCAPTCHA_public_key": "",
        "reCAPTCHA_private_key": "",
    },

    # LOGGING
    # Will be emailed any severe internal exceptions!
    # Requires email block to be setup.
    "logging": {
        "admin_emails": ["ben@example.com", "joe@example.com"],
        "critical_error_timeout": 600
    },

    # SHELL SERVERS
    "shell_servers": {
        "enable_sharding": False,
        "default_stepping": 5000,
        "steps": [7500, 12500, 17500],
        "limit_added_range": False,
    },

    # ELIGIBILITY CONDITIONS
    # (user properties)
    "eligibility": {
        "usertype": "student",
        "country": "US"
    }
}


def get_settings():
    """Retrieve settings from the database."""
    db = api.db.get_conn()
    settings = db.settings.find_one({}, {"_id": 0})

    if settings is None:
        db.settings.insert(default_settings)
        # Initialize indexes, runonce
        api.db.index_mongo()
        return default_settings
    return settings


def change_settings(changes):
    """
    Update settings in the database.

    Raises:
        PicoException: if an updated key did not previously exist in settings,
                       or the updated value is of a different type

    """
    db = api.db.get_conn()
    settings = db.settings.find_one({})

    # @TODO validate incoming settings at the request level
    def check_keys(real, changed):
        keys = list(changed.keys())
        for key in keys:
            if key not in real:
                raise PicoException(
                    "Cannot update setting for '{}'".format(key) +
                    " (setting not found)",
                    status_code=400)
            elif type(real[key]) != type(changed[key]):  # noqa:E721
                raise PicoException(
                    "Cannot update setting for '{}'".format(key) +
                    " (incorrect type)",
                    status_code=400)
            elif isinstance(real[key], dict):
                check_keys(real[key], changed[key])
                # change the key so mongo $set works correctly
                for key2 in changed[key]:
                    changed["{}.{}".format(key, key2)] = changed[key][key2]
                changed.pop(key)

    check_keys(settings, changes)
    db.settings.update({"_id": settings["_id"]}, {"$set": changes})


def check_competition_active():
    """Check whether the competition is currently running."""
    settings = get_settings()

    return (settings["start_time"].timestamp() <
            datetime.datetime.utcnow().timestamp() <
            settings["end_time"].timestamp())


def block_before_competition(f):
    """Wrap routing functions that are blocked prior to the competition."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if (datetime.utcnow().timestamp()
                <= get_settings()['start_time'].timestamp()):
            raise PicoException(
                'The competition has not begun yet!', 422)
        return f(*args, **kwds)
    return wrapper


def block_after_competition(f):
    """Wrap routing functions that are blocked after the competition."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if (datetime.utcnow().timestamp()
                >= get_settings()['end_time'].timestamp()):
            raise PicoException(
                'The competition has ended!', 422)
        return f(*args, **kwds)
    return wrapper
