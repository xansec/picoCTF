"""Endpoint for the current user."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.auth
import api.user
from api.common import PicoException

from .schemas import login_req, user_extdata_req, disable_account_req

ns = Namespace('user', description='Authentication and information about ' +
                                   'current user')


@ns.response(200, 'Success')
@ns.response(401, 'Not logged in')
@ns.route('/')
class User(Resource):
    """Get the current user or update their extdata."""

    # @require_login
    def get(self):
        """Get information about the current user."""
        return jsonify(api.user.get_user())

    # @require_login
    @ns.expect(user_extdata_req)
    def patch(self):
        """Update the current user's extdata (other fields not supported)."""
        req = user_extdata_req.parse_args(strict=True)
        api.user.update_extdata(req['extdata'])
        return jsonify({
            'success': True
        })


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
        return jsonify({
            "success": True,
            "username": req['username']
        })


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
        return jsonify({
            'success': True
        })


@ns.route('/authorize/<string:requested_role>')
class AuthorizationResponse(Resource):
    """
    Determine whether the current user has certain roles.

    Used to handle authorization in nginx.
    """

    @ns.response(200, 'User is authorized for the given role')
    @ns.response(401, 'User is not authorized for the given role')
    def get(self, requested_role):
        """Get the authorization status for the current user."""
        # Determine authorizations
        authorizations = {
            'anonymous': True,
            'user': False,
            'teacher': False,
            'admin': False
        }
        if requested_role not in authorizations:
            raise PicoException('Invalid role', 401)
        try:
            user = api.user.get_user()
        except PicoException:
            user = None
        if user:
            for role in ['teacher', 'admin']:
                authorizations['role'] = user['role']

        if authorizations[requested_role] is True:
            status_code = 200
        else:
            status_code = 401

        res = jsonify(authorizations)
        res.status_code = status_code
        return res


@ns.route('/disable_account')
class DisableAccountResponse(Resource):
    """Disable your user account. Requires password confirmation."""

    # @require_login
    # @check_csrf
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    @ns.response(500, 'Provided password is not correct')
    @ns.expect(disable_account_req)
    def post(self):
        """
        Disable your user account. Requires password confirmation.

        Note that this is an irreversable action.
        """
        user = api.user.get_user(include_pw_hash=True)
        req = disable_account_req.parse_args(strict=True)

        if not api.auth.confirm_password(
                req['password'], user['password_hash']):
            raise PicoException('The provided password is not correct.')
        api.user.disable_account(user['uid'])
        return jsonify({
            'success': True
            })
