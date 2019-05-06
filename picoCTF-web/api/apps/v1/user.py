"""Endpoint for the current user."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.auth
import api.user
from api.common import PicoException

from .schemas import login_req

ns = Namespace('user', description='Authentication and information about ' +
                                   'current user')


@ns.route('/')
class User(Resource):
    """Get the current user."""

    # @require_login
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    def get(self):
        """Get information about the current user."""
        res = jsonify(api.user.get_user())
        res.response_code = 200
        return res


@ns.route('/login')
class LoginResponse(Resource):
    """Log in."""

    # @require_login
    @ns.response(200, 'Sucess')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Incorrect password')
    @ns.response(403, 'Account disabled or not yet verified')
    @ns.expect(login_req)
    def post(self):
        """Log in."""
        req = login_req.parse_args(strict=True)
        api.auth.login(req['username'], req['password'])
        res = jsonify({
            "success": True,
            "username": req['username']
        })
        res.status_code = 200
        return res


@ns.route('/logout')
class LogoutResponse(Resource):
    """Log out."""

    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    def get(self):
        """Log out."""
        if not api.auth.is_logged_in():
            raise PicoException(
                'There is no user currently logged in.', 401
            )
        else:
            api.auth.logout()
        res = jsonify({
            'success': True
        })
        res.status_code = 200
        return res
