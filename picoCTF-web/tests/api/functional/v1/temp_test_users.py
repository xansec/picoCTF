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
    Tests the /reset_password and /confirm_password_reset endpoints.

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
    # Attempt to confirm the reset with the wrong token
    res = client.post('/api/user/confirm_password_reset', data={
            'new-password': 'newpassword',
            'new-password-confirmation': 'newpassword',
            'reset-token': 'wrongtoken'
            })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Could not find password_reset.'  # @todo: better error message # noqa:E501
    # Perform the password reset with the correct token
    res = client.post('/api/user/confirm_password_reset', data={
            'new-password': 'newpassword',
            'new-password-confirmation': 'newpassword',
            'reset-token': db_token
            })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Your password has been reset.'
    # Log in with the new password
    res = client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': 'newpassword',
        })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Successfully logged in as sampleuser'


def test_verify(client):
    """@todo."""
    pass


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
    assert db_user['verified'] is True
