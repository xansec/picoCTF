"""Shell server related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.shell_servers
from api.common import PicoException

from .schemas import shell_server_req, shell_server_patch_req

ns = Namespace('shell_servers', description='Shell server management')


@ns.route('/')
class ShellServerList(Resource):
    """Get the full list of shell servers, or add a new one."""

    # @require_admin
    def get(self):
        """Get the full list of shell servers."""
        return api.shell_servers.get_servers(get_all=True), 200

    # @require_admin
    @ns.expect(shell_server_req)
    @ns.response(201, 'Shell server added')
    @ns.response(400, 'Error parsing request')
    @ns.response(409, 'server_number conflicts with existing server')
    def post(self):
        """Add a new shell server."""
        req = shell_server_req.parse_args(strict=True)
        sid = api.shell_servers.add_server(**req)
        res = jsonify({
            'success': True,
            'sid': sid
            })
        res.response_code = 201
        return res


@ns.response(200, 'Success')
@ns.response(404, 'Shell server not found')
@ns.route('/<string:server_id>')
class ShellServer(Resource):
    """Get, update, or delete a specific shell server."""

    # @require_admin
    def get(self, server_id):
        """Retrieve a specific shell server."""
        res = api.shell_servers.get_server(server_id)
        if not res:
            raise PicoException('Shell server not found', status_code=404)
        else:
            return res, 200

    # @require_admin
    @ns.expect(shell_server_req)
    @ns.response(400, 'Error parsing request')
    @ns.response(409, 'server_number conflicts with existing server')
    def put(self, server_id):
        """Replace a specific shell server."""
        req = shell_server_req.parse_args(strict=True)
        sid = api.shell_servers.update_server(server_id, req)
        if sid is None:
            raise PicoException('Shell server not found', status_code=404)
        res = jsonify({
            'success': True,
            'sid': sid
        })
        res.response_code = 200
        return res

    # @require_admin
    @ns.expect(shell_server_patch_req)
    @ns.response(400, 'Error parsing request')
    @ns.response(409, 'server_number conflicts with existing server')
    def patch(self, server_id):
        """Update an existing shell server."""
        req = {
            k: v for k, v in shell_server_patch_req.parse_args().items() if
            v is not None
        }
        sid = api.shell_servers.update_server(server_id, req)
        if sid is None:
            raise PicoException('Shell server not found', status_code=404)
        res = jsonify({
            'success': True,
            'sid': sid
        })
        res.response_code = 200
        return res

    # @require_admin
    def delete(self, server_id):
        """Delete a shell server."""
        sid = api.shell_servers.remove_server(server_id)
        if sid is None:
            raise PicoException('Shell server not found', status_code=404)
        res = jsonify({
            'success': True,
        })
        res.response_code = 200
        return res
