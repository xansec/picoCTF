"""Endpoint for the current user."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.user


ns = Namespace('user', description='Information about the logged in user')


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
