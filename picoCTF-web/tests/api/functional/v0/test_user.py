"""Tests for the /api/v0/user/ routes."""
import hashlib
from common import ( # noqa (fixture)
  ADMIN_DEMOGRAPHICS,
  clear_db,
  client,
  decode_response,
  get_csrf_token,
  register_test_accounts,
  TEACHER_DEMOGRAPHICS,
  USER_DEMOGRAPHICS,
  get_conn
)


def test_login(client): # noqa (fixture)
    """Tests the /user/login and /user/logout endpoints."""
    clear_db()
    register_test_accounts()

    # Test logging out without being logged in
    res = client.get('/api/v0/user/logout')
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You do not appear to be logged in.'

    # Test logging in with an invalid username
    res = client.post('/api/v0/user/login', data={
        'username': 'invalidusername',
        'password': USER_DEMOGRAPHICS['password'],
        })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Incorrect username.'

    # Test logging in with an invalid password
    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': 'invalidpassword',
        })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Incorrect password'

    # Test logging in with correct credentials
    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Successfully logged in as sampleuser'

    # Test logging out
    res = client.get('/api/v0/user/logout')
    status, message, data = decode_response(res)
    print('{}{}{}'.format(status, message, data))
    assert status == 1
    assert message == 'Successfully logged out.'


def test_status(client): # noqa (fixture)
    """
    Tests the /user/status endpoint.
    """
    clear_db()
    register_test_accounts()
    # Test with an new empty database
    res = client.get('/api/v0/user/status')
    status, message, data = decode_response(res)
    assert res.status_code == 200
    assert data['logged_in'] is False
    assert data['admin'] is False
    assert data['teacher'] is False
    assert data['enable_feedback'] is True
    assert data['enable_captcha'] is False
    assert data['competition_active'] is False
    assert data['username'] == ''
    assert data['tid'] == ''
    assert data['email_verification'] is False

    # Test when logged in as a standard user
    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    res = client.get('/api/v0/user/status')
    status, message, data = decode_response(res)
    assert data['logged_in'] is True
    assert data['admin'] is False
    assert data['teacher'] is False
    assert data['enable_feedback'] is True
    assert data['enable_captcha'] is False
    assert data['competition_active'] is False
    assert data['username'] == USER_DEMOGRAPHICS['username']
    assert data['tid'] != ''
    assert data['team_name'] == USER_DEMOGRAPHICS['username']
    assert data['score'] == 0

    # Test when logged in as a teacher
    res = client.get('/api/v0/user/logout')
    res = client.post('/api/v0/user/login', data={
        'username': TEACHER_DEMOGRAPHICS['username'],
        'password': TEACHER_DEMOGRAPHICS['password'],
        })
    res = client.get('/api/v0/user/status')
    status, message, data = decode_response(res)
    assert data['logged_in'] is True
    assert data['admin'] is False
    assert data['teacher'] is True
    assert data['enable_feedback'] is True
    assert data['enable_captcha'] is False
    assert data['competition_active'] is False
    assert data['username'] == TEACHER_DEMOGRAPHICS['username']
    assert data['tid'] != ''
    assert data['team_name'] == TEACHER_DEMOGRAPHICS['username']
    assert data['score'] == 0

    # Test when logged in as an admin
    res = client.get('/api/user/logout')
    res = client.post('/api/v0/user/login', data={
        'username': ADMIN_DEMOGRAPHICS['username'],
        'password': ADMIN_DEMOGRAPHICS['password'],
        })
    res = client.get('/api/v0/user/status')
    status, message, data = decode_response(res)
    assert data['logged_in'] is True
    assert data['admin'] is True
    assert data['teacher'] is True
    assert data['enable_feedback'] is True
    assert data['enable_captcha'] is False
    assert data['competition_active'] is False
    assert data['username'] == ADMIN_DEMOGRAPHICS['username']
    assert data['tid'] != ''
    assert data['team_name'] == ADMIN_DEMOGRAPHICS['username']
    assert data['score'] == 0


def test_extdata(client): # noqa (fixture)
    """Tests the /user/extdata endpoint."""
    clear_db()
    register_test_accounts()
    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    csrf_t = get_csrf_token(res)

    # Set some extdata
    res = client.put('/api/v0/user/extdata', data={
        'samplekey': 'samplevalue',
        'numerickey': 2,
        'token': csrf_t,
        'nonce': 1
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Your extdata has been successfully updated.'

    # Try to set some extdata with a lower nonce
    res = client.put('/api/v0/user/extdata', data={
        'invalid_nonce': 'true',
        'token': csrf_t,
        'nonce': 0
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Session expired. Please reload your client.'

    # Retrieve extdata
    res = client.get('/api/v0/user/extdata')
    status, message, data = decode_response(res)
    assert status == 1
    assert data['samplekey'] == 'samplevalue'
    assert data['numerickey'] == '2'


def test_minigame(client): # noqa (fixture)
    """Tests the /user/minigame endpoint."""
    clear_db()
    register_test_accounts()

    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    csrf_t = get_csrf_token(res)

    # Attempt to call without specifying a minigame ID
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'v': 'invalid'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Invalid input!'

    # Attempt to call without specifying a validation key
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'mid': 'invalid'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Invalid input!'

    # Attempt to specify an invalid minigame ID
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'mid': 'invalid',
        'v': 'invalid'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Invalid input!'

    # Attempt to specify a correct minigame but invalid key
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'mid': 'a1',
        'v': 'invalid'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Invalid input!'

    # Attempt to successfully record completion of the minigame
    db = get_conn()
    settings = db.settings.find_one()
    hashstring = 'a1' + USER_DEMOGRAPHICS['username'] + \
        settings['minigame']['secret']
    v = hashlib.md5(hashstring.encode('utf-8')).hexdigest()
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'mid': 'a1',
        'v': v
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'You win! You have earned {} tokens.'.format(
        str(settings['minigame']['token_values']['a1'])
    )

    # Attempt to record completion of the same minigame
    res = client.post('/api/v0/user/minigame', data={
        'token': csrf_t,
        'mid': 'a1',
        'v': v
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You win! You have already completed this minigame, so you have not earned additional tokens.' # noqa (79char)
