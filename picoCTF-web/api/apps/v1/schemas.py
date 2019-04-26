"""Validation schemas for API requests."""
from flask_restplus import reqparse, inputs


def object_type(value):
    """To make the openAPI object type show up in the docs."""
    return value
object_type.__schema__ = {'type': 'object'} # noqa


def protocol_type(value):
    if value not in ['HTTP', 'HTTPS']:
        raise ValueError('Invalid protocol (must be HTTP or HTTPS)')
    return value
protocol_type.__schema__ = {'type': 'string'} # noqa

# Achievement request schema
achievement_req = reqparse.RequestParser()
achievement_req.add_argument(
    'name', required=True, type=str,
    help='Name of the achievement.')
achievement_req.add_argument(
    'score', required=True, type=inputs.natural,
    help='Point value of the achievement (positive integer).')
achievement_req.add_argument(
    'description', required=True, type=str,
    help='Description of the achievement.')
achievement_req.add_argument(
    'processor', required=True, type=str,
    help='Path to the achievement processor.')
achievement_req.add_argument(
    'hidden', required=True, type=inputs.boolean,
    help='Hide this achievement?')
achievement_req.add_argument(
    'image', required=True, type=str,
    help='Path to achievement image.')
achievement_req.add_argument(
    'smallimage', required=True, type=str,
    help='Path to achievement thumbnail.')
achievement_req.add_argument(
    'disabled', required=True, type=inputs.boolean,
    help='Disable this achievement?')
achievement_req.add_argument(
    'multiple', required=True, type=inputs.boolean,
    help='Allow earning multiple instances of this achievement?')
achievement_patch_req = achievement_req.copy()
for arg in achievement_patch_req.args:
    arg.required = False

# Shell server output schema
# (This is too complex for reqparse to really handle, so we'll trust it.
#  If we move to another validation engine e.g. marshmallow, we can revisit.)
shell_server_out = reqparse.RequestParser()
shell_server_out.add_argument(
    'sid', required=True, type=str, location='args',
    help="Shell server ID.")
shell_server_out.add_argument(
    'problems', required=False, type=object_type, action='append',
    location='json')
shell_server_out.add_argument(
    'bundles', required=False, type=object_type, action='append',
    location='json')

# Problem PATCH request schema
# ("disabled" is the only mutable field as the others are controlled by the
#  shell manager.)
problem_patch_req = reqparse.RequestParser()
# @TODO: finish after shell server part is in place
problem_patch_req.add_argument(
    ''
)

# Shell server request schema
shell_server_req = reqparse.RequestParser()
shell_server_req.add_argument(
    'name', required=True, type=str,
    help='Shell server display name.')
shell_server_req.add_argument(
    'host', required=True, type=str,
    help='Shell server hostname.')
shell_server_req.add_argument(
    'port', required=True, type=inputs.int_range(1, 65535),
    help='Shell server port.')
shell_server_req.add_argument(
    'username', required=True, type=str,
    help='Username.')
shell_server_req.add_argument(
    'password', required=True, type=str,
    help='Password.')
shell_server_req.add_argument(
    'protocol', required=True, type=protocol_type,
    help='Protocol (HTTP/HTTPS).'
)
shell_server_req.add_argument(
    'server_number', required=False, type=inputs.positive,
    help='Server number (will be automatically assigned if not provided).')
shell_server_patch_req = shell_server_req.copy()
for arg in shell_server_patch_req.args:
    arg.required = False
