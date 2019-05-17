"""Tests for the /api/v1/team endpoints."""

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


def test_get_my_team(client):
    """Tests the /team endpoint."""
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    expected_fields = {
        'achievements': [],
        'affiliation': 'Sample School',
        'competition_active': False,
        'country': 'US',
        'eligible': True,
        'flagged_submissions': [],
        'max_team_size': 1,
        'progression': [],
        'score': 0,
        'size': 1,
        'solved_problems': [],
        'team_name': 'sampleuser'
        }
    expected_member_fields = {
        'affiliation': 'None',
        'country': 'US',
        'email': 'sample@example.com',
        'firstname': 'Sample',
        'lastname': 'User',
        'username': 'sampleuser',
        'usertype': 'student'
    }
    res = client.get('/api/v1/team')
    assert res.status_code == 200
    for k, v in expected_fields.items():
        assert res.json[k] == v

    assert len(res.json['members']) == 1
    for k, v in expected_member_fields.items():
        assert res.json['members'][0][k] == v

    db = get_conn()
    uid = db.users.find_one({'username': USER_DEMOGRAPHICS['username']})['uid']
    assert res.json['members'][0]['uid'] == uid
