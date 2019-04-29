"""Tests for the /api/team routes."""

from .common import (
  ADMIN_DEMOGRAPHICS,
  clear_db,
  client,
  decode_response,
  get_conn,
  get_csrf_token,
  register_test_accounts,
  TEACHER_DEMOGRAPHICS,
  USER_DEMOGRAPHICS,
  load_sample_problems,
  enable_sample_problems,
)


def test_score(client):
    """Tests the /team/score endpoint."""
    clear_db()
    register_test_accounts()

    # Test without being logged in
    res = client.get('/api/team/score')
    status, message, data = decode_response(res)
    print('{}{}{}'.format(status, message, data))
    assert status == 0
    assert message == 'You must be logged in'

    # Test after logging in - inital score should be 0
    client.post('/api/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    res = client.get('/api/team/score')
    status, message, data = decode_response(res)
    assert status == 1
    assert data['score'] == 0

    # @TODO Test after making sample problem submission(s)
    load_sample_problems()
    enable_sample_problems()
