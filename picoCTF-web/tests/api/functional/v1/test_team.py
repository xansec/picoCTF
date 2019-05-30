"""Tests for the /api/v1/team endpoints."""
from pytest_mongo import factories
from ..common import ( # noqa (fixture)
  ADMIN_DEMOGRAPHICS,
  clear_db,
  client,
  decode_response,
  get_csrf_token,
  register_test_accounts,
  TEACHER_DEMOGRAPHICS,
  USER_DEMOGRAPHICS,
  USER_2_DEMOGRAPHICS,
  get_conn
)
import api


def test_get_my_team(mongo_proc, client): # noqa (fixture)
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


def test_get_my_team_score(mongo_proc, client): # noqa (fixture)
    """Test the /team/score endpoint."""
    # @TODO test after submitting a problem to modify score
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    res = client.get('/api/v1/team/score')
    assert res.status_code == 200
    assert res.json['score'] == 0


def test_update_team_password(mongo_proc, client): # noqa (fixture)
    """Test the /team/update_password endpoint."""
    clear_db()
    register_test_accounts()
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    csrf_t = get_csrf_token(res)

    # Attempt to change password while still in initial team
    res = client.post('/api/v1/team/update_password', json={
        'new_password': 'newpassword',
        'new_password_confirmation': 'newpassword',
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 422
    assert res.json['message'] == "You have not created a team yet."

    # Attempt to set with non-matching passwords
    res = client.post('/api/v1/teams', json={
        'team_name': 'newteam',
        'team_password': 'newteam'
    })
    tid = res.json['tid']

    res = client.post('/api/v1/team/update_password', json={
        'new_password': 'newpassword',
        'new_password_confirmation': 'invalid',
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 422
    assert res.json['message'] == "Your team passwords do not match."

    # Successfully change password
    db = get_conn()
    old_password = str(db.teams.find_one({'tid': tid})['password'])

    res = client.post('/api/v1/team/update_password', json={
        'new_password': 'newpassword',
        'new_password_confirmation': 'newpassword',
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 200
    assert res.json['success'] is True
    new_password = str(db.teams.find_one({'tid': tid})['password'])
    assert new_password != old_password


def test_team_score_progression(mongo_proc, client): # noqa (fixture)
    """Test the /team/score_progression endpoint."""
    # @TODO test submitting problems to change score
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    # Test without category argument
    res = client.get('/api/v1/team/score_progression')
    assert res.status_code == 200
    assert res.json == []

    # Test with empty category argument
    res = client.get('/api/v1/team/score_progression?category=')
    assert res.status_code == 200
    assert res.json == []

    # Test with a category
    res = client.get(
        r'/api/v1/team/score_progression?category=Web%20Exploitation')
    assert res.status_code == 200
    assert res.json == []


def test_join_team(mongo_proc, client): # noqa (fixture)
    """Test the /api/v1/team/join endpoint."""
    clear_db()
    register_test_accounts()
    client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })

    # Create the new team that we will try to join
    res = client.post('/api/v1/teams', json={
        'team_name': 'newteam',
        'team_password': 'newteam'
    })
    new_tid = res.json['tid']

    # Attempt to join as a teacher
    client.get('/api/v1/user/logout')
    client.post('/api/v1/user/login', json={
        'username': TEACHER_DEMOGRAPHICS['username'],
        'password': TEACHER_DEMOGRAPHICS['password']
    })
    res = client.post('/api/v1/team/join', json={
        'team_name': 'newteam',
        'team_password': 'newteam'
    })
    assert res.status_code == 403
    assert res.json['message'] == 'Teachers may not join teams!'

    # Attempt to join a nonexistant team
    client.get('/api/v1/user/logout')
    client.post('/api/v1/user/login', json={
        'username': USER_2_DEMOGRAPHICS['username'],
        'password': USER_2_DEMOGRAPHICS['password']
    })
    res = client.post('/api/v1/team/join', json={
        'team_name': 'invalid',
        'team_password': 'newteam'
    })
    assert res.status_code == 404
    assert res.json['message'] == 'Team not found'

    # Attempt to join when max_team_size is 1 (default)
    res = client.post('/api/v1/team/join', json={
        'team_name': 'newteam',
        'team_password': 'newteam'
    })
    assert res.status_code == 403
    assert res.json['message'] == 'That team is already at maximum capacity.'

    # Update max_team_size and attempt to join with incorrect password
    api.config.get_settings()
    db = get_conn()
    db.settings.find_one_and_update({}, {'$set': {'max_team_size': 2}})

    res = client.post('/api/v1/team/join', json={
        'team_name': 'newteam',
        'team_password': 'invalid'
    })
    assert res.status_code == 403
    assert res.json['message'] == 'That is not the correct password to ' + \
                                  'join that team.'

    # Join the new team
    user = db.users.find_one(
        {'username': USER_2_DEMOGRAPHICS['username']})
    uid = user['uid']
    previous_tid = user['tid']
    res = client.post('/api/v1/team/join', json={
        'team_name': 'newteam',
        'team_password': 'newteam'
    })
    assert res.status_code == 200
    assert res.json['success'] is True
    assert db.users.find_one({'uid': uid})['tid'] == new_tid
    assert db.teams.find_one({'tid': previous_tid})['size'] == 0
    assert db.teams.find_one({'tid': new_tid})['size'] == 2

    # Attempt to switch back to old team
    res = client.post('/api/v1/team/join', json={
        'team_name': USER_2_DEMOGRAPHICS['username'],
        'team_password': USER_2_DEMOGRAPHICS['password']
    })
    assert res.status_code == 403
    assert res.json['message'] == 'You can not switch teams once you ' + \
                                  'have joined one.'


def test_join_group(mongo_proc, client): # noqa (fixture)
    """Test the /team/join_group endpoint."""
    clear_db()
    register_test_accounts()

    # Create the group we will join
    res = client.post('/api/v1/user/login', json={
        'username': TEACHER_DEMOGRAPHICS['username'],
        'password': TEACHER_DEMOGRAPHICS['password']
    })
    csrf_t = get_csrf_token(res)
    res = client.post('/api/v1/groups', json={
        'name': 'newgroup'
    }, headers=[('X-CSRF-Token', csrf_t)])

    # Attempt to join a nonexistent group
    client.get('/api/v1/user/logout')
    res = client.post('/api/v1/user/login', json={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password']
    })
    csrf_t = get_csrf_token(res)
    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'invalid',
        'group_owner': TEACHER_DEMOGRAPHICS['username']
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 404
    assert res.json['message'] == 'Group not found'

    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'newgroup',
        'group_owner': 'invalid'
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 404
    assert res.json['message'] == 'Group owner not found'

    # Attempt to join a group that we don't pass the email whitelist for
    db = get_conn()
    db.groups.find_one_and_update({'name': 'newgroup'}, {'$set': {
        'settings.email_filter': ['filtered@email.com']
    }})
    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'newgroup',
        'group_owner': TEACHER_DEMOGRAPHICS['username']
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 403
    assert res.json['message'] == "{}'s email does not belong to the " + \
        "whitelist for that classroom. Your team may not join this " + \
        "classroom at this time.".format(USER_DEMOGRAPHICS['username'])
    db.groups.find_one_and_update({'name': 'newgroup'}, {'$set': {
        'settings.email_filter': []
    }})

    # Successfully join a group
    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'newgroup',
        'group_owner': TEACHER_DEMOGRAPHICS['username']
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 200
    assert res.json['success'] is True
    user_team = db.users.find_one({
        'username': USER_DEMOGRAPHICS['username']})['tid']
    group = db.groups.find_one({'name': 'newgroup'})
    assert user_team in group['members']

    # Attempt to join a group we are already a member of
    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'newgroup',
        'group_owner': TEACHER_DEMOGRAPHICS['username']
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 409
    assert res.json['message'] == 'Your team is already a member of ' + \
                                  'this group.'

    # Join a group as a user with teacher permissions
    client.get('/api/v1/user/logout')
    res = client.post('/api/v1/user/login', json={
        'username': ADMIN_DEMOGRAPHICS['username'],
        'password': ADMIN_DEMOGRAPHICS['password']
    })
    csrf_t = get_csrf_token(res)
    res = client.post('/api/v1/team/join_group', json={
        'group_name': 'newgroup',
        'group_owner': TEACHER_DEMOGRAPHICS['username']
    }, headers=[('X-CSRF-Token', csrf_t)])
    assert res.status_code == 200
    assert res.json['success'] is True
    admin_team = db.users.find_one({
        'username': ADMIN_DEMOGRAPHICS['username']})['tid']
    group = db.groups.find_one({'name': 'newgroup'})
    assert admin_team not in group['members']
    assert admin_team in group['teachers']
