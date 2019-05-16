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


def test_disable_account(client):
    """Tests the /user/disable_account endpoint."""
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    # Attempt to disable account with an incorrect password
    res = client.post('/api/v1/user/disable_account', json={
                    'password': 'invalid'
                })
    assert res.status_code == 422
    assert res.json['message'] == 'The provided password is not correct.'

    # Successfully disable account
    db = get_conn()
    user_before_disabling = db.users.find_one(
        {'username': USER_DEMOGRAPHICS['username']})
    assert user_before_disabling['disabled'] is False
    res = client.post('/api/v1/user/disable_account', json={
                    'password': USER_DEMOGRAPHICS['password']
                })
    assert res.status_code == 200
    assert res.json['success'] is True
    user_after_disabling = db.users.find_one(
        {'username': USER_DEMOGRAPHICS['username']})
    assert user_after_disabling['disabled'] is True


def test_update_password(client):
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    # Attempt to update password with incorrect current password
    res = client.post('/api/v1/user/update_password', json={
        'current_password': 'invalid',
        'new_password': 'newpassword',
        'new_password_confirmation': 'newpassword'
    })
    assert res.status_code == 422
    assert res.json['message'] == 'Your current password is incorrect.'

    # Attempt to update password but the passwords don't match
    res = client.post('/api/v1/user/update_password', json={
        'current_password': USER_DEMOGRAPHICS['password'],
        'new_password': 'newpassword1',
        'new_password_confirmation': 'newpassword2'
    })
    assert res.status_code == 422
    assert res.json['message'] == 'Your passwords do not match.'

    # Successfully update password and log in
    res = client.post('/api/v1/user/update_password', json={
        'current_password': USER_DEMOGRAPHICS['password'],
        'new_password': 'newpassword',
        'new_password_confirmation': 'newpassword'
    })
    assert res.status_code == 200
    assert res.json['success'] is True

    client.get('/api/v1/user/logout')
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': 'newpassword'
    })
    assert res.status_code == 200
    assert res.json['success'] is True


def test_get_user(client):
    """Tests the GET /user endpoint."""
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    expected_body = {
        'admin': False,
        'completed_minigames': [],
        'country': 'US',
        'demo': {
            'age': '13-17',
            'parentemail': 'student@example.com'},
        'disabled': False,
        'email': 'sample@example.com',
        'extdata': {},
        'firstname': 'Sample',
        'lastname': 'User',
        'teacher': False,
        'tid': '8b19b0478dcc43e7a448a4e500584c10',
        'tokens': 0,
        'uid': 'dc7089e279d24b70b989cd53665eb49c',
        'unlocked_walkthroughs': [],
        'username': 'sampleuser',
        'usertype': 'student',
        'verified': True
        }
    res = client.get('/api/v1/user')
    assert res.status_code == 200
    for k, v in res.json.items():
        if k not in {'uid', 'tid'}:
            assert res.json[k] == expected_body[k]


def test_patch_user(client):
    """Tests the PATCH /user endpoint."""
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    updated_extdata = {
            'testdata': '1'
        }
    res = client.patch('/api/v1/user', json={
        'extdata': updated_extdata
    })
    assert res.status_code == 200
    assert res.json['success'] is True

    res = client.get('api/v1/user')
    assert res.json['extdata'] == updated_extdata
