"""Tests for the /api/user/ routes."""
import pytest
import json
import pymongo

from api import api

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
    """Check that the /status route returns the expected results."""
    res = client.get('/api/user/status')
    #@todo check for more fields
    assert res.status_code == 200


def test_create_user(client):
    """Test user creation."""
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
    assert db.get_collection('users').find({"username": "sampleuser"}) \
             .count() == 1
