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


def test_login(client):
    """Test the /user/login endpoint."""
    clear_db()
    register_test_accounts()

    # Attempt to login with a malformed request
    res = client.post('/api/v1/user/login', json={
        'username': 'invalid'
    })
    assert res.status_code == 400
    assert res.json['message'] == 'Input payload validation failed'

    # Attempt to login with an invalid username
    res = client.post('/api/v1/user/login', json={
        'username': 'invalid',
        'password': 'invalid'
    })
    assert res.status_code == 401
    assert res.json['message'] == 'Incorrect username.'

    # Attempt to login with an incorrect password
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': 'invalid'
    })
    assert res.status_code == 401
    assert res.json['message'] == 'Incorrect password'

    # Force-disable account and attempt to login
    db = get_conn()
    db.users.update({'username': USER_DEMOGRAPHICS['username']},
                    {'$set': {'disabled': True}})
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    assert res.status_code == 403
    assert res.json['message'] == 'This account has been disabled.'
    db.users.update({'username': USER_DEMOGRAPHICS['username']},
                    {'$set': {'disabled': False}})

    # Force un-verify account and attempt to login
    db = get_conn()
    db.users.update({'username': USER_DEMOGRAPHICS['username']},
                    {'$set': {'verified': False}})
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    assert res.status_code == 403
    assert res.json['message'] == 'This account has not been verified yet.'
    db.users.update({'username': USER_DEMOGRAPHICS['username']},
                    {'$set': {'verified': True}})

    # Successfully log in
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    assert res.status_code == 200
    assert res.json['success'] is True
    assert res.json['username'] == USER_DEMOGRAPHICS['username']


def test_logout(client):
    """Test the /user/logout endpont."""
    clear_db()
    register_test_accounts()

    # Attempt to log out without being logged in
    res = client.get('/api/v1/user/logout')
    assert res.status_code == 401
    assert res.json['message'] == 'You must be logged in'

    # Successfully log out
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    res = client.get('/api/v1/user/logout')
    assert res.status_code == 200
    assert res.json['success'] is True


def test_authorize(client):
    """Test the /user/authorize endpoint."""
    clear_db()
    register_test_accounts()

    # Test invalid role
    res = client.get('/api/v1/user/authorize/invalid')
    assert res.status_code == 401
    assert res.json['message'] == 'Invalid role'

    # Test "anonymous" role
    expected_body = {
        'anonymous': True,
        'user': False,
        'teacher': False,
        'admin': False
    }
    res = client.get('/api/v1/user/authorize/user')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/teacher')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/admin')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.json == expected_body

    # Test "user" role
    expected_body = {
        'anonymous': True,
        'user': True,
        'teacher': False,
        'admin': False
    }
    client.post('/api/v1/user/login', json={
                        'username': USER_DEMOGRAPHICS['username'],
                        'password': USER_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/v1/user/authorize/user')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/teacher')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/admin')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.json == expected_body
    client.get('/api/v1/user/logout')

    # Test "teacher" role
    expected_body = {
        'anonymous': True,
        'user': True,
        'teacher': True,
        'admin': False
    }
    client.post('/api/v1/user/login', json={
                        'username': TEACHER_DEMOGRAPHICS['username'],
                        'password': TEACHER_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/v1/user/authorize/user')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/teacher')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/admin')
    assert res.status_code == 401
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.json == expected_body
    client.get('/api/v1/user/logout')

    # Test "admin" role
    expected_body = {
        'anonymous': True,
        'user': True,
        'teacher': True,
        'admin': True
    }
    client.post('/api/v1/user/login', json={
                        'username': ADMIN_DEMOGRAPHICS['username'],
                        'password': ADMIN_DEMOGRAPHICS['password']
                      })
    res = client.get('/api/v1/user/authorize/user')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/teacher')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/admin')
    assert res.status_code == 200
    assert res.json == expected_body
    res = client.get('/api/v1/user/authorize/anonymous')
    assert res.status_code == 200
    assert res.json == expected_body
    client.get('/api/v1/user/logout')
