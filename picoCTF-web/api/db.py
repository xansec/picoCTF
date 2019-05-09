"""Handles database interaction."""

import logging

from flask import current_app
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from api.common import PicoException

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
        else:
            uri = "mongodb://{}:{}/{}".format(
                conf["MONGO_ADDR"], conf["MONGO_PORT"], conf["MONGO_DB_NAME"])
        try:
            __client = MongoClient(uri)
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

    db.users.create_index("uid", unique=True, name="unique uid")
    db.users.create_index("username", unique=True, name="unique username")
    db.users.create_index("tid")

    db.groups.create_index("gid", unique=True, name="unique gid")

    db.problems.create_index("pid", unique=True, name="unique pid")

    db.submissions.create_index([("tid", 1), ("uid", 1), ("correct", 1)])
    db.submissions.create_index([("uid", 1), ("correct", 1)])
    db.submissions.create_index([("tid", 1), ("correct", 1)])
    db.submissions.create_index([("pid", 1), ("correct", 1)])
    db.submissions.create_index("uid")
    db.submissions.create_index("tid")

    db.teams.create_index("team_name", unique=True, name="unique team names")
    db.teams.create_index("country")

    db.shell_servers.create_index("sid", unique=True, name="unique shell sid")

    db.cache.create_index("expireAt", expireAfterSeconds=0)
    db.cache.create_index("key")

    db.shell_servers.create_index(
        "sid", unique=True, name="unique shell server id")
