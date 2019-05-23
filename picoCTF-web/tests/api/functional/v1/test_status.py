"""Tests for the /api/v1/status endpoint."""

from common import ( # noqa (fixture)
  ADMIN_DEMOGRAPHICS,
  clear_db,
  client,
  decode_response,
  get_csrf_token,
  register_test_accounts,
  TEACHER_DEMOGRAPHICS,
  USER_DEMOGRAPHICS,
  USER_2_DEMOGRAPHICS,
  load_sample_problems,
  get_conn,
  ensure_within_competition,
  enable_sample_problems,
  get_problem_key
)


def test_status(client): # noqa
    """Test the /status endpoint."""
    # @TODO currently only tests the default values of these fields
    #       try modifying the settings and testing also
    clear_db()

    expected_responses = {
        'enable_feedback': True,
        'enable_captcha': False,
        'reCAPTCHA_public_key': '',
        'competition_active': False,
        'email_verification': False,
        'max_team_size': 1,
        'email_filter': []
    }
    nondeterministic_responses = ['time']
    res = client.get('/api/v1/status')
    assert res.status_code == 200
    for k, v in expected_responses.items():
        assert res.json[k] == v
    for k in nondeterministic_responses:
        assert k in res.json
