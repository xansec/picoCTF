"""Handles MongoDB connections for load testing."""

from pymongo import MongoClient

db = None
db_conf = {
    'MONGO_HOST': '127.0.0.1',
    'MONGO_PORT': 27017,
    'MONGO_USER': None,
    'MONGO_PASS': None,
    'MONGO_DB_NAME': 'picoCTF-load-testing',
}

API_BASE_URL = 'api/v1'
REGISTRATION_ENDPOINT = API_BASE_URL + '/users'
LOGIN_ENDPOINT = API_BASE_URL + '/user/login'
LOGOUT_ENDPOINT = API_BASE_URL + '/user/logout'
SCOREBOARDS_ENDPOINT = API_BASE_URL + '/scoreboards'
GROUPS_ENDPOINT = API_BASE_URL + '/groups'

SHELL_PAGE_URL = 'shell'
GAME_PAGE_URL = 'game'
SCOREBOARD_PAGE_URL = 'scoreboard'

def get_db():
    global db
    if not db:
        if db_conf['MONGO_USER'] or db_conf['MONGO_PASS']:
            mongo_client = MongoClient(
                    "mongodb://{}:{}@{}:{}/{}?authMechanism=SCRAM-SHA-1".format(
                        db_conf['MONGO_USER'], db_conf['MONGO_PASS'],
                        db_conf['MONGO_HOST'], db_conf['MONGO_PORT'],
                        db_conf['MONGO_DB_NAME']
                    ))
        else:
            mongo_client = MongoClient(
                "mongodb://{}:{}/{}".format(
                    db_conf['MONGO_HOST'], db_conf['MONGO_PORT'],
                    db_conf['MONGO_DB_NAME']
                ))
        db = mongo_client[db_conf['MONGO_DB_NAME']]
    return db
