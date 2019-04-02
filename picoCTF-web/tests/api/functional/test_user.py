"""Tests for the /api/user/ routes."""
import pytest
import json
import pymongo
import re

from api import api
from api.auth import confirm_password
import api.email

# Helper functions and data

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


# /user blueprint route tests


def test_authorization(client):
    """
    Tests the /authorize_role endpoint.

    Tests logging in as various user types, and verifies that the
    authorize_role endpoint works as expected.
    """
    clear_db()
    register_test_accounts()

    # Test "anonymous" role
    res = client.get('/api/user/authorize/user')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/teacher')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/admin')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is authorized.'

    # Test "user" role
    client.post('/api/user/login', data={
                        'username': USER_DEMOGRAPHICS['username'],
                        'password': USER_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/user/authorize/user')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is logged in.'
    res = client.get('/api/user/authorize/teacher')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/admin')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is authorized.'
    client.get('/api/user/logout')

    # Test "teacher" role
    client.post('/api/user/login', data={
                        'username': TEACHER_DEMOGRAPHICS['username'],
                        'password': TEACHER_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/user/authorize/user')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is logged in.'
    res = client.get('/api/user/authorize/teacher')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is a teacher.'
    res = client.get('/api/user/authorize/admin')
    assert res.status_code == 401
    assert res.data.decode('utf8') == 'Client is not authorized.'
    res = client.get('/api/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is authorized.'
    client.get('/api/user/logout')

    # Test "admin" role
    client.post('/api/user/login', data={
                        'username': ADMIN_DEMOGRAPHICS['username'],
                        'password': ADMIN_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/user/authorize/user')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is logged in.'
    # @todo admins are always also teachers?
    res = client.get('/api/user/authorize/teacher')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is a teacher.'
    res = client.get('/api/user/authorize/admin')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is an administrator.'
    res = client.get('/api/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.data.decode('utf8') == 'Client is authorized.'
    client.get('/api/user/logout')


    # status, message, data = decode_response(res)
    # assert status == 1
    # assert message == 'Successfully logged in as sampleuser'
    # assert data['teacher'] is True
    # assert data['admin'] is True  # First user created will be admin
    # # Test calling authorize_role
    # res = client.get('/api/user/authorize/admin')
    # assert res.status_code == 200
    # assert res.data.decode('utf8') == 'Client is an administrator.'
    # # Log out
    # res = client.get('/api/user/logout')
    # status, message, data = decode_response(res)
    # assert status == 1
    # assert message == 'Successfully logged out.'

def test_update_password(client):
    """Tests the /update_password endpoint."""
    clear_db()
    register_test_accounts()
    res = client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
        })
    status, message, data = decode_response(res)
    csrf_t = get_csrf_token(res)
    # Test with the wrong current password
    res = client.post('/api/user/update_password', data={
        'current-password': 'incorrectpw',
        'new-password': 'updatedpw',
        'new-password-confirmation': 'updatedpw',
        'token': csrf_t
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Your current password is incorrect.'
    # Test with the correct current password
    res = client.post('/api/user/update_password', data={
        'current-password': 'samplepw',
        'new-password': 'updatedpw',
        'new-password-confirmation': 'updatedpw',
        'token': csrf_t
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Your password has been successfully updated!'
    # Attempt to log in with the new password
    res = client.get('/api/user/logout')
    res = client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': 'updatedpw'
        })
    status, message, data = decode_response(res)
    assert status == 1


def test_disable_account(client):
    """Tests the /disable_account endpoint."""
    clear_db()
    register_test_accounts()
    res = client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    csrf_t = get_csrf_token(res)
    # Attempt to disable with the wrong current password.
    res = client.post('/api/user/disable_account', data={
        'current-password': 'incorrectpw',
        'token': csrf_t,
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Your current password is incorrect.'
    # Disable with the correct current password.
    res = client.post('/api/user/disable_account', data={
        'current-password': USER_DEMOGRAPHICS['password'],
        'token': csrf_t,
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'You have successfully disabled your account!'
    # Try to log in and verify that it fails.
    res = client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'This account has been disabled.'
    # Verify the disabled account status in the database.
    db = get_conn()
    assert db.get_collection('users').find_one(
        {"username": "sampleuser"})['disabled'] is True


def test_reset_password(client):
    """
    Tests the /reset_password endpoint.

    - Checks that the password reset token was inserted into the database.
    - Verifies that the email is in the outbox.

    """
    clear_db()
    register_test_accounts()
    # App init will set api.email.mail to a testing FlaskMail instance
    with api.email.mail.record_messages() as outbox:
        # Send the password reset request
        res = client.post('/api/user/reset_password', data={
            'username': USER_DEMOGRAPHICS['username'],
            })
        status, message, data = decode_response(res)
        assert status == 1
        assert message == 'A password reset link has been sent to the ' + \
                          'email address provided during registration.'
        # Verify that the token is in the DB
        # Since we cleared the DB, it's the only token in there, so
        # we can avoid searching for it...
        db = get_conn()
        db_token = db.get_collection('tokens') \
                     .find_one({})['tokens']['password_reset']
        assert db_token is not None
        # Verify that the email is in the outbox
        assert len(outbox) == 1
        assert outbox[0].subject == ' Password Reset'
        assert db_token in outbox[0].body


def test_create_user(client):
    """
    Tests the /create_simple endpoint.

    Differs from register_test_accounts() in that we are:
    - validating the response
    - checking the correctness of each field stored in the DB

    @todo an improvement: randomly generate several users with different
          characteristics and verify their creation
    """
    clear_db()
    db = get_conn()
    assert db.get_collection('users').find({"username": "sampleuser"}) \
             .count() == 0
    res = client.post('/api/user/create_simple',
                      data=USER_DEMOGRAPHICS)

    status, message, data = decode_response(res)
    assert status == 1
    assert message == "User \'{}\' registered successfully!".format(
        'sampleuser')
    user_db_entries = list(db.get_collection('users').find(
        {"username": "sampleuser"}))
    assert len(user_db_entries) == 1
    db_user = user_db_entries[0]
    assert db_user['firstname'] == USER_DEMOGRAPHICS['firstname']
    assert db_user['lastname'] == USER_DEMOGRAPHICS['lastname']
    assert db_user['username'] == USER_DEMOGRAPHICS['username']
    assert db_user['email'] == USER_DEMOGRAPHICS['email']
    assert confirm_password(USER_DEMOGRAPHICS['password'],
                            db_user['password_hash'])
    assert db_user['usertype'] == USER_DEMOGRAPHICS['usertype']
    assert db_user['country'] == USER_DEMOGRAPHICS['country']
    assert db_user['demo']['parentemail'] == \
        USER_DEMOGRAPHICS['demo[parentemail]']
    assert db_user['demo']['age'] == \
        USER_DEMOGRAPHICS['demo[age]']
    assert db_user['admin'] is True  # first account in an empty DB is an admin
    assert db_user['teacher'] is True  # ...and admins are also teachers
    assert db_user['eligible'] is True
    assert db_user['verified'] is True


def test_status(client):
    """
    Tests the /status endpoint.

    Expected results based on a newly initialized DB.
    """
    clear_db()
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
