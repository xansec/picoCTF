from .common import (
    client,
    decode_response,
    clear_db,
    register_test_accounts,
    USER_DEMOGRAPHICS,
    load_sample_problems,
    enable_sample_problems,
    problems_endpoint_response
)


def test_problems(client):
    """Tests the /problems endpoint."""
    clear_db()
    register_test_accounts()

    # Test without logging in
    res = client.get('/api/problems')
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You must be logged in'

    # Test without any loaded problems
    client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })

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
    for i in range(len(data)):
        # Cannot compare randomly templated fields with e.g. port numbers
        for field in {
            'author', 'category', 'disabled', 'hints', 'name', 'organization',
            'pid', 'sanitized_name', 'score', 'server', 'server_number',
            'socket', 'solved', 'solves', 'unlocked'
        }:
            assert data[i][field] == problems_endpoint_response[i][field]
