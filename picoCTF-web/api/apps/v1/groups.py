"""Group manangement."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.group
import api.team
import api.user
from api.common import PicoException

from .schemas import group_req, group_patch_req

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

    # @require_teacher @TODO throw 403 in this
    # @check_csrf
    @ns.response(400, 'Error parsing request')
    @ns.response(403, 'You do not have permission to create a group')
    @ns.response(409, 'You already have a group with that name')
    @ns.expect(group_req)
    def post(self):
        """Add a new group."""
        req = group_req.parse_args(strict=True)
        curr_tid = api.user.get_user('tid')

        # Don't create group if teacher already has one with same name
        if api.group.get_group(
                name=req['name'], owner_tid=curr_tid) is not None:
            raise PicoException(
                'You already have a classroom with that name', 409)

        gid = api.group.create_group(curr_tid, req['name'])
        res = jsonify({
            'success': True,
            'gid': gid
        })
        res.status_code = 201
        return res


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
                'You do not have permission to access this group.', 403
            )

        # Replace the team ids with full team objects
        full_teachers = []
        for tid in group['teachers']:
            full_teachers.append(api.team.get_team_information(tid))
        group['teachers'] = full_teachers
        full_members = []
        for tid in group['members']:
            full_members.append(api.team.get_team_information(tid))
        group['members'] = full_members

        return jsonify(group)

    # @require_teacher
    @ns.response(400, 'Error parsing request')
    @ns.expect(group_patch_req)
    def patch(self, group_id):
        """Modify a group's settings (other fields are not available)."""
        req = group_patch_req.parse_args(strict=True)

        group = api.group.get_group(gid=group_id)
        if not group:
            raise PicoException('Group not found', 404)

        curr_user = api.user.get_user()
        if (curr_user['tid'] not in group['teachers']
                and not curr_user['admin']):
            raise PicoException(
                'You do not have permission to access this group.', 403
            )
        api.group.change_group_settings(group_id, req['settings'])
        return jsonify({
            'success': True
        })


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
                'You do not have permission to access this group.', 403
            )

        return jsonify(
            api.stats.check_invalid_instance_submissions(group['gid']))
