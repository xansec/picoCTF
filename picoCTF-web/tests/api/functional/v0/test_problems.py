from .common import (
    client,
    decode_response,
    clear_db,
    register_test_accounts,
    USER_DEMOGRAPHICS,
    ADMIN_DEMOGRAPHICS,
    load_sample_problems,
    enable_sample_problems,
)


def test_problems(client):
    """Tests the /problems endpoint."""
    clear_db()
    register_test_accounts()

    client.post('/api/user/login', data={
        'username': ADMIN_DEMOGRAPHICS['username'],
        'password': ADMIN_DEMOGRAPHICS['password'],
        })

    # Test without any loaded problems
    res = client.get('/api/problems')
    status, message, data = decode_response(res)
    assert status == 1
    assert data == []

    # Test after loading sample problems
    # Should still display none as disabled problems are filtered out
    load_sample_problems()
    res = client.get('/api/problems')
    status, message, data = decode_response(res)
    assert status == 1
    assert data == []

    # Test after enabling sample problems
    enable_sample_problems()
    res = client.get('/api/problems')
    status, message, data = decode_response(res)
    assert status == 1
    assert data != []
