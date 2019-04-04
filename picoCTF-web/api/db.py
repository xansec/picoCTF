"""Handles database interaction."""

from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, InvalidName
import logging
from api.common import SevereInternalException

log = logging.getLogger(__name__)


def get_conn():
    """Get a database connection, reusing one if it exists."""
    if 'db' not in g:
        conf = current_app.config
        if conf["MONGO_USER"] and conf["MONGO_PW"]:
            uri = "mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1".format(
                conf["MONGO_USER"], conf["MONGO_PW"], conf["MONGO_ADDR"],
                conf["MONGO_PORT"], conf["MONGO_DB_NAME"])
        else:
            uri = "mongodb://{}:{}/{}".format(
                conf["MONGO_ADDR"], conf["MONGO_PORT"], conf["MONGO_DB_NAME"])
        try:
            client = MongoClient(uri)
            connection = client[conf["MONGO_DB_NAME"]]
        except InvalidName as error:
            raise SevereInternalException(
                "Database {} is invalid! - {}".format(conf["MONGO_DB_NAME"],
                                                      error))
        except ConnectionFailure:
            raise SevereInternalException(
                "Could not connect to mongo database at {}".format(uri))
        g.db = connection
    return g.db


def index_mongo():
    """Ensure the mongo collections are indexed."""
    db = get_conn()

    log.debug("Ensuring mongo is indexed.")

    db.users.ensure_index("uid", unique=True, name="unique uid")
    db.users.ensure_index("username", unique=True, name="unique username")
    db.users.ensure_index("tid")

    db.groups.ensure_index("gid", unique=True, name="unique gid")

    db.problems.ensure_index("pid", unique=True, name="unique pid")

    db.submissions.ensure_index([("tid", 1), ("uid", 1), ("correct", 1)])
    db.submissions.ensure_index([("uid", 1), ("correct", 1)])
    db.submissions.ensure_index([("tid", 1), ("correct", 1)])
    db.submissions.ensure_index([("pid", 1), ("correct", 1)])
    db.submissions.ensure_index("uid")
    db.submissions.ensure_index("tid")

    db.teams.ensure_index("team_name", unique=True, name="unique team names")
    db.teams.ensure_index("country")

    db.shell_servers.ensure_index("name", unique=True,
                                  name="unique shell name")
    db.shell_servers.ensure_index("sid", unique=True, name="unique shell sid")

    db.cache.ensure_index("expireAt", expireAfterSeconds=0)
    db.cache.ensure_index("kwargs", name="kwargs")
    db.cache.ensure_index([("function", 1), ("ordered_kwargs", 1)])
    db.cache.ensure_index("args", name="args")

    db.shell_servers.ensure_index(
        "sid", unique=True, name="unique shell server id")
