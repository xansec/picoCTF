"""Tests for the /api/v0/problems/ routes."""
from pytest_mongo import factories
from ..common import ( clear_db, client, decode_response, # noqa (fixture)
                     enable_sample_problems, ensure_after_competition,
                     ensure_before_competition, ensure_within_competition,
                     get_conn, get_csrf_token, load_sample_problems,
                     problems_endpoint_response, register_test_accounts,
                     USER_DEMOGRAPHICS)


def test_problems(mongo_proc, client): # noqa (fixture)
    """Tests the /problems endpoint."""
    clear_db()
    register_test_accounts()

    # Test without logging in
    res = client.get('/api/v0/problems')
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You must be logged in'

    # Test without any loaded problems
    client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })

    res = client.get('/api/v0/problems')
    status, message, data = decode_response(res)
    assert status == 1
    assert data == []

    # Test after loading sample problems
    # Should still display none as disabled problems are filtered out
    load_sample_problems()
    res = client.get('/api/v0/problems')
    status, message, data = decode_response(res)
    assert status == 1
    assert data == []

    # Test after enabling sample problems
    enable_sample_problems()
    res = client.get('/api/v0/problems')
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


def test_submit(mongo_proc, client): # noqa (fixture)
    """Test the /problems/submit endpoint."""
    clear_db()
    register_test_accounts()
    load_sample_problems()
    enable_sample_problems()
    ensure_within_competition()

    # Test without being logged in
    res = client.post('/api/v0/problems/submit', data={})
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You must be logged in'

    # Test without CSRF token
    client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })

    res = client.post('/api/v0/problems/submit', data={})
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'CSRF token not in form'
    csrf_t = get_csrf_token(res)

    # Test with an incorrect CSRF token
    res = client.post('/api/v0/problems/submit', data={
        'token': 'invalid_csrf_token'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'CSRF token is not correct'

    # Test outside of competition boundaries
    ensure_before_competition()
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'The competition has not begun yet!'

    ensure_after_competition()
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'The competition is over!'

    ensure_within_competition()

    # Test submitting a solution to an invalid problem
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t,
        'pid': 'invalid',
        'key': 'incorrect',
        'method': 'testint'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == "You can't submit flags to problems you haven't " + \
                      "unlocked."

    # Test submitting an incorrect solution to a valid problem
    res = client.get('/api/v0/problems')
    status, message, data = decode_response(res)
    unlocked_pids = [problem['pid'] for problem in data]

    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t,
        'pid': unlocked_pids[0],
        'key': 'incorrect',
        'method': 'testing'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'That is incorrect!'

    # Test submitting the correct solution
    db = get_conn()
    assigned_instance_id = db.teams.find_one({
        'team_name': USER_DEMOGRAPHICS['username']
    })['instances'][unlocked_pids[0]]
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
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'That is correct!'

    # Test submitting the correct solution a second time
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t,
        'pid': unlocked_pids[0],
        'key': correct_key,
        'method': 'testing'
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Flag correct: however, you have already ' + \
                      'solved this problem.'

    # Test submitting an incorrect solution a second time
    # @TODO cases where another team member has solved
    res = client.post('/api/v0/problems/submit', data={
        'token': csrf_t,
        'pid': unlocked_pids[0],
        'key': 'incorrect',
        'method': 'testing'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Flag incorrect: please note that you have ' + \
                      'already solved this problem.'


def test_walkthrough(mongo_proc, client): # noqa (fixture)
    """Tests the /problems/walkthrough endpoint."""
    clear_db()
    register_test_accounts()
    load_sample_problems()
    enable_sample_problems()
    ensure_within_competition()

    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })

    # Attempt to request a walkthrough without a pid
    res = client.get('/api/v0/problems/walkthrough')
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Please supply a pid.'

    # Request a walkthrough for a problem without one
    res = client.get('/api/v0/problems/walkthrough?pid=4508167aa0b219fd9d131551d10aa58e') # noqa (79char)
    status, message, data = decode_response(res)
    assert status == 0
    assert message == "This problem does not have a walkthrough!"

    # Request a walkthrough that the user has not unlocked yet
    res = client.get('/api/v0/problems/walkthrough?pid=1bef644c399e10a3f35fecdbf590bd0c') # noqa (79char)
    status, message, data = decode_response(res)
    assert status == 0
    assert message == "You haven't unlocked this walkthrough yet!"

    # Force unlocked status and retrieve the walkthrough
    db = get_conn()
    db.users.update_one({
        'username': USER_DEMOGRAPHICS['username']
    }, {
        '$set': {
            'unlocked_walkthroughs': ['1bef644c399e10a3f35fecdbf590bd0c']
        }
    })
    res = client.get('/api/v0/problems/walkthrough?pid=1bef644c399e10a3f35fecdbf590bd0c') # noqa
    status, message, data = decode_response(res)
    assert status == 1
    assert message == "PROTIP: Find the correct answer to get the points."


def test_unlock_walkthrough(mongo_proc, client): # noqa (fixture)
    """Tests the /problems/unlock_walkthrough endpoint."""
    clear_db()
    register_test_accounts()
    load_sample_problems()
    enable_sample_problems()
    ensure_within_competition()

    res = client.post('/api/v0/user/login', data={
        'username': USER_DEMOGRAPHICS['username'],
        'password': USER_DEMOGRAPHICS['password'],
        })
    csrf_t = get_csrf_token(res)

    # Attempt to unlock a walkthrough without a pid
    res = client.post('/api/v0/problems/unlock_walkthrough', data={
        'token': csrf_t
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'Please supply a pid.'

    # Attempt to unlock the walkthrough for a problem without one
    res = client.post('/api/v0/problems/unlock_walkthrough', data={
        'token': csrf_t,
        'pid': '4508167aa0b219fd9d131551d10aa58e'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'This problem does not have a walkthrough!'

    # Attempt to unlock a walkthrough without enough tokens
    res = client.post('/api/v0/problems/unlock_walkthrough', data={
        'token': csrf_t,
        'pid': '1bef644c399e10a3f35fecdbf590bd0c'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You do not have enough tokens to unlock this walkthrough!' # noqa

    # Force-add enough tokens and unlock the walkthrough
    db = get_conn()
    unlock_cost = db.problems.find_one({
        'pid': '1bef644c399e10a3f35fecdbf590bd0c'})['score']
    db.users.find_one_and_update({
        'username': USER_DEMOGRAPHICS['username']
    }, {
        '$set': {'tokens': unlock_cost}
    })

    res = client.post('/api/v0/problems/unlock_walkthrough', data={
        'token': csrf_t,
        'pid': '1bef644c399e10a3f35fecdbf590bd0c'
    })
    status, message, data = decode_response(res)
    assert status == 1
    assert message == 'Walkthrough unlocked.' # noqa

    # Attempt to unlock a previously unlocked walkthrough
    res = client.post('/api/v0/problems/unlock_walkthrough', data={
        'token': csrf_t,
        'pid': '1bef644c399e10a3f35fecdbf590bd0c'
    })
    status, message, data = decode_response(res)
    assert status == 0
    assert message == 'You have already unlocked this walkthrough!'
