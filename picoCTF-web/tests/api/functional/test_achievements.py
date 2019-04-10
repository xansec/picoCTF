"""Tests for the /api/achievements/ routes."""

from .common import (USER_DEMOGRAPHICS, clear_db, client, decode_response,
                     register_test_accounts)


def test_get_achievements(client):
    """
    Tests the /achievements endpoint.

    @todo improvement: unlock and verify an achievement
    """
    clear_db()
    register_test_accounts()
    client.post('/api/user/login', data={
                'username': USER_DEMOGRAPHICS['username'],
                'password': USER_DEMOGRAPHICS['password']
                })
    res = client.get('/api/achievements')
    status, message, data = decode_response(res)
    assert status == 1
    assert data == []
