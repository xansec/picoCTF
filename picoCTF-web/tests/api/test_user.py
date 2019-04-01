"""Tests for the /api/user/ routes."""
# noqa: E712
import pytest
import json
import pymongo

from api import api
from api.auth import confirm_password

TESTING_DB_NAME = 'ctf_test'
db = None


# Helper functions
def decode_response(res):
    """Parse a WebSuccess or WebError response."""
    decoded_dict = json.loads(res.data.decode('utf-8'))
    return (decoded_dict['status'], decoded_dict['message'],
            decoded_dict['data'])


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


# User route tests
def test_status(client):
    """
    Check that the /status route returns the expected results.

    Expected results based on a newly initialized DB.
    """
    res = client.get('/api/user/status')
    status, message, data = decode_response(res)
    assert res.status_code == 200
    assert data['logged_in'] is False
    assert data['admin'] is False
    assert data['teacher'] is False
    assert data['enable_teachers'] is True
    assert data['enable_feedback'] is True
    assert data['enable_captcha'] is False
    assert data['competition_active'] is False
    assert data['username'] == ''
    assert data['tid'] == ''
    assert data['email_verification'] is False


def test_create_user(client):
    """
    Test user creation.

    Ensures that the specified user is created in the database.
    @todo separate tests for student, teacher, admin, other user creation
    """
    clear_db()
    db = get_conn()
    assert db.get_collection('users').find({"username": "sampleuser"}) \
             .count() == 0
    res = client.post('/api/user/create_simple',
                      data={
                        'username': 'sampleuser',
                        'password': 'samplepw',
                        'firstname': 'First',
                        'lastname': 'Last',
                        'email': 'sample@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Sample School',
                        'usertype': 'teacher',
                        'demo[parentemail]': 'sample@example.com',
                        'demo[age]': '18+',
                        'gid': None,
                        'rid': None
                        }
                      )

    status, message, data = decode_response(res)
    assert status == 1
    assert message == "User \'{}\' registered successfully!".format(
        'sampleuser')
    user_db_entries = list(db.get_collection('users').find(
        {"username": "sampleuser"}))
    assert len(user_db_entries) == 1
    db_user = user_db_entries[0]
    assert db_user['firstname'] == 'First'
    assert db_user['lastname'] == 'Last'
    assert db_user['username'] == 'sampleuser'
    assert db_user['email'] == 'sample@example.com'
    assert confirm_password('samplepw', db_user['password_hash'])
    assert db_user['usertype'] == 'teacher'
    assert db_user['country'] == 'US'
    assert db_user['demo']['parentemail'] == 'sample@example.com'
    assert db_user['demo']['age'] == '18+'
    assert db_user['teacher'] is True
    assert db_user['admin'] is True
    assert db_user['eligible'] is False
    assert db_user['verified'] is True

