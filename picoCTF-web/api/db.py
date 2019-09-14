"""Handles database interaction."""

import logging

from flask import current_app
import pymongo
from pymongo.errors import PyMongoError

from api import PicoException

log = logging.getLogger(__name__)

__connection = None
__client = None


def get_conn():
    """
    Get a database connection, reusing one if it exists.

    Raises:
        PicoException if a successful connection cannot be established

    """
    global __client, __connection
    if not __connection:
        conf = current_app.config
        if conf["MONGO_USER"] and conf["MONGO_PW"]:
            uri = "mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1".format(
                conf["MONGO_USER"], conf["MONGO_PW"], conf["MONGO_ADDR"],
                conf["MONGO_PORT"], conf["MONGO_DB_NAME"])
            if conf["MONGO_REPLICA_SETTINGS"]:
                uri = "{}&{}".format(uri, conf["MONGO_REPLICA_SETTINGS"])
            if conf["MONGO_TLS_SETTINGS"]:
                uri = "{}&{}".format(uri, conf["MONGO_TLS_SETTINGS"])
        else:
            uri = "mongodb://{}:{}/{}".format(
                conf["MONGO_ADDR"], conf["MONGO_PORT"], conf["MONGO_DB_NAME"])
        try:
            __client = pymongo.MongoClient(uri)
            __connection = __client[conf["MONGO_DB_NAME"]]
        except PyMongoError as error:
            raise PicoException(
                'Internal server error. Please contact a system adminstrator.',
                data={'original_error': error})
    return __connection


def index_mongo():
    """Ensure the mongo collections are indexed."""
    db = get_conn()

    log.debug("Ensuring mongo is indexed.")

    db.exceptions.create_index([('time', pymongo.DESCENDING)])

    db.groups.create_index("gid", unique=True, name="unique gid")
    db.groups.create_index("owner", name="owner")
    db.groups.create_index("teachers", name="teachers")
    db.groups.create_index("members", name="members")
    db.groups.create_index([('owner', 1), ('time', 1)], name="name and owner")

    db.problems.create_index("pid", unique=True, name="unique pid")
    db.problems.create_index("disabled")
    db.problems.create_index([('score', pymongo.ASCENDING),
                              ('name', pymongo.ASCENDING)])

    db.scoreboards.create_index("sid", unique=True, name="unique scoreboard sid")

    db.shell_servers.create_index("sid", unique=True, name="unique shell sid")

    db.submissions.create_index([("pid", 1), ("uid", 1), ("correct", 1)])
    db.submissions.create_index([("pid", 1), ("tid", 1), ("correct", 1)])
    db.submissions.create_index([("uid", 1), ("correct", 1)])
    db.submissions.create_index([("tid", 1), ("correct", 1)])
    db.submissions.create_index([("pid", 1), ("correct", 1)])
    db.submissions.create_index("uid")
    db.submissions.create_index("tid")

    db.teams.create_index("team_name", unique=True, name="unique team_names")
    db.teams.create_index("tid", unique=True, name="unique tid")
    db.teams.create_index(
        "eligibilities",
        name="non-empty eligiblity",
        partialFilterExpression={
            "size": {
                "$gt": 0
            }
        })
    db.teams.create_index("size",
        name="non-empty size",
        partialFilterExpression={
            "size": {
                "$gt": 0
            }
        })

    db.tokens.create_index("uid")
    db.tokens.create_index("gid")
    db.tokens.create_index("tokens.registration_token")
    db.tokens.create_index("tokens.email_verification")
    db.tokens.create_index("tokens.password_reset")

    db.users.create_index("uid", unique=True, name="unique uid")
    db.users.create_index("username", unique=True, name="unique username")
    db.users.create_index("tid")
    db.users.create_index("email")
    db.users.create_index("demo.parentemail")
