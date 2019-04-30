"""Tests for the /api/v0/team routes."""

from .common import (
  ADMIN_DEMOGRAPHICS,
  clear_db,
  client,
  decode_response,
  enable_sample_problems,
  ensure_within_competition,
  get_conn,
  get_csrf_token,
  load_sample_problems,
  register_test_accounts,
  TEACHER_DEMOGRAPHICS,
  USER_DEMOGRAPHICS
)


def test_score(client):
    """Tests the /team/score endpoint."""
    clear_db()
    register_test_accounts()

    # Test without being logged in
    res = client.get('/api/v0/team/score')
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You must be logged in'

    # Test after logging in - inital score should be 0
    client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    res = client.get('/api/v0/team/score')
    csrf_t = get_csrf_token(res)
    status, message, data = decode_response(res)
    assert status == 1
    assert data['score'] == 0

    # Test that score increases with a correct problem submission
    load_sample_problems()
    enable_sample_problems()
    ensure_within_competition()
    res = client.get('/api/v0/problems')
    status, message, data = decode_response(res)
    unlocked_pids = [problem['pid'] for problem in data]
    db = get_conn()
    assigned_instance_id = db.teams.find_one({
        'team_name': USER_DEMOGRAPHICS['username']
    })['instances'][unlocked_pids[0]]
    expected_score = db.problems.find_one({
        'pid': unlocked_pids[0]
    })['score']
    problem_instances = db.problems.find_one({
        'pid': unlocked_pids[0]
    })['instances']
    assigned_instance = None
    for instance in problem_instances:
        if instance['iid'] == assigned_instance_id:
            assigned_instance = instance
            break
    correct_key = assigned_instance['flag']
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t,
        'pid': unlocked_pids[0],
        'key': correct_key,
        'method': 'testing'
    })

    res = client.get('/api/v0/team/score')
    csrf_t = get_csrf_token(res)
    status, message, data = decode_response(res)
    assert status == 1
    assert data['score'] == expected_score
