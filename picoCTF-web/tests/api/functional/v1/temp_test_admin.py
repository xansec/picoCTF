# from .common import (
#   ADMIN_DEMOGRAPHICS,
#   clear_db,
#   client,
#   decode_response,
#   get_conn,
#   get_csrf_token,
#   register_test_accounts,
#   TEACHER_DEMOGRAPHICS,
#   USER_DEMOGRAPHICS
# )
# from api.config import default_settings
# import api.email
# from bson import json_util

# # /admin blueprint route tests


# def test_problems(client):
#     """Test the /problems endpoint."""
#     clear_db()
#     register_test_accounts()
#     client.post('/api/user/login', data={
#                     'username': ADMIN_DEMOGRAPHICS['username'],
#                     'password': ADMIN_DEMOGRAPHICS['password']
#                     })
#     res = client.get('/api/admin/problems')
#     status, message, data = decode_response(res)
#     assert status == 1
#     assert data['problems'] == []
#     assert data['bundles'] == []


# def test_users(client):
#     """Test the /users endpoint."""
#     clear_db()
#     register_test_accounts()
#     client.post('/api/user/login', data={
#                     'username': ADMIN_DEMOGRAPHICS['username'],
#                     'password': ADMIN_DEMOGRAPHICS['password']
#                     })
#     res = client.get('/api/admin/users')
#     status, message, data = decode_response(res)
#     assert status == 1
#     assert len(data) == 1
#     assert data[0]['username'] == 'sampleuser'


# def test_settings(client):
#     """Test the /settings endpoint."""
#     clear_db()
#     register_test_accounts()
#     client.post('/api/user/login', data={
#                     'username': ADMIN_DEMOGRAPHICS['username'],
#                     'password': ADMIN_DEMOGRAPHICS['password']
#                     })
#     res = client.get('/api/admin/settings')
#     status, message, data = decode_response(res)
#     assert status == 1
#     # Filter out dates and _id fields because they won't match
#     ignore_keys = {'start_time', 'end_time', '_id'}
#     assert {k: v for k, v in data.items() if k not in ignore_keys} \
#         == {k: v for k, v in default_settings.items() if k not in ignore_keys}


# def test_settings_change(client):
#     """
#     Test the /settings/change endpoint.

#     Specifically, test changing the mail server configuration.
#     """
#     clear_db()
#     register_test_accounts()
#     client.post('/api/user/login', data={
#                     'username': ADMIN_DEMOGRAPHICS['username'],
#                     'password': ADMIN_DEMOGRAPHICS['password']
#                     })
#     old_default_sender = api.email.mail.default_sender
#     res = client.post('/api/admin/settings/change', data={
#         'json': json_util.dumps({
#                     "email": {
#                         "enable_email": True,
#                         "email_verification": False,
#                         "parent_verification_email": False,
#                         "smtp_url": "",
#                         "smtp_port": 587,
#                         "email_username": "",
#                         "email_password": "",
#                         "from_addr": "updated_default@picoctf.com",
#                         "from_name": "",
#                         "max_verification_emails": 3,
#                         "smtp_security": "TLS"
#                     }})
#     })
#     status, message, data = decode_response(res)
#     assert status == 1
#     assert message == 'Settings updated'
#     assert api.email.mail.default_sender != old_default_sender
