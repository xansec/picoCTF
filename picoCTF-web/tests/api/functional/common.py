"""Utilities for functional tests."""

import pytest
import json
import pymongo
import re
import api

TESTING_DB_NAME = 'ctf_test'
db = None


def decode_response(res):
    """Parse a WebSuccess or WebError response."""
    decoded_dict = json.loads(res.data.decode('utf-8'))
    return (decoded_dict['status'], decoded_dict['message'],
            decoded_dict['data'])


def get_csrf_token(res):
    """Extract the CSRF token from a response."""
    for header in res.headers:
        m = re.search('token=(.+?);', header[1])
        if m:
            return m.group(1)
    return RuntimeError('Could not find CSRF token in response headers.')


def get_conn():
    """Get a connection to the testing database."""
    global db
    if db is None:
        client = pymongo.MongoClient('127.0.0.1')
        db = client[TESTING_DB_NAME]
    return db


def clear_db():
    """Clear out the testing database."""
    db = get_conn()
    db.command('dropDatabase')


@pytest.fixture
def client():
    """Create an new instance of the Flask app for testing."""
    app = api.create_app()
    app.config['TESTING'] = True
    app.config['MONGO_DB_NAME'] = TESTING_DB_NAME
    return app.test_client()


ADMIN_DEMOGRAPHICS = {
                        'username': 'adminuser',
                        'password': 'adminpw',
                        'firstname': 'Admin',
                        'lastname': 'User',
                        'email': 'admin@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Admin School',
                        'usertype': 'other',
                        'demo[parentemail]': 'admin@example.com',
                        'demo[age]': '18+',
                        'gid': None,
                        'rid': None
                      }

TEACHER_DEMOGRAPHICS = {
                        'username': 'teacheruser',
                        'password': 'teacherpw',
                        'firstname': 'Teacher',
                        'lastname': 'User',
                        'email': 'teacher@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Sample School',
                        'usertype': 'teacher',
                        'demo[parentemail]': 'teacher@example.com',
                        'demo[age]': '18+',
                        'gid': None,
                        'rid': None
                      }

USER_DEMOGRAPHICS = {
                        'username': 'sampleuser',
                        'password': 'samplepw',
                        'firstname': 'Sample',
                        'lastname': 'User',
                        'email': 'sample@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Sample School',
                        'usertype': 'student',
                        'demo[parentemail]': 'student@example.com',
                        'demo[age]': '13-17',
                        'gid': None,
                        'rid': None
                      }


def register_test_accounts():
    """
    Register an admin, teacher, and student account with known demographics.

    Intended to be used, if needed, in conjunction with clear_db()
    to set up a clean environment for each test.
    """
    flask_client = client()
    flask_client.post('/api/user/create_simple',
                      data=ADMIN_DEMOGRAPHICS)
    flask_client.post('/api/user/create_simple',
                      data=TEACHER_DEMOGRAPHICS)
    flask_client.post('/api/user/create_simple',
                      data=USER_DEMOGRAPHICS)
