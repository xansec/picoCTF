"""Group manangement."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.team
import api.user

ns = Namespace('groups', description='Group management')


@ns.route('/')
class GroupList(Resource):
    """Get the list of groups, or add a new group."""

    # @TODO allow admins to see all groups with querystring parameter
    # @require_login
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    def get(self):
        """Get the groups of which you are a member."""
        curr_tid = api.user.get_user()['tid']
        return jsonify(api.team.get_groups(curr_tid))


@ns.route('/<string:group_id>')
class Group(Resource):
    """Get a specific group."""
    pass
