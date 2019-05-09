"""Group manangement."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.group
import api.team
import api.user
from api.common import PicoException

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


@ns.response(200, 'Success')
@ns.response(403, 'You do not have permission to view this group.')
@ns.response(404, 'Group not found')
# @require_login
@ns.route('/<string:group_id>')
class Group(Resource):
    """Get a specific group."""

    # @require_login
    def get(self, group_id):
        """Get a specific group."""
        group = api.group.get_group(gid=group_id)
        if not group:
            raise PicoException('Group not found', 404)

        group_members = [group['owner']] + group['members'] + group['teachers']
        curr_user = api.user.get_user()
        if curr_user['tid'] not in group_members and not curr_user['admin']:
            raise PicoException(
                'You do not have permission to view this group.', 403
            )
        return jsonify(group)


@ns.route('/<string:group_id>/flag_sharing')
class FlagSharingInfo(Resource):
    """Get flag sharing statistics for a specific group."""

    # @require_teacher
    def get(self, group_id):
        """Get flag sharing statistics for a specific group."""
        group = api.group.get_group(gid=group_id)
        if not group:
            raise PicoException('Group not found', 404)

        curr_user = api.user.get_user()
        if (curr_user['tid'] not in group['teachers']
                and not curr_user['admin']):
            raise PicoException(
                'You do not have permission to view this group.', 403
            )

        return jsonify(
            api.stats.check_invalid_instance_submissions(group['gid']))
